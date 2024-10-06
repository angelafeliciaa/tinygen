from supabase import create_client, Client
import os

# Initialize the Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
client: Client = create_client(supabase_url, supabase_key)

def log_generation(repo_url: str, prompt: str, diff: str):
    client.table("tinygen_logs").insert({
        "repo_url": repo_url,
        "prompt": prompt,
        "diff": diff
    }).execute()