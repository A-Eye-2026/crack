import re

with open(r'c:\Users\수빈36\Desktop\플라스크\Crack\templates\ppt.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract spots (slides)
spots = re.split(r'<div class="spot', html)
results = []
for i, spot in enumerate(spots[1:], 1):
    # Remove HTML tags to get pure text
    text = re.sub(r'<[^>]+>', ' ', spot)
    # Condense whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    if text:
        results.append(f"Slide {i}: {text[:500]}") # Only first 500 chars to see what it is

with open(r'c:\Users\수빈36\Desktop\플라스크\Crack\ppt_parsed.txt', 'w', encoding='utf-8') as f:
    f.write("\n\n-----------------\n".join(results))

print("Parsing complete.")
