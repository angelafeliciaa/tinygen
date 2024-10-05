from .github_service import fetch_repo_content
from .llm_service import find_relevant_files, rank_and_select_files, generate_changes, perform_reflection
from .diff_service import generate_diff, format_diff_indentation
from .supabase_service import SupabaseService

# Create an instance of SupabaseService
supabase_service = SupabaseService()

__all__ = [
    'fetch_repo_content',
    'find_relevant_files',
    'rank_and_select_files',
    'generate_changes',
    'perform_reflection',
    'generate_diff',
    'format_diff_indentation',
    'supabase_service'
]
