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

def find_relevant_files(repo_content: dict, prompt: str) -> dict:
    relevant_files = {}
    for file_path, content in repo_content.items():
        if not should_process_file(file_path):
            logger.info(f"Skipping file: {file_path}")
            continue

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that determines how relevant a file is to a given prompt. Respond with a relevance score from 1 to 100, where 100 is extremely relevant and 1 is not relevant at all."},
                {"role": "user", "content": f"Given the following code:\n\n{content}\n\nHow relevant is this file to the following change request: {prompt}\n\nRelevance score (1-100):"}
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

def extract_relevant_functions(top_files: dict, prompt: str) -> dict:
    relevant_functions = {}
    for file_path, file_info in top_files.items():
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts relevant functions from a given code file. Respond with the names of the most relevant functions, separated by commas."},
                {"role": "user", "content": f"Given the following code:\n\n{file_info['content']}\n\nWhat are the most relevant functions for this change request: {prompt}\n\nRelevant functions:"}
            ],
            max_tokens=100,
            temperature=0.2
        )
        relevant_functions[file_path] = {
            "score": file_info["score"],
            "functions": [func.strip() for func in response.choices[0].message.content.split(",")]
        }

    return relevant_functions

def generate_changes(repo_content: dict, prompt: str) -> dict:
    changes = {}
    for file_path, content in repo_content.items():
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that modifies code based on user prompts. Don't give long explanations or comments. Just fix the code relevant to what is requested. DO NOT WRITE COMMENTS, KEY CHANGES OR SUMMARY. DO NOT EDIT THE README.md file."},
            {"role": "user", "content": f"Given the following code:\n\n{content}\n\nApply the following change: {prompt}\n\nModified code:"}
        ],
        max_tokens=1000,
        temperature=0.2)
        changes[file_path] = response.choices[0].message.content.strip()
    return changes

def perform_reflection(changes: dict, prompt: str) -> dict:
    reflected_changes = {}
    for file_path, modified_content in changes.items():
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a code reviewer assistant."},
            {"role": "user", "content": f"We are trying to solve this problem: \n\n{prompt}\n\nReview the following code changes:\n\n{modified_content}\n\n. Are the code changes relevant to what is asked? DO NOT WRITE COMMENTS, KEY CHANGES OR SUMMARY. DO NOT EDIT THE README.md file. Are there any improvements or corrections needed? If yes, provide the corrected code. If no, respond with 'No changes needed.'"}
        ],
        max_tokens=1000,
        temperature=0.2)
        reflection = response.choices[0].message.content.strip()
        if reflection.lower() != "no changes needed.":
            reflected_changes[file_path] = reflection
        else:
            reflected_changes[file_path] = modified_content
    return reflected_changes