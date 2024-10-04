import os
import tempfile
from git import Repo
import requests

def fetch_repo_content(repo_url: str) -> dict:
    # Extract owner and repo name from the URL
    parts = repo_url.split('/')
    owner = parts[-2]
    repo = parts[-1]
    if repo.endswith('.git'):
        repo = repo[:-4]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    
    content = {}
    
    def fetch_contents(path=''):
        response = requests.get(f"{api_url}/{path}")
        response.raise_for_status()
        
        for item in response.json():
            if item['type'] == 'file':
                file_content = requests.get(item['download_url']).text
                content[item['path']] = file_content
            elif item['type'] == 'dir':
                fetch_contents(item['path'])

    fetch_contents()
    return content