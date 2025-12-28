import json
import re

path = r'data\processed\FORM44_Synthetic_001.json'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except:
    with open(path, 'r', encoding='latin-1') as f:
        data = json.load(f)

text = data.get('text', '')
print("LEN:", len(text))

# Find Corrective Action block
idx = text.find("Corrective Action")
if idx != -1:
    print("--- FOUND AT", idx)
    snippet = text[idx:idx+200]
    print(ascii(snippet))
    print("---")
else:
    print("NOT FOUND")
