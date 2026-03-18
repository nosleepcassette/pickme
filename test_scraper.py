import re

def extract_tab_blocks(text):
    text = re.sub(r'<[^>]+>', '', text)
    lines = text.splitlines()
    
    def is_tab_line(l):
        l = l.strip()
        # Must have dashes and numbers, and probably starts with a dash or a string label
        # Example: "-2-------" or "e|---2---" or "E|-------"
        if not l: return False
        
        # Strip string label if present
        m = re.match(r'^([eBGDAEebgdae1-6])\s*\|(.*)', l)
        content = m.group(2) if m else l
        
        content = content.strip()
        if not content: return False
        
        # Must have dashes
        if '-' not in content: return False
        
        # Most of the line should be dashes, numbers, spaces, h, p, /, \, s, b, r, etc.
        # Let's check the ratio of valid tab chars
        valid_chars = set("-0123456789hps/\\| ")
        valid_count = sum(1 for c in content if c in valid_chars)
        
        if len(content) < 10: return False # too short
        
        if valid_count / len(content) > 0.8:
            return True
        return False

    blocks = []
    current_block = []
    
    # We want to gather 6 consecutive tab lines
    # Sometimes they are separated by a blank line or a line with ` |   ^   | ` (beat markers)
    # Let's just collect lines, and if we hit 6 valid tab lines close together, we take it.
    
    for line in lines:
        if is_tab_line(line):
            # Check if it has a label
            m = re.match(r'^([eBGDAEebgdae1-6])\s*\|(.*)', line.strip())
            if m:
                label = m.group(1).upper()
                content = m.group(2)
            else:
                # No label, just assign e,B,G,D,A,E based on index
                string_names = ["e", "B", "G", "D", "A", "E"]
                label = string_names[len(current_block)] if len(current_block) < 6 else 'E'
                content = line.strip()
            
            if label == 'E' and len(current_block) == 0: label = 'e'
            current_block.append((label, content))
            if len(current_block) == 6:
                blocks.append(current_block)
                current_block = []
        else:
            # If we hit a non-tab line, maybe it's just a beat marker line.
            # But if we accumulate too many non-tab lines, we should reset.
            # For simplicity, let's allow a beat marker line.
            l = line.strip()
            if l.startswith('|') and '^' in l:
                pass # skip beat marker
            elif l == '':
                pass # skip blank
            else:
                if current_block:
                    current_block = []
                
    return blocks

import urllib.request
req = urllib.request.Request("http://www.sweetadeline.net/angeleswoody.txt", headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')

blocks = extract_tab_blocks(html)
print(f"Found {len(blocks)} blocks")
