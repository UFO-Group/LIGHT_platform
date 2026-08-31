# Fix smart quotes in Python file
with open('fetch_material_frequencies.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace smart quotes with regular quotes
content = content.replace('\u201c', '"')  # Left double quote
content = content.replace('\u201d', '"')  # Right double quote
content = content.replace('\u2018', "'")  # Left single quote
content = content.replace('\u2019', "'")  # Right single quote
content = content.replace('\u2013', '-')  # En dash to hyphen
content = content.replace('\u2014', '-')  # Em dash to hyphen

with open('fetch_material_frequencies.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed smart quotes')
