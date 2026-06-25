import re

filepath = r'c:\paramynd-admin\templates\tenants\detail.html'
js_path = r'c:\paramynd-admin\static\js\tenant_detail.js'
css_path = r'c:\paramynd-admin\static\css\tenant_detail.css'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Modify HTML to add data-uri
content = content.replace('data-value="{{ tag.tag }}" data-ready=', 'data-value="{{ tag.tag }}" data-uri="{{ tag.uri }}" data-ready=')

# Extract CSS
css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
if css_matches:
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_matches[0].strip() + '\n')
    content = re.sub(r'<style>.*?</style>', r'<link rel="stylesheet" href="/static/css/tenant_detail.css">', content, count=1, flags=re.DOTALL)

# Extract JS
js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
if js_matches:
    # There are TWO script blocks in detail.html! 
    # Let's combine them into one file.
    combined_js = ""
    for idx, match in enumerate(js_matches):
        js_content = match.strip()
        
        # Remove tagsData block
        tagsData_pattern = r'const tagsData = \{\s*\{% for tag in available_tags %\}\s*".*?": ".*?",\s*\{% endfor %\}\s*\};'
        js_content = re.sub(tagsData_pattern, '', js_content, flags=re.DOTALL)
        
        # Replace the preview logic
        js_content = js_content.replace("""  if (select) {
    select.addEventListener('change', function() {
      const uri = tagsData[this.value];
      preview.textContent = uri ? `URI: ${uri}` : '';
    });
  }""", "")
        
        js_content = js_content.replace(
            "select.value = value;", 
            "select.value = value;\n        const uri = this.getAttribute('data-uri');\n        if (preview) preview.textContent = uri ? `URI: ${uri}` : '';"
        )
        
        combined_js += js_content + "\n\n"
        
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(combined_js)
    
    # Remove all script blocks and replace the last one with the src link
    content = re.sub(r'<script>.*?</script>', '', content, flags=re.DOTALL)
    content = content.replace('{% block scripts %}\n', '{% block scripts %}\n<script src="/static/js/tenant_detail.js"></script>\n')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done detail.html")
