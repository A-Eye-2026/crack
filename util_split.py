import re
import os

def split_ppt():
    file_path = "templates/ppt.html"
    out_dir = "templates/ppt"
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all spots using regex for the start tag and manual logic for matching ending div
    spots = []
    
    # regex to match `<div class="spot" id="...">` or `<div class="spot scatter-init" id="...">` etc
    # Actually, looking at the code, they are just `<div class="spot" id="spot-...">`
    
    pattern = re.compile(r'(<div[^>]*class="[^"]*spot[^"]*"[^>]*id="([^"]+)"[^>]*>)')
    
    parts = []
    last_idx = 0
    
    for match in pattern.finditer(content):
        start_tag = match.group(1)
        spot_id = match.group(2)
        start_idx = match.start()
        
        # Append anything before this spot opening
        parts.append(content[last_idx:start_idx])
        
        # Find closing div
        depth = 1
        curr_idx = match.end()
        while depth > 0 and curr_idx < len(content):
            next_open = content.find("<div", curr_idx)
            next_close = content.find("</div>", curr_idx)
            
            if next_close == -1:
                break
                
            if next_open != -1 and next_open < next_close:
                depth += 1
                curr_idx = next_open + 4
            else:
                depth -= 1
                curr_idx = next_close + 6
                
        end_idx = curr_idx
        
        spot_html = content[start_idx:end_idx]
        
        # Save to file
        slide_filename = spot_id + ".html"
        slide_path = os.path.join(out_dir, slide_filename)
        with open(slide_path, "w", encoding="utf-8") as out_f:
            out_f.write(spot_html)
            
        print(f"Extracted {spot_id} into {slide_filename} ({len(spot_html)} bytes)")
        
        # Add include tag
        parts.append(f"{{% include 'ppt/{slide_filename}' %}}")
        
        last_idx = end_idx

    parts.append(content[last_idx:])
    
    new_content = "".join(parts)
    
    # Save a backup just in case
    with open("templates/ppt_backup.html", "w", encoding="utf-8") as f:
        f.write(content)
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print(f"\nDone! Extracted {len(spots)} spots. Splitting complete.")

if __name__ == "__main__":
    split_ppt()
