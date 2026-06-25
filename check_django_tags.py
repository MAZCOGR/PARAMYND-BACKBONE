import re
import glob
import os

files = glob.glob('c:/paramynd-admin/templates/**/*.html', recursive=True)

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    styles = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
    scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
    
    for s in styles:
        if '{{' in s or '{%' in s:
            print(f"Django tag in CSS: {filepath}")
            
    for s in scripts:
        if '{{' in s or '{%' in s:
            print(f"Django tag in JS: {filepath}")
