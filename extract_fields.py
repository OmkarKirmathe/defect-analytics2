# extract_fields.py
"""
FINAL CLEAN & CORRECTED SCRIPT (with small fixes)
- Sanitizes remarks to remove header/footer tokens
- Fallback extraction for corrective_action from Remedial Measures
- Strips role prefixes from approval names before saving
"""

from pathlib import Path
import json, re, os
from collections import OrderedDict
from datetime import datetime

# -----------------------------------------
# TRY DATEUTIL
# -----------------------------------------
try:
    from dateutil import parser as dtparser
    def try_parse_date(text):
        if not text:
            return None
        try:
            return dtparser.parse(text, dayfirst=True).date().isoformat()
        except:
            return None
except:
    def try_parse_date(text):
        if not text:
            return None
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text.strip(), fmt).date().isoformat()
            except:
                continue
        return None

# -----------------------------------------
# PATHS
# -----------------------------------------
PROC_DIR = Path("data/processed")
OUT_DIR = Path("data/structured")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------
# SAFE READER
# -----------------------------------------
def safe_read_json(path: Path):
    encs = ["utf-8", "latin-1", "cp1252"]
    for e in encs:
        try:
            txt = path.read_text(encoding=e)
            return json.loads(txt)
        except:
            pass
    try:
        txt = path.read_bytes().decode("utf-8", errors="replace")
        return json.loads(txt)
    except:
        return None

# -----------------------------------------
# CLEANERS
# -----------------------------------------
def clean_extracted_value(v):
    if not v:
        return v
    s = re.sub(r'\s*\n\s*', ' ', v.strip())
    s = re.sub(r'\s{2,}', ' ', s)
    s = re.sub(r'\s+[a-z]\)\s*$', '', s, flags=re.I)
    s = re.sub(r'\s+[ivx]+\.\s*$', '', s, flags=re.I)
    s = re.sub(r'^[ivx]+\.\s*$', '', s, flags=re.I)
    return s.strip()


def is_month_year(t):
    return bool(t and re.match(r'^[A-Za-z]+\s+[0-9]{4}$', t))


def split_life(l):
    if not l:
        return None, None
    m = re.search(r'([0-9,\.]+)\s*Hrs\s*\/\s*([0-9,\.]+)\s*Cycles', l, re.I)
    if not m: return None, None
    try:
        hrs = int(m.group(1).replace(',', '').split('.')[0])
        cyc = int(m.group(2).replace(',', '').split('.')[0])
        return hrs, cyc
    except:
        return None, None


def score_conf(src, length):
    s = (src or "").lower()
    if "full_text" in s and length > 20: return "high"
    if "full_text" in s and length > 5: return "medium"
    if "ocr" in s: return "medium"
    return "low"


def sanitize(cid):
    if not cid: return "UNKNOWN"
    cid = re.sub(r'[\\/]+', "_", cid)
    cid = re.sub(r'[^A-Za-z0-9_\-\.]', "_", cid)
    return cid

# -----------------------------------------
# REGEX SHORTCUTS
# -----------------------------------------
DATE_RE = re.compile(r"([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})")
AUTH_SIGN_RE = re.compile(
    r"(?:Authorized Signatory of|Authorized Signatory|Signature of|Signature)[:\-\s]*\s*(.+)",
    flags=re.I
)

# -----------------------------------------
# FIELD PATTERNS (corrected)
# -----------------------------------------
FIELD_PATTERNS = {
    "dr_no": [
        r"(DR/\d{4}/\d{3,5})",
        r"Defect Report.*?No[:\s]*([A-Za-z0-9/-]+)"
    ],

    "date_of_occurrence": [
        r"Date of Occurrence[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})"
    ],

    "aircraft": [
        r"Installation Details[:\s]*([\s\S]{1,200}?)(?=\n[a-z]\)|\nPart\s*-?\s*II|\n$)"
    ],

    # FIXED TRADE
    "trade": [
        r"Trade[:\s]*([A-Za-z0-9 \-/]+?)(?=\s*b\)|\s*c\)|\n|$)"
    ],

    # FIXED SYSTEM
    "system": [
        r"System(?:/Sub System)?[:\s]*([A-Za-z0-9 \-/]+?)(?=\s*[a-f]\)|\n|$)"
    ],

    # FIXED MAIN ASSEMBLY
    "main_assembly": [
        r"Main Assembly[:\s]*([A-Za-z0-9 \-/]+?)(?=\s*[a-f]\)|\n|$)"
    ],

    # FIXED NOMENCLATURE
    "nomenclature": [
        r"Nomenclature[:\s]*([A-Za-z0-9 \-/]+?)(?=\s*f\)|\n|$)"
    ],

    "mod_status": [
        r"MOD Status[:\s]*([A-Za-z0-9 \-]+)"
    ],

    "part_no": [
        r"Part\s*No[\.:\s]*([A-Za-z0-9\-\/]+)"
    ],

    "serial_no": [
        r"Sl\s*No[\.:\s]*([A-Za-z0-9\-\/]+)"
    ],

    "date_of_installation": [
        r"Date\s*of\s*Installation[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})"
    ],

    "date_of_removal": [
        r"Date\s*of\s*Removal[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})"
    ],

    # FIXED MANUFACTURER
    "manufacturer": [
        r"Manufactur(?:er|ing Agency)[:\s]*([A-Za-z0-9 .\-]+?)(?=\s*n\)|\n|$)"
    ],

    "manufacture_date": [
        r"Date, Month & Year[:\s]*([A-Za-z]+\s+[0-9]{4})"
    ],

    "warranty": [
        r"Whether under warranty[:\s]*(Yes|No)"
    ],

    "amc_repair_contract": [
        r"Whether under AMC[:\s]*(Yes|No)"
    ],

    "life": [
        r"Life completed.*?:\s*([0-9,\.]+\s*Hrs\s*\/\s*[0-9,\.]+\s*Cycles)"
    ],

    "defect_category": [
        r"Defect Category[:\s]*([A-Za-z \-]+)"
    ],

    "defect_observed": [
        r"Defect Observed[:\s]*([\s\S]{1,400}?)(?=\nPart\s*-?\s*IV|\n[a-z]\)|$)"
    ],

    "root_cause": [
        r"Root Cause Analysis[:\s]*([\s\S]{1,400}?)(?=(?:[\s\r\n]*)[a-z]\)|\nFindings|Corrective|Preventive|$)"
    ],

    "findings": [
        r"Findings\s*/\s*Conclusions[:\s]*([\s\S]{1,600}?)(?=(?:[\s\r\n]*)[a-z]\)|\nCorrective|Preventive|\nPart\s*-?\s*V|$)"
    ],

    "corrective_action": [
        r"Corrective Action[:\s]*([\s\S]{1,400}?)(?=(?:[\s\r\n]*)ii\.[\s\r\n]|(?:[\s\r\n]*)Preventive Action|(?:[\s\r\n]*)[a-z]\)|\nPart\s*-?\s*V|$)"
    ],

    "preventive_action": [
        r"Preventive Action[:\s]*([\s\S]{1,400}?)(?=(?:[\s\r\n]*)[a-z]\)|\nPart\s*-?\s*V|\nFindings|$)"
    ],

    # REMARKS (fixed)
    "remarks_investigation": [
        r"Part\s*-?\s*IV[\s\S]*?Remarks[:\s]*([\s\S]{1,600}?)(?=\nPart\s*-?\s*V|$)"
    ],

    "remarks_design": [
        r"Part\s*-?\s*V[\s\S]*?Remarks(?:\s*by\s*Design)?[:\s]*"
        r"([\s\S]{1,600}?)(?=\nPart\s*-?\s*VI|$)"
    ],

    "remarks_quality": [
        r"Part\s*-?\s*VI[\s\S]*?Remarks(?:\s*by\s*Quality)?[:\s]*"
        r"([\s\S]{1,600}?)(?=\nPart\s*-?\s*VII|$)"
    ],

    "remarks_user": [
        r"Part\s*-?\s*VII[\s\S]*?Remarks(?:\s*by\s*User|Project)?[:\s]*"
        r"([\s\S]{1,600}?)(?=\nPart\s*-?\s*VIII|$)"
    ],

    "remarks_ordaqa": [
        r"Part\s*-?\s*VIII[\s\S]*?Remarks(?:\s*by\s*ORDAQA)?[:\s]*"
        r"([\s\S]{1,600}?)(?=\nPart\s*-?\s*IX|$)"
    ],

    "remarks_cemilac": [
        r"Part\s*-?\s*IX[\s\S]*?Remarks(?:\s*by\s*CEMILAC|CEMILAC\s*/\s*RCMA)?[:\s]*"
        r"([\s\S]{1,600}?)(?=\nEdition|$)"
    ],
}

# -----------------------------------------
# EXTRACTOR
# -----------------------------------------
def extract_with_patterns(full_text, pages):

    # CLEAN PDF NOISE
    full_text = re.sub(r'---\s*Page\s*\d+.*?(?=\n)', "", full_text)
    full_text = re.sub(r'Centre for Military Airworthiness and Certification', '', full_text, flags=re.I)
    full_text = re.sub(r'\n{2,}', '\n\n', full_text)

    result = {}

    # GENERIC FIELD EXTRACTION
    for field, patterns in FIELD_PATTERNS.items():
        v = None
        src = None
        pat_used = None

        for pat in patterns:
            m = re.search(pat, full_text, re.I)
            if m:
                v = clean_extracted_value(m.group(1))
                src = "full_text"
                pat_used = pat
                break

        if field == "life" and v:
            hrs, cyc = split_life(v)
            v = {"raw": v, "hours": hrs, "cycles": cyc}

        conf = score_conf(src, len(str(v)) if v else 0)
        result[field] = {"value": v, "source": src, "pattern": pat_used, "confidence": conf}

    # -----------------------------------------
    # DATE COMPONENT RECEIVED — STRICT PART II
    # -----------------------------------------
    part2 = re.search(
        r"(Part\s*-?\s*II[\s\S]*?)(?=\nPart\s*-?\s*III|$)",
        full_text, re.I
    )
    part2_text = part2.group(1) if part2 else ""

    dcr = None
    if part2_text:
        m = re.search(
            r"Date\s*Component[\s\S]{0,40}?Received[:\s]*\n?\s*"
            r"([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})",
            part2_text, re.I
        )
        # NEW PATTERN: Date embedded between Date Component ... Received
        if not m:
            m = re.search(
                r"Date\s*Component\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})[\s\S]*?Received",
                part2_text, re.I
            )

        if m:
            dcr = m.group(1)
        else:
            # fallback forward scan
            lines = part2_text.splitlines()
            pos = None
            for i, ln in enumerate(lines):
                if "Received" in ln:
                    pos = i
                    break
            if pos is not None:
                for j in range(pos+1, min(pos+6, len(lines))):
                    dj = DATE_RE.search(lines[j])
                    if dj:
                        dcr = dj.group(1)
                        break

    result["date_component_received"] = {
        "value": dcr,
        "source": "partII" if dcr else None,
        "pattern": "partII_dcr" if dcr else None,
        "confidence": "high" if dcr else "low"
    }

    # -----------------------------------------
    # APPROVALS (DESIGN, QUALITY, USER, ORDAQA, CEMILAC)
    # -----------------------------------------
    approvals = {
        "design": None,
        "quality": None,
        "user": None,
        "ordaqa": None,
        "cemilac": None
    }

    part_roles = {
        5: "design",
        6: "quality",
        7: "user",
        8: "ordaqa",
        9: "cemilac"
    }

    romans = {5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}

    for pnum, key in part_roles.items():
        roman = romans.get(pnum, str(pnum))
        next_pnum = pnum + 1
        next_roman = romans.get(next_pnum, str(next_pnum))

        pat = (
            rf"(Part\s*-?\s*(?:{pnum}|{roman})[\s\S]*?)"
            rf"(?=\nPart\s*-?\s*(?:{next_pnum}|{next_roman})\b|Edition Number|$)"
        )

        block = re.search(pat, full_text, re.I)

        if not block:
            approvals[key] = {"name": None, "date": None}
            continue

        blk = block.group(1)

        # extract signatory name
        ms = AUTH_SIGN_RE.search(blk)
        name = clean_extracted_value(ms.group(1)) if ms else None

        # CLEAN ROLE PREFIXES FROM NAME (exact placement)
        if name:
            name = re.sub(r'^(?:Design|Quality|User|ORDAQA|CEMILAC)[:\-\s]*', '', name, flags=re.I)

        # extract date from last 8 lines
        date_val = None
        for line in reversed(blk.splitlines()[-8:]):
            md = DATE_RE.search(line)
            if md:
                date_val = try_parse_date(md.group(1)) or md.group(1)
                break

        approvals[key] = {"name": name, "date": date_val}

    result["approvals"] = approvals

    # -------------------------------
    # SANITIZE REMARKS (remove headers/footers)
    # -------------------------------
    def sanitize_remarks(s):
        if not s:
            return s
        s = re.sub(r'FORM\s*-\s*44', '', s, flags=re.I)
        s = re.sub(r'DEFECT INVESTIGATION REPORT FORMAT', '', s, flags=re.I)
        s = re.sub(r'Edition Number[:\s\S]*$', '', s, flags=re.I)
        s = re.sub(r'---\s*Page\s*\d+.*', '', s)
        s = re.sub(r'\n{2,}', '\n', s)
        return clean_extracted_value(s)

    for rkey in [
        "remarks_investigation",
        "remarks_design",
        "remarks_quality",
        "remarks_user",
        "remarks_ordaqa",
        "remarks_cemilac"
    ]:
        if result.get(rkey) and result[rkey]["value"]:
            result[rkey]["value"] = sanitize_remarks(result[rkey]["value"])

    # -----------------------------------------
    # Corrective fallback: if corrective_action is empty or too short, try remedial measures
    # -----------------------------------------
    curr_val = result.get("corrective_action", {}).get("value")
    if not curr_val or len(curr_val) < 5:
        m = re.search(r"Remedial Measures[:\s]*([\s\S]{1,600}?)(?=\ni\.|\nii\.|\nPart\s*-?\s*V|$)", full_text, re.I)
        if m:
            cand = clean_extracted_value(m.group(1))
            if cand:
                result["corrective_action"]["value"] = cand
                result["corrective_action"]["confidence"] = "high"

    return result


# -----------------------------------------
# CORRECTIVE FALLBACK (kept for completeness)
# -----------------------------------------
def corrective_fallback(text, cur):
    if cur and len(cur.strip()) > 10:
        return cur
    m = re.search(r"Remedial Measures[:\s]*([\s\S]{1,600}?)(?=\nPreventive|\nPart|$)", text, re.I)
    return clean_extracted_value(m.group(1)) if m else cur


# -----------------------------------------
# PROCESSOR
# -----------------------------------------
def process_all():
    files = sorted(PROC_DIR.glob("*.json"))
    N = int(os.environ.get("EXTRACT_N", len(files)))

    for p in files[:N]:
        rec = safe_read_json(p)
        if not rec:
            continue

        full_text = rec.get("text", "")
        pages = rec.get("pages") or rec.get("ocr_pages") or []

        fields = extract_with_patterns(full_text, pages)

        # corrective fallback (redundant but safe)
        cur = fields["corrective_action"]["value"]
        fixed = corrective_fallback(full_text, cur)
        if fixed and not fields["corrective_action"]["value"]:
            fields["corrective_action"]["value"] = fixed
            fields["corrective_action"]["confidence"] = "high"

        # ID
        cid = fields["dr_no"]["value"]
        cid = sanitize(cid or p.stem)

        out = OrderedDict()
        out["case_id"] = cid
        out["source_file"] = rec.get("file_name")
        out["extracted"] = fields
        out["raw_text_snippet"] = full_text[:2000] + "..."
        out["processed_ts"] = rec.get("processed_timestamp") or datetime.now().isoformat()

        out_path = OUT_DIR / f"{cid}.json"
        out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

        print("Wrote:", out_path)


if __name__ == "__main__":
    process_all()
