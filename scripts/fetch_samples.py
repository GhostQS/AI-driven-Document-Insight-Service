import os
import pathlib
import requests

SAMPLE_DIR = pathlib.Path(__file__).resolve().parents[1] / "sample_docs"
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "invoice_sample.pdf": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "scanned_note.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Handwriting_sample_-_journal.jpg/640px-Handwriting_sample_-_journal.jpg",
}

for name, url in FILES.items():
    path = SAMPLE_DIR / name
    if path.exists():
        print(f"Exists: {path}")
        continue
    try:
        print(f"Downloading {url} -> {path}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Failed to download {url}: {e}")

print("Done.")
