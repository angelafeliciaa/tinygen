from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from .github_utils import fetch_repo_content
from .llm_utils import generate_changes, perform_reflection, find_relevant_files, rank_and_select_files, extract_relevant_functions
from .diff_utils import generate_diff, format_diff_indentation

load_dotenv()

app = FastAPI()

# Supabase setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Serve static files
static_dir = os.path.join(os.getcwd(), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

class CodegenRequest(BaseModel):
    repoUrl: str
    prompt: str

@app.get("/")
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return JSONResponse(status_code=404, content={"error": "index.html not found"})

@app.post("/generate")
async def generate_code(request: CodegenRequest):
    try:
        # Fetch repo content
        repo_content = fetch_repo_content(request.repoUrl)
        
        # Find relevant files
        relevant_files = find_relevant_files(repo_content, request.prompt)
        
        # Rank and select top files
        top_files = rank_and_select_files(relevant_files)
        
        # Iteratively generate and refine changes
        final_changes = iterative_change_generation(top_files, request.prompt)
        
        # Generate diff
        diff = generate_diff(repo_content, final_changes)
        
        # Sanitize diff by removing null bytes
        sanitized_diff = diff.replace('\u0000', '')
        
        # Store in Supabase
        supabase.table("tinygen_logs").insert({
            "repo_url": request.repoUrl,
            "prompt": request.prompt,
            "diff": sanitized_diff
        }).execute()
        
        return JSONResponse(content={"diff": sanitized_diff})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/fetch-content")
async def fetch_content(repo_url: str):
    try:
        # Fetch repo content
        repo_content = fetch_repo_content(repo_url)
        print(repo_content)  # Print the content to the console
        # Return the fetched content as JSON
        return JSONResponse(content={"repo_content": repo_content})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def iterative_change_generation(top_files: dict, prompt: str) -> dict:
    changes = generate_changes(top_files, prompt)
    while True:
        # Perform reflection
        final_changes = perform_reflection(changes, prompt)
        
        # Check if any changes were suggested
        if all(final_changes[file_path] == changes[file_path] for file_path in changes):
            break  # No further changes needed
        
        # Update changes with the reflected corrections
        changes = final_changes
    
    return changes

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)