
from pathlib import Path

from weasyprint import HTML

OUTPUTS_FOLDER = "outputs"
HTML_DIR = "tests"
PDF_NAME = "outputs.pdf"

def create_pdf():
    with open("tests/test.html", "r", encoding="UTF-8") as f:
        html_content = f.read()
        HTML(string=html_content, base_url=HTML_DIR).write_pdf(Path(OUTPUTS_FOLDER, PDF_NAME))


create_pdf()
