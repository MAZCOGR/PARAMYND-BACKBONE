import re

filepath = r'c:\paramynd-admin\templates\tenants\builds.html'
js_path = r'c:\paramynd-admin\static\js\builds.js'
css_path = r'c:\paramynd-admin\static\css\builds.css'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract CSS
css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
if css_matches:
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_matches[0].strip() + '\n')
    content = re.sub(r'<style>.*?</style>', r'<link rel="stylesheet" href="/static/css/builds.css">', content, count=1, flags=re.DOTALL)

# Extract JS
js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
if js_matches:
    js_content = js_matches[0].strip()
    
    # Replace {{ csrf_token }} with a function call
    js_content = """function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}
""" + js_content.replace("'{{ csrf_token }}'", "getCsrfToken()")
    
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content + '\n')
    
    content = re.sub(r'<script>.*?</script>', r'<script src="/static/js/builds.js"></script>', content, count=1, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done builds.html")
