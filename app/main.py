# storing fastAPI app

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from .github_utils import fetch_repo_content
from .llm_utils import generate_changes, perform_reflection
from .diff_utils import generate_diff

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
        
        # Generate initial changes
        initial_changes = generate_changes(repo_content, request.prompt)
        
        # Perform reflection
        final_changes = perform_reflection(initial_changes)
        
        # Generate diff
        diff = generate_diff(repo_content, final_changes)

        # # Store in Supabase
        supabase.table("tinygen_logs").insert({
            "repo_url": request.repoUrl,
            "prompt": request.prompt,
            "diff": diff
        }).execute()
        
        return JSONResponse(content={"diff": diff})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
# fetch content works  
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)