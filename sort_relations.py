
import re

file_path = 'Relations.md'

def get_sort_key(line):
    # Regex to capture ID at start of line
    # Matches optional whitespace, then chars A-Z, then one of [ { (
    match = re.search(r'^\s*([A-Z]+)[\[{(]', line)
    if match:
        id_str = match.group(1)
        # return tuple: (length, text) to sort by length then lexically
        return (len(id_str), id_str)
    else:
        # If no ID found (e.g. empty line or comment?), append at end
        # Use a high length to push to bottom
        return (999, line)

def main():
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    header = []
    content_lines = []
    footer = []
    
    # Simple state machine
    for line in lines:
        if line.strip().startswith('```mermaid') or line.strip().startswith('graph LR'):
            header.append(line)
        elif line.strip() == '```':
            footer.append(line)
        elif line.strip() == '':
            pass # Skipping blank lines during sort, can add back differently if needed
        else:
            content_lines.append(line)
            
    # Sort content lines
    # Sort by ID length then ID text
    # Also we want to keep relations for same ID together? 
    # The default sort is stable, providing we sort by the key.
    
    sorted_lines = sorted(content_lines, key=get_sort_key)
    
    # Reassemble
    new_content = header
    new_content.extend(sorted_lines)
    if footer:
        new_content.extend(footer)
    else:
        new_content.append('```\n')
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    
    print("Sorted relations.")

if __name__ == '__main__':
    main()
