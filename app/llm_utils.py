from openai import OpenAI
from dotenv import load_dotenv
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

load_dotenv()

def generate_changes(repo_content: dict, prompt: str) -> dict:
    changes = {}
    for file_path, content in repo_content.items():
        response = client.chat.completions.create(model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that modifies code based on user prompts. Don't give long explanations or comments. Just fix the code relevant to what is requested. DO NOT WRITE COMMENTS, KEY CHANGES OR SUMMARY."},
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
            {"role": "user", "content": f"We are trying to solve this problem: \n\n{prompt}\n\nReview the following code changes:\n\n{modified_content}\n\n. Are the code changes relevant to what is asked? DO NOT WRITE COMMENTS, KEY CHANGES OR SUMMARY. Are there any improvements or corrections needed? If yes, provide the corrected code. If no, respond with 'No changes needed.'"}
        ],
        max_tokens=1000,
        temperature=0.2)
        reflection = response.choices[0].message.content.strip()
        if reflection.lower() != "no changes needed.":
            reflected_changes[file_path] = reflection
        else:
            reflected_changes[file_path] = modified_content
    return reflected_changes