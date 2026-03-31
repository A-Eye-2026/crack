import os
import re

jikeon_base = r"c:\Users\수빈36\Desktop\플라스크\Crack\지건브랜치\templates"
local_base = r"c:\Users\수빈36\Desktop\플라스크\Crack\templates"

def sync_file(filename, layout_fixes=True):
    with open(os.path.join(jikeon_base, filename), 'r', encoding='utf-8') as f:
        content = f.read()
    
    if layout_fixes:
        # 1. min-height: 650px -> min-height: auto
        content = content.replace("min-height: 650px;", "min-height: auto;")
        
        # 2. flex: 1; in .section -> flex: 0 0 auto;
        # Use regex to be safe
        content = re.sub(r'(\.section\s*\{[^}]*?flex:\s*)1(;)', r'\1 0 0 auto\2', content, flags=re.DOTALL)
        
        # 3. .table-shell flex: 1 -> flex: 0 0 auto
        content = re.sub(r'(\.table-shell\s*\{[^}]*?flex:\s*)1(;)', r'\1 0 0 auto\2', content, flags=re.DOTALL)
        
        # 4. .table-wrap flex: 1 -> flex: 0 0 auto
        content = re.sub(r'(\.table-wrap\s*\{[^}]*?flex:\s*)1(;)', r'\1 0 0 auto\2', content, flags=re.DOTALL)

        # 5. Move pagination outside for members
        if filename == "admin_members.html":
            # Find the pagination block and move it
            pattern = re.compile(r'({% if total_pages > 1 %}.*?{% endif %})\s*(</section>)', re.DOTALL)
            content = pattern.sub(r'\2\n\n\1', content)
            
        # 6. Move pagination outside for incidents
        if filename == "admin_incidents.html":
            # Find the pagination block and move it
            # The pattern for incidents is a bit different
            pattern = re.compile(r'({% if total_pages > 1 %}.*?{% endif %})\s*(</form>\s*</section>)', re.DOTALL)
            content = pattern.sub(r'\2\n\n\1', content)

    with open(os.path.join(local_base, filename), 'w', encoding='utf-8') as f:
        f.write(content)

# Run sync
sync_file("admin_members.html")
sync_file("admin_incidents.html")
sync_file("admin_layout.html", layout_fixes=False) # Layout should stay as Jikeon's but with my earlier app fixes? 
# Actually, I'll just copy layout exactly for now.
print("Sync complete.")
