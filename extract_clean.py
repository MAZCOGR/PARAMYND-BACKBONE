import re
import os

clean_files = [
    (r'c:\paramynd-admin\templates\request_demo.html', 'request_demo.css', 'request_demo.js'),
    (r'c:\paramynd-admin\templates\verify_otp.html', 'verify_otp.css', None),
    (r'c:\paramynd-admin\templates\accounts\login.html', 'login.css', 'login.js'),
    (r'c:\paramynd-admin\templates\accounts\roles\matrix.html', 'role_matrix.css', None),
    (r'c:\paramynd-admin\templates\accounts\users\password_reset.html', 'password_reset.css', None),
    (r'c:\paramynd-admin\templates\monitoring\logs.html', 'logs.css', 'logs.js'),
    (r'c:\paramynd-admin\templates\tenants\list.html', 'tenant_list.css', 'tenant_list.js'),
    (r'c:\paramynd-admin\templates\tenants\saas_commits.html', 'saas_commits.css', None),
    (r'c:\paramynd-admin\templates\tenants\partials\create_form.html', None, 'tenant_create_form.js')
]

for filepath, css_name, js_name in clean_files:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    css_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    js_matches = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

    if css_matches and css_name:
        css_path = os.path.join(r'c:\paramynd-admin\static\css', css_name)
        with open(css_path, 'w', encoding='utf-8') as f:
            for match in css_matches:
                f.write(match.strip() + '\n\n')
        content = re.sub(r'<style>.*?</style>', f'<link rel="stylesheet" href="/static/css/{css_name}">', content, count=0, flags=re.DOTALL)

    if js_matches and js_name:
        js_path = os.path.join(r'c:\paramynd-admin\static\js', js_name)
        with open(js_path, 'w', encoding='utf-8') as f:
            for match in js_matches:
                f.write(match.strip() + '\n\n')
        content = re.sub(r'<script>.*?</script>', f'<script src="/static/js/{js_name}"></script>', content, count=0, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done extracting clean files.")
