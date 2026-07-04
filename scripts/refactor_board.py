import os, re

board_path = r'c:\paramynd-admin\templates\projects\board.html'
with open(board_path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSS
start_style = content.find('<style>') + len('<style>\n')
end_style = content.find('</style>')
css_content = content[start_style:end_style]

os.makedirs(r'c:\paramynd-admin\static\css', exist_ok=True)
with open(r'c:\paramynd-admin\static\css\board.css', 'w', encoding='utf-8') as f:
    f.write(css_content)

# Modals
start_modal = content.find('<!-- Modal Sprint -->')
end_modal = content.find('<script>')
modals_content = content[start_modal:end_modal]

os.makedirs(r'c:\paramynd-admin\templates\projects\partials', exist_ok=True)
with open(r'c:\paramynd-admin\templates\projects\partials\board_modals.html', 'w', encoding='utf-8') as f:
    f.write(modals_content)

# JS
start_js = content.find('window._graphSnapDist   = 900;') + len('window._graphSnapDist   = 900;\n')
end_js = content.find('</script>')
js_content = content[start_js:end_js]

os.makedirs(r'c:\paramynd-admin\static\js', exist_ok=True)
with open(r'c:\paramynd-admin\static\js\board.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

# Assemble new board.html
new_board = content[:content.find('<style>')]
new_board += '{% load static %}\n<link rel="stylesheet" href="{% static \'css/board.css\' %}">\n\n'

# Body without CSS
body_part = content[end_style + len('</style>\n') : start_modal]
# Remove task-meta div
body_part = re.sub(r'\s*<!-- Sprint chip -->\s*<div class="task-meta">.*?</div>', '', body_part, flags=re.DOTALL)

new_board += body_part
new_board += '{% include "projects/partials/board_modals.html" %}\n\n'
new_board += '<script>\n'
new_board += content[content.find('// ── HTMX-safe globals'):start_js]
new_board += '</script>\n'
new_board += '<script src="{% static \'js/board.js\' %}"></script>\n'
new_board += content[end_js + len('</script>\n') :]

with open(board_path, 'w', encoding='utf-8') as f:
    f.write(new_board)

print("Refactoring complete.")
