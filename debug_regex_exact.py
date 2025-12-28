
import re

# Simulate CRLF
snippet = 'Corrective Action:\r\nii. Preventive Action: Implement quality cont'

regex_current = r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=\n?\s*ii\.|\n\s*Preventive Action)"

m = re.search(regex_current, snippet, re.I)
if m:
    print(f"MATCH CURRENT: '{ascii(m.group(1))}'")
else:
    print("NO MATCH CURRENT")

regex_robust = r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=(?:[\s\r\n]*)ii\.|\n\s*Preventive Action)"
m2 = re.search(regex_robust, snippet, re.I)
if m2:
    print(f"MATCH ROBUST: '{ascii(m2.group(1))}'")
else:
    print("NO MATCH ROBUST")
