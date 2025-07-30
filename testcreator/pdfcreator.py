import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, FrameBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1) フォント登録
pdfmetrics.registerFont(TTFont('Noto', 'fonts/NotoSansJP-Regular.ttf'))

# 2) スタイル定義
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='Question',
    fontName='Noto',
    fontSize=12,
    leading=14,
))
styles.add(ParagraphStyle(
    name='Answer',
    fontName='Noto',
    fontSize=12,
    leading=14,
    leftIndent=12,
))
styles['Title'].fontName = 'Noto'
styles['Title'].fontSize = 18
styles['Normal'].fontName = 'Noto'

def df_to_story(df: pd.DataFrame, meta: dict):
    """
    DataFrame に以下のカラムがある前提：
      - prompt: 問題文（英単語 or 和訳）
      - answer: 解答文
    meta:
      - title, subtitle, date
    """
    story = []
    # タイトルセクション
    story.append(Paragraph(meta['title'], styles['Title']))
    story.append(Paragraph(meta['subtitle'], styles['Normal']))
    story.append(Paragraph(meta['date'], styles['Normal']))
    story.append(Spacer(1, 12))

    # 2段組用の FrameBreak 前まで問題を並べる
    for idx, row in df.iterrows():
        text = f"{idx+1}. {row['prompt']} __________"
        story.append(Paragraph(text, styles['Question']))
    # 段組終了
    story.append(FrameBreak())

    # 解答ページ
    story.append(Paragraph("解答", styles['Title']))
    story.append(Spacer(1, 12))
    for idx, row in df.iterrows():
        text = f"{idx+1}. {row['answer']}"
        story.append(Paragraph(text, styles['Answer']))

    return story


def build_from_dataframe(df: pd.DataFrame, meta: dict, out_path: str):
    # A4縦×２段組
    doc = BaseDocTemplate(out_path, pagesize=A4, title=meta['title'])
    frame_width = (A4[0] - doc.leftMargin - doc.rightMargin - 12) / 2
    frame1 = Frame(doc.leftMargin, doc.bottomMargin,
                   frame_width, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + frame_width + 12, doc.bottomMargin,
                   frame_width, doc.height, id='col2')
    # まず 2 段組テンプレートを登録
    two_col = PageTemplate(id='TwoCol', frames=[frame1, frame2])
    doc.addPageTemplates([two_col])

    # ドキュメンツ作成
    story = df_to_story(df, meta)
    doc.build(story)


if __name__ == '__main__':
    l = []
    for i in range(100):
        d = {}
        d["prompt"] = str(i)
        d["answer"] = str(i)
        l.append(d)
    df_all = pd.DataFrame(l)
    # ランダム抽出(シード固定)
    df = df_all.sample(n=50, random_state=20250730).reset_index(drop=True)

    # メタ情報
    meta = {
        'title': '小テスト',
        'subtitle': '英単語ターゲット1900 1〜1900番からランダム50問',
        'date': datetime.date.today().isoformat()
    }

    build_from_dataframe(df, meta, 'build/test_reportlab.pdf')
