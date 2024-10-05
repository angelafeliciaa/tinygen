from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

def find_relevant_files(repo_content: dict, issue_analysis: str) -> dict:
    relevant_files = {}
    for file_path, content in repo_content.items():
        if not should_process_file(file_path):
            logger.info(f"Skipping file: {file_path}")
            continue

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI assistant that determines the relevance of a file to a given issue analysis. Evaluate the file's content and provide a relevance score from 1 to 100, where 100 is extremely relevant and 1 is not relevant at all. Consider both direct and indirect relevance to the issue."},
                {"role": "user", "content": f"Given the following code:\n\n{content}\n\nHow relevant is this file to the following issue analysis: {issue_analysis}\n\nRelevance score (1-100):"}
            ],
            max_tokens=10,
            temperature=0.2
        )
        try:
            score = int(response.choices[0].message.content.strip())
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

def extract_relevant_functions(top_files: dict, issue_analysis: str) -> dict:
    relevant_functions = {}
    for file_path, file_info in top_files.items():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI assistant that identifies and extracts relevant functions from a given code file. Analyze the code and the issue, then provide the names of the most relevant functions, separated by commas. Consider both functions that may need modification and those that are crucial to understanding the context."},
                {"role": "user", "content": f"Given the following code:\n\n{file_info['content']}\n\nWhat are the most relevant functions for addressing this issue analysis: {issue_analysis}\n\nRelevant functions:"}
            ],
            max_tokens=100,
            temperature=0.2
        )
        relevant_functions[file_path] = {
            "content": file_info['content'],
            "score": file_info["score"],
            "functions": [func.strip() for func in response.choices[0].message.content.split(",")]
        }

    return relevant_functions

def generate_changes(relevant_files_and_functions: dict, issue_analysis: str) -> dict:
    changes = {}
    for file_path, file_info in relevant_files_and_functions.items():
        content = file_info['content']
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert AI programmer tasked with modifying code to address specific issues. Focus on making precise, targeted changes that directly address the issue while maintaining the overall structure and style of the code. Only modify parts of the code that are directly relevant to the requested change. Preserve existing functions and structure unless explicitly asked to remove or refactor them. Do not add comments explaining the changes."},
                {"role": "user", "content": f"Given the following code:\n\n{content}\n\nApply the following change based on this issue analysis: {issue_analysis}\n\nProvide only the modified parts of the code, keeping the rest unchanged:"}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        modified_content = response.choices[0].message.content.strip()
        
        # Merge the changes with the original content
        original_lines = content.split('\n')
        modified_lines = modified_content.split('\n')
        
        final_lines = original_lines.copy()
        for i, line in enumerate(modified_lines):
            if line.strip() and (i >= len(original_lines) or line != original_lines[i]):
                if i < len(final_lines):
                    final_lines[i] = line
                else:
                    final_lines.append(line)
        
        changes[file_path] = '\n'.join(final_lines)
    
    return changes

def perform_reflection(changes: dict, issue_analysis: str) -> dict:
    reflected_changes = {}
    for file_path, modified_content in changes.items():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior code reviewer with expertise in identifying and improving code changes. Analyze the modifications made to address the given issue, focusing on correctness, efficiency, and adherence to best practices. Suggest improvements only for the parts that have been changed, and ensure that your suggestions maintain the overall structure and style of the code. REMOVE ANY SUGGESTIONS, COMMENTS, OR EXPLANATIONS. JUST GIVE CODE."},
                {"role": "user", "content": f"We are addressing this issue: \n\n{issue_analysis}\n\nReview the following code changes:\n\n{modified_content}\n\nAre the code changes relevant, correct, and optimal? If improvements are needed, provide only the corrected parts. If no changes are needed, respond with 'No changes needed.'"}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        reflection = response.choices[0].message.content.strip()
        if reflection.lower() != "no changes needed.":
            # Merge reflection changes with the modified content
            reflected_changes[file_path] = merge_changes(modified_content, reflection)
        else:
            reflected_changes[file_path] = modified_content
    return reflected_changes

def merge_changes(original: str, changes: str) -> str:
    original_lines = original.split('\n')
    change_lines = changes.split('\n')
    
    final_lines = original_lines.copy()
    for i, line in enumerate(change_lines):
        if line.strip() and (i >= len(original_lines) or line != original_lines[i]):
            if i < len(final_lines):
                final_lines[i] = line
            else:
                final_lines.append(line)
    
    return '\n'.join(final_lines)

def understand_repository(repo_content: dict) -> str:
    # Combine all file contents into a single string
    all_content = "\n\n".join([f"File: {path}\n{content}" for path, content in repo_content.items()])
    
    # Truncate the content if it's too long
    max_chars = 14000
    if len(all_content) > max_chars:
        all_content = all_content[:max_chars] + "...\n(Content truncated due to length)"
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI Software Engineer tasked with analyzing code repositories. Provide a concise yet comprehensive summary of the repository's structure, purpose, main components, and potential areas for improvement."},
            {"role": "user", "content": f"Analyze the following repository content and provide a detailed summary:\n\n{all_content}"}
        ],
        max_tokens=500,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def analyze_issue(repo_understanding: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI software engineer specializing in analyzing coding issues within the context of a repository. Provide a detailed analysis of the issue, how it relates to the repository, and potential approaches to address it."},
            {"role": "user", "content": f"Given the following repository summary:\n\n{repo_understanding}\n\nAnalyze this issue and propose solutions:\n\n{prompt}"}
        ],
        max_tokens=500,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()