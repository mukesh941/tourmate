import re
with open('temp.js') as f:
    content = f.read()
urls = set(re.findall(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d+)?(?:/[^\s\'"]*)?', content))
for u in urls:
    if "api" in u.lower() or "tourmate" in u.lower() or "render" in u.lower():
        print(u)
