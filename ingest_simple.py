import pdfplumber
import pytesseract
from PIL import Image
from pathlib import Path
import json
import datetime

RAW_DIR = Path("data/raw_pdfs")
OUT_DIR = Path("data/processed")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# If Windows and Tesseract isn't on PATH, set it manually:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_page(page):
    # Try direct text extraction
    text = page.extract_text()
    if text and len(text.strip()) > 50:
        return text, "pdf_text"
    # Fallback OCR
    img = page.to_image(resolution=200).original
    ocr_text = pytesseract.image_to_string(img)
    return ocr_text, "ocr"

def process_pdf(pdf_path):
    print(f"Processing: {pdf_path.name}")
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            t, source = extract_text_page(page)
            all_text.append(f"--- Page {i} ({source}) ---\n" + t)

    record = {
        "file_name": pdf_path.name,
        "processed_timestamp": datetime.datetime.now().isoformat(),
        "text": "\n\n".join(all_text)
    }

    out_file = OUT_DIR / f"{pdf_path.stem}.json"
    out_file.write_text(json.dumps(record, indent=2, ensure_ascii=False))

    print(f"Saved: {out_file}")

def main():
    pdfs = list(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in data/raw_pdfs/")
        return

    for pdf in pdfs:
        process_pdf(pdf)

if __name__ == "__main__":
    main()
