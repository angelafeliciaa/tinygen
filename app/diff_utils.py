import difflib

def generate_diff(original_content: dict, modified_content: dict) -> str:
    diff = []
    
    for file_path in original_content.keys():
        if file_path in modified_content:
            original_lines = original_content[file_path].splitlines()
            modified_lines = modified_content[file_path].splitlines()
            
            # Generate the unified diff
            file_diff = difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}',
                lineterm='',
                n=0  # Set context lines to 0 for a more concise diff
            )
            
            diff.extend(file_diff)
    
    return '\n'.join(diff)
 