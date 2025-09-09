
from typing import Final
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone
from weasyprint import HTML, CSS


CSS_NAME: Final[str] = "quiz.css"
FILE_NAME_FORMAT: Final[str] = "%Y_%m_%d_%H_%M_%S_%f.pdf"

def create_pdf(html: str):
    """HTMLをPDFに変換する関数.  
    
    Args:
        html (str): PDFに変換するHTMLの文字列.
    Return:
        bytes: PDFのバイトデータ.
    """
    file_name = create_name()
    HTML(
        string=html, 
        base_url=settings.BASE_DIR
    ).write_pdf(
        target=Path(settings.OUTPUT_PDF_DIR, file_name),
        stylesheets=[CSS(filename=finders.find("quiz/css/" + CSS_NAME))],
    )
    return file_name


def create_name():
    now = timezone.localtime(timezone.now())
    return now.strftime(FILE_NAME_FORMAT)