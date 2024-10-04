import os
import tempfile
from git import Repo
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define maximum file size (e.g., 1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 Megabyte

def is_binary_file(file_content: str) -> bool:
    """
    Determines if a file is binary using a simple heuristic.
    """
    # Check for null bytes
    if '\x00' in file_content:
        return True
    # Attempt to decode as UTF-8
    try:
        file_content.encode('utf-8').decode('utf-8')
    except UnicodeDecodeError:
        return True
    return False

def fetch_repo_content(repo_url: str) -> dict:
    """
    Fetches the content of a GitHub repository, excluding binary and large files.
    
    Args:
        repo_url (str): The URL of the GitHub repository.
    
    Returns:
        dict: A dictionary with file paths as keys and file contents as values.
    """
    # Extract owner and repo name from the URL
    parts = repo_url.rstrip('/').split('/')
    owner = parts[-2]
    repo = parts[-1]
    if repo.endswith('.git'):
        repo = repo[:-4]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    
    content = {}
    
    # Recursive fetching with file filtering
    def fetch_contents(path=''):
        response = requests.get(f"{api_url}/{path}")
        response.raise_for_status()
        
        for item in response.json():
            if item['type'] == 'file':
                # Skip files larger than MAX_FILE_SIZE
                if item['size'] > MAX_FILE_SIZE:
                    logger.info(f"Skipping large file: {item['path']} ({item['size']} bytes)")
                    continue

                file_response = requests.get(item['download_url'])
                file_response.raise_for_status()
                file_content = file_response.text

                # Skip binary files
                if is_binary_file(file_content):
                    logger.info(f"Skipping binary file: {item['path']}")
                    continue

                content[item['path']] = file_content
            elif item['type'] == 'dir':
                fetch_contents(item['path'])

    fetch_contents()
    return content