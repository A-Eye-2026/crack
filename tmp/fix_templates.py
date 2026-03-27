import re
import os

path = r'c:\Users\수빈36\Desktop\플라스크\Crack\templates\alert_view.html'
if not os.path.exists(path):
    print(f"File not found: {path}")
    exit(1)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix all variants of {{ detail.id }} or {{ detail.id }}} to exactly {{ detail.id }}
# This regex matches the center and then any number of surrounding curly braces
content = re.sub(r'\{\{\s*detail\.id\s*\}*\}*', '{{ detail.id }}', content)

# 2. Add missing semicolon if it was stripped
content = content.replace('var reportId = {{ detail.id }}\n', 'var reportId = {{ detail.id }};\n')

# 3. Fix the specific number parsing in JS
content = content.replace("Number('{{ detail.id }}')", "{{ detail.id }}") # Often better as direct number
# OR if we want to keep Number():
# content = content.replace("Number('{{ detail.id }}')", "Number('{{ detail.id }}')")

# 4. Correct the IIFE closing and bracket clutter
# Let's target the end of the CV logic more specifically
# The drawFrame function and listeners should be inside the IIFE.
# The IIFE closing was originally like }) (); or similar.
content = re.sub(r'\}\s*\)\s*;\s*\}\s*\)\s*;\s*', '})();\n', content)
content = re.sub(r'\}\s*;\s*\}\s*\)\s*;\s*', '})();\n', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Template fix executed successfully.")
