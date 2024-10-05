from supabase import create_client, Client
import os

class SupabaseService:
    def __init__(self):
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        self.client: Client = create_client(supabase_url, supabase_key)

    def log_generation(self, repo_url: str, prompt: str, diff: str):
        self.client.table("tinygen_logs").insert({
            "repo_url": repo_url,
            "prompt": prompt,
            "diff": diff
        }).execute()