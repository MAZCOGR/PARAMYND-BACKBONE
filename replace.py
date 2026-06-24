import re

with open(r'c:\paramynd-admin\templates\home.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract and delete integ-section
integ_pattern = re.compile(r'<!-- ══════════════ INTEGRATIONS ══════════════ -->\n<section class=\"section integ-section\" id=\"integrations\">.*?</section>\n', re.DOTALL)
integ_match = integ_pattern.search(content)
if not integ_match:
    print('Could not find integ-section')
    exit(1)

integ_html = integ_match.group(0)
content = content.replace(integ_html, '')

# 2. Find logos-band and replace with integ-section
logos_pattern = re.compile(r'<!-- ══════════════ LOGOS ══════════════ -->\n<div class=\"logos-band\">.*?</div>\n', re.DOTALL)
if not logos_pattern.search(content):
    print('Could not find logos-band')
    exit(1)

content = logos_pattern.sub(integ_html, content)

# 3. Find logos-band CSS and remove it
css_pattern = re.compile(r'/\* ════════════════════════════════\n   LOGOS BAND\n   ════════════════════════════════ \*/\n\.logos-band \{.*?\n\}\n', re.DOTALL)
content = css_pattern.sub('/* Logos band removed */\n', content)

with open(r'c:\paramynd-admin\templates\home.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success')
