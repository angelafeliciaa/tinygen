from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
import re

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# could give examples of prompt and response, but that won't work for all cases, 
# although it would give very accurate results for the specific sample output we're given.


def should_process_file(file_path):
    # List of directories and file extensions to ignore
    ignore_dirs = ['.idea', '.git', '__pycache__', 'venv', 'env']
    ignore_extensions = ['.pyc', '.pyo', '.pyd', '.db', '.lock', '.toml', '.md', '.txt']
    ignore_filenames = ['requirements.txt', 'Pipfile', 'poetry.lock']

    # Check if the file is in an ignored directory
    if any(ignored_dir in file_path.split(os.sep) for ignored_dir in ignore_dirs):
        return False

    # Check if the file has an ignored extension
    if any(file_path.endswith(ext) for ext in ignore_extensions):
        return False

    # Check if the file is in the list of ignored filenames
    if os.path.basename(file_path) in ignore_filenames:
        return False

    return True

def find_relevant_files(repo_content: dict, prompt: str) -> dict:
    relevant_files = {}
    for file_path, content in repo_content.items():
        if not should_process_file(file_path):
            logger.info(f"Skipping file: {file_path}")
            continue

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that determines how relevant a file is to a given prompt. Respond with a numeric relevance score from 1 to 100, where 100 is extremely relevant and 1 is not relevant at all. Only provide the numeric score as your response."},
                {"role": "user", "content": f"Given the following code:\n\n{content}\n\nHow relevant is this file to the following change request: {prompt}\n\nRelevance score (1-100):"}
            ],
            max_tokens=5000,
            temperature=0
        )
        try:
            score_str = response.choices[0].message.content.strip()
            score = int(score_str)
            relevant_files[file_path] = {"content": content, "score": score}
        except ValueError:
            logger.warning(f"Error parsing score for {file_path}. Setting default score of 1.")
            relevant_files[file_path] = {"content": content, "score": 1}

    return relevant_files

def rank_and_select_files(relevant_files: dict) -> dict:
    # Sort files by score
    ranked_files = sorted(relevant_files.items(), key=lambda x: x[1]["score"], reverse=True)

    # Determine top_n dynamically
    total_files = len(ranked_files)
    cumulative_score = 0
    score_threshold = 0.8 * sum(file["score"] for _, file in ranked_files)

    for i, (file_path, file_info) in enumerate(ranked_files):
        cumulative_score += file_info["score"]
        if cumulative_score >= score_threshold or i >= min(5, total_files // 2):
            top_n = i + 1
            break
    else:
        top_n = total_files

    logger.info(f"Selected {top_n} out of {total_files} files for detailed analysis.")

    # Select top N files
    top_files = dict(ranked_files[:top_n])

    return top_files

def extract_relevant_functions(top_files: dict, prompt: str) -> dict:
    relevant_functions = {}
    for file_path, file_info in top_files.items():
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts relevant functions from a given code file. Respond with the names of the most relevant functions, separated by commas."},
                {"role": "user", "content": f"Given the following code:\n\n{file_info['content']}\n\nWhat are the most relevant functions for this change request: {prompt}\n\nRelevant functions:"}
            ],
            max_tokens=5000,
            temperature=0
        )
        relevant_functions[file_path] = {
            "score": file_info["score"],
            "functions": [func.strip() for func in response.choices[0].message.content.split(",")]
        }

    return relevant_functions

def is_special_file(file_path: str) -> bool:
    """Check if the file requires special handling."""
    file_name = os.path.basename(file_path).lower()
    special_files = ['__init__.py', 'index.js']
    return file_name in special_files

def clean_code_block(code: str) -> str:
    # Remove leading and trailing whitespace
    code = code.strip()
    
    # Remove leading '''python or ''' if present
    code = re.sub(r'^\'\'\'(?:python)?\s*', '', code)
    
    # Remove trailing ''' if present
    code = re.sub(r'\s*\'\'\'$', '', code)
    
    # Remove any remaining ''' markers within the code
    code = code.replace("'''", "")
    
    return code.strip()

def generate_changes(top_files: dict, prompt: str) -> dict:
    changes = {}
    for file_path, file_info in top_files.items():
        is_special = is_special_file(file_path)
        
        system_message = (
            "You are a helpful assistant that modifies code based on user prompts. Follow these rules strictly:\n"
            "1. Only suggest changes that are directly related to the user's prompt.\n"
            "2. If you think there needs to be a change to fulfill the prompt, respond with the entire updated code for the file.\n"
            "3. If no changes are needed, respond with 'No changes needed.'\n"
            "4. Provide only the modified code, not explanations or comments about the changes.\n"
            "5. Do not use markdown formatting or code block syntax (like '''python or ''').\n"
            "6. Do not include any text before or after the code.\n"
            "7. The user prompt might give potential solutions or examples to solve the problem, but do not jump to conclusions over these examples. Carefully consider the best approach.\n"
        )
        
        if is_special:
            system_message += (
                "8. This is a special file (__init__.py or index.js). Be extra cautious:\n"
                "   - For __init__.py: Only modify if absolutely necessary. Prefer adding imports over adding logic.\n"
                "   - For index.js: Ensure changes don't break the module's main functionality or exports.\n"
            )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Given the following code in {file_path}:\n\n{file_info['content']}\n\nApply the following change if necessary: {prompt}\n\nProvide the entire updated code for the file:"}
            ],
            max_tokens=5000,
            temperature=0
        )
        
        content = response.choices[0].message.content.strip()
        
        if content != "No changes needed.":
            # Clean the code block
            content = clean_code_block(content)
            changes[file_path] = content + '\n'  # Ensure there's a newline at the end

    return changes

def perform_reflection(changes: dict, prompt: str, max_iterations: int = 3) -> dict:
    for iteration in range(max_iterations):
        reflected_changes = {}
        changes_made = False
        
        for file_path, content in changes.items():
            is_special = is_special_file(file_path)
            
            system_message = (
                "You are a code reviewer assistant. Follow these rules strictly:\n"
                "1. Ensure code changes are relevant to the given prompt and in the correct file.\n"
                "2. Do not write comments, summaries, or explanations.\n"
                "3. If no changes are needed, return the original code exactly.\n"
                "4. If improvements are needed, provide only the corrected code.\n"
                "5. Do not add any text that isn't part of the code.\n"
            )
            
            if is_special:
                system_message += (
                    "6. This is a special file (__init__.py or index.js). Be extra cautious:\n"
                    "   - For __init__.py: Only approve changes if absolutely necessary. Prefer imports over logic.\n"
                    "   - For index.js: Ensure changes don't break the module's main functionality or exports.\n"
                )
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Problem to solve:\n\n{prompt}\n\nReview these changes in {file_path}:\n\n{content}\n\nReturn the code as-is if appropriate, or provide corrected code if needed."}
                ],
                max_tokens=5000,
                temperature=0
            )
            reflection = response.choices[0].message.content.strip()
            
            # Clean the reflection
            cleaned_reflection = '\n'.join(
                line for line in reflection.split('\n')
                if not line.strip().startswith(('+', '-', '#')) and 'changes needed' not in line.lower()
            )
            
            reflected_changes[file_path] = cleaned_reflection.strip() or content
            
            if reflected_changes[file_path] != content:
                changes_made = True
        
        if not changes_made:
            # If no changes were made in this iteration, we're satisfied
            return changes
        
        # Update changes for the next iteration
        changes = reflected_changes
    
    # If we've reached max_iterations and still making changes, return the latest version
    return changes