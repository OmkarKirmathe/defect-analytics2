
import re

full_text = """
c) Remedial Measures Replace entire assembly due to extent of damage
i. Corrective Action:
ii. Preventive Action: Implement quality control check at manufacturing stage
"""

# Try 1: Non-greedy whitespace?
# Or just handle the fact that we might be at 'ii.' immediately.
# If Corrective Action is empty, we want to match NOTHING.
# So `(?=ii\.)` should match immediately.

regex_improved = r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=\n?\s*ii\.|\n\s*Preventive Action)"
m = re.search(regex_improved, full_text, re.I)
if m:
    print(f"MATCH 1: '{m.group(1)}'")
else:
    print("MATCH 1: NO MATCH")

# Try 2: Exclude Roman numerals from capture
# Or explicit lookahead for starting Roman numeral
regex_improved_2 = r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=(?:^|\n)\s*ii\.|\n\s*Preventive Action)"
m2 = re.search(regex_improved_2, full_text, re.I | re.MULTILINE)
if m2:
    print(f"MATCH 2: '{m2.group(1)}'")
else:
    print("MATCH 2: NO MATCH")
    
# Try 3: What if we ensure we don' consume the newline using `[^\S\r\n]*` and explicit `\n`?
# But `\s` is convenient.
# Let's try stopping at `ii.` explicitly without newline constraint if it matches.

regex_3 = r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=\s*ii\.|\s*Preventive Action)"
m3 = re.search(regex_3, full_text, re.I)
if m3:
    print(f"MATCH 3: '{m3.group(1)}'")
    print(f"ASCII: {ascii(m3.group(1))}")
else:
    print("MATCH 3: NO MATCH")
