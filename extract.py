import re
import os

def process_file(filepath, css_path, js_path):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

    css_name = os.path.basename(css_path)
    js_name = os.path.basename(js_path)

    if css_matches:
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_matches[0].strip() + '\n')
        content = re.sub(r'<style>.*?</style>', f'<link rel="stylesheet" href="/static/css/{css_name}">', content, count=1, flags=re.DOTALL)

    if js_matches:
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_matches[0].strip() + '\n')
        content = re.sub(r'<script>.*?</script>', f'<script src="/static/js/{js_name}"></script>', content, count=1, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

process_file(r'c:\paramynd-admin\templates\home.html', r'c:\paramynd-admin\static\css\home.css', r'c:\paramynd-admin\static\js\home.js')
