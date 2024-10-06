import os
import requests
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define maximum file size (e.g., 1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 Megabyte

def is_binary_content(content: str) -> bool:
    """Determines if content is binary using a simple heuristic."""
    return '\x00' in content or not is_valid_utf8(content)

def is_valid_utf8(content: str) -> bool:
    """Checks if the content is valid UTF-8."""
    try:
        content.encode('utf-8').decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def get_github_api_url(repo_url: str) -> str:
    """Constructs the GitHub API URL from the repository URL."""
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]
    repo = repo[:-4] if repo.endswith('.git') else repo
    return f"https://api.github.com/repos/{owner}/{repo}/contents"

def fetch_file_content(url: str) -> str:
    """Fetches content from a given URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def process_github_item(item: Dict) -> Tuple[str, str]:
    """Processes a single item from GitHub API response."""
    if item['size'] > MAX_FILE_SIZE:
        logger.info(f"Skipping large file: {item['path']} ({item['size']} bytes)")
        return None

    content = fetch_file_content(item['download_url'])
    
    if is_binary_content(content):
        logger.info(f"Skipping binary file: {item['path']}")
        return None

    return item['path'], content

def recursive_fetch_contents(api_url: str, path: str = '') -> Dict[str, str]:
    """Recursively fetches contents from GitHub API."""
    content = {}
    response = requests.get(f"{api_url}/{path}")
    response.raise_for_status()
    
    for item in response.json():
        if item['type'] == 'file':
            result = process_github_item(item)
            if result:
                content[result[0]] = result[1]
        elif item['type'] == 'dir':
            content.update(recursive_fetch_contents(api_url, item['path']))

    return content

def fetch_repo_content(repo_url: str) -> Dict[str, str]:
    """
    Main function to fetch content of a GitHub repository.
    
    Args:
        repo_url (str): The URL of the GitHub repository.
    
    Returns:
        Dict[str, str]: A dictionary with file paths as keys and file contents as values.
    """
    api_url = get_github_api_url(repo_url)
    return recursive_fetch_contents(api_url)