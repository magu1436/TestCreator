"""デモ専用JSONからOCR練習用JPEGを生成する。実行時配信には使わない。"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, required=True, help='日本語対応フォントのパス')
    parser.add_argument('--output', type=Path, required=True, help='出力JPEGのパス')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent.parent / 'demo/data/samples.json'
    sample = json.loads(source.read_text(encoding='utf-8-sig'))['ocr_samples']
    font = ImageFont.truetype(str(args.font), 42)
    title_font = ImageFont.truetype(str(args.font), 48)
    image = Image.new('RGB', (1400, 1500), 'white')
    draw = ImageDraw.Draw(image)
    draw.text((80, 55), '英単語 OCR練習用サンプル', font=title_font, fill='black')
    columns = (80, 280, 760, 1320)
    top = 175
    row_height = 110
    rows = [('番号', '単語', '意味')] + [
        (str(word['number']), word['term'], word['meaning']) for word in sample['words']
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        draw.line((columns[0], y, columns[-1], y), fill='black', width=2)
        for x, text in zip(columns, row):
            draw.text((x + 22, y + 22), text, font=font, fill='black')
    bottom = top + len(rows) * row_height
    draw.line((columns[0], bottom, columns[-1], bottom), fill='black', width=2)
    for x in columns:
        draw.line((x, top, x, bottom), fill='black', width=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format='JPEG', quality=95, subsampling=0)
    print(f'{len(sample["words"])}語のOCR練習画像を生成しました: {args.output}')


if __name__ == '__main__':
    main()
