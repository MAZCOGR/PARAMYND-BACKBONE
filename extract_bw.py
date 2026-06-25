import re

filepath = r'c:\paramynd-admin\templates\building_workspace.html'
css_path = r'c:\paramynd-admin\static\css\building_workspace.css'
js_path = r'c:\paramynd-admin\static\js\building_workspace.js'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS
css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
if css_matches:
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_matches[0].strip() + '\n')
    content = re.sub(r'<style>.*?</style>', r'<link rel="stylesheet" href="/static/css/building_workspace.css">', content, count=1, flags=re.DOTALL)

# JS
js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
if js_matches:
    js_content = js_matches[0].strip()
    # Replace the Django template vars with dataset reads
    js_content = js_content.replace('const slug = "{{ slug }}";', "const slug = document.getElementById('tenant-data').dataset.slug;")
    
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content + '\n')
    
    script_replacement = r'<div id="tenant-data" data-slug="{{ slug }}" style="display:none;"></div>\n<script src="/static/js/building_workspace.js"></script>'
    content = re.sub(r'<script>.*?</script>', script_replacement, content, count=1, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done building_workspace.html")
