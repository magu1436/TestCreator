
import datetime
from pathlib import Path
from typing import Final

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils import timezone
from weasyprint import HTML, CSS


CSS_NAME: Final[str] = "quiz.css"

def create_pdf(html: str):
    """HTMLをPDFに変換して保存する関数.  
    
    Args:
        html (str): PDFに変換するHTMLの文字列.
    """
    print(finders.find("quiz/css/" + CSS_NAME))
    HTML(
        string=html, 
        base_url=settings.BASE_DIR
    ).write_pdf(
        Path(settings.OUTPUT_PDF_DIR, __create_name()),
        stylesheets=[CSS(filename=finders.find("quiz/css/" + CSS_NAME))],
    )

def __create_name():
    now = timezone.localtime(timezone.now())
    return now.strftime("%Y%m%d_%H%M%S_%f.pdf")