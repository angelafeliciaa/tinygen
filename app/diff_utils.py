import difflib
import re

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
def format_diff_indentation(diff: str) -> str:
    lines = diff.split('\n')
    formatted_lines = []
    indent_level = 0
    in_code_block = False

    for line in lines:
        if line.startswith('```python'):
            in_code_block = True
            formatted_lines.append(line)
            continue
        elif line.startswith('```'):
            in_code_block = False
            formatted_lines.append(line)
            continue

        if not in_code_block:
            formatted_lines.append(line)
            continue

        # Remove leading '+' and spaces for code lines
        code_line = re.sub(r'^\+\s*', '', line)

        if code_line.strip().startswith(('def ', 'class ')):
            indent_level = 0
        elif code_line.strip().startswith(('if ', 'elif ', 'else:', 'for ', 'while ')):
            if not code_line.strip().endswith(':'):
                indent_level += 1

        formatted_line = ' ' * (4 * indent_level) + code_line.strip()
        
        if code_line.strip().endswith(':'):
            indent_level += 1

        formatted_lines.append('+' + formatted_line)

    return '\n'.join(formatted_lines)
