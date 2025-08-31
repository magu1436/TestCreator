import random
from typing import TypedDict, Literal

from django.shortcuts import get_object_or_404
from django.db.models import Q

from wordbank.models import WordList
from vocab.models import Word


class Range(TypedDict):
    start: int
    end: int


class Config(TypedDict):
    """テスト作成のHTMLに埋め込むための設定を保持する辞書"""
    wordlist: dict[str, str]
    ranges: list[Range]
    num_question: int
    sequence: Literal["ランダム", "番号順"]
    words: list[dict[str, int | str]]


def create_configure(configure) -> Config:
    """フロントから受け取ったJSONからテスト作成のための設定を作成する関数.
    
    Args:
        configure: フロントから受け取ったJSONデータ
    
    Returns:
        Config: テスト作成のための設定を保持する辞書
    """
    wordlist_id = configure["wordlistId"]
    wordlist = get_object_or_404(WordList, pk=wordlist_id)
    ranges = configure["ranges"]
    num_question = configure["numQuestion"]
    sequence = ""
    match configure["sequence"]:
        case "random": sequence = "ランダム"
        case "sequence": sequence = "番号順"
        case _: raise ValueError(f"sequence value error: {sequence}")

    # 複数の範囲指定に対応した番号の単語を取得
    q_obj = Q()
    for range in ranges:
        q_obj.add(Q(number__range=(range["start"], range["end"])), Q.OR)
    words = list(Word.objects.filter(Q(wordlist=wordlist), q_obj).values("number", "term", "meaning").order_by("number"))

    # フォーマットが "意味 → 単語" の場合, 単語と意味を入れ替えた辞書をコンテキストにわたす
    if configure["format"] == "qfr-mt":
        for w in words:
            w["term"], w["meaning"] = w["meaning"], w["term"]

    # 順番の確定
    if sequence == "ランダム":
        words = random.sample(words, k=(min(num_question, len(words))))
    
    param: Config = {
        "wordlist": {"name": wordlist.name},
        "ranges": ranges,
        "num_question": num_question,
        "sequence": sequence,
        "words": words,
    }
    
    return param