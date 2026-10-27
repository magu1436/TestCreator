
from typing import Final

from django.conf import settings
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS


CSS_NAME: Final[str] = "quiz.css"

def create_pdf(html: str):
    """HTMLをPDFに変換する関数.  
    
    Args:
        html (str): PDFに変換するHTMLの文字列.
    Return:
        bytes: PDFのバイトデータ.
    """
    pdf = HTML(
        string=html, 
        base_url=settings.BASE_DIR
    ).write_pdf(
        stylesheets=[CSS(filename=finders.find("quiz/css/" + CSS_NAME))],
    )
    if (not(pdf)): raise ValueError("create pdf failed")
    return pdf