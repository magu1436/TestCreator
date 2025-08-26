
from abc import ABC
import base64
import json
from typing import TypedDict

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from openai import OpenAI
from openai.types import CompletionUsage

RATE = 146.85

class Word(TypedDict):
    number: int
    term: str
    meaning: str

class RequestResult(TypedDict):
    words: list[Word]
    cost: float
    errors: list[Exception]

class GPTModel(ABC):

    def __init__(self, model: str, input_price: float, output_price: float):
        """コンストラクタ
        
        Args:
            model(str): 使用するモデルの名前
            input_price(float): トークンに応じた入力時の金額($/MToken)
            output_price(float): トークンに応じた出力時の金額($/MToken)
        """
        self.model = model
        self.input_price = input_price
        self.output_price = output_price
    
    def request(self, file: UploadedFile) -> RequestResult:
        client = OpenAI(api_key=settings.API_KEY)
        result: RequestResult = {"words": None, "cost": None, "errors": None}
        try:
            res = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.__get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content":[
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.__to_base64(file)}",
                                },
                            },
                        ],
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.,
            )
            result["words"] = self.__to_word_dict_list(res.choices[0].message.content)
            result["cost"] = self.__calc_balance(res.usage)
        except Exception as e:
            result["errors"].append(e)
        return result


    def __calc_balance(self, usage: CompletionUsage) -> float:
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        return (input_tokens * self.input_price + output_tokens * self.output_price) * RATE / 1000000  # 1M = 1000000
    
    def __to_base64(self, image: UploadedFile) -> str:
        return base64.b64encode(image.read()).decode("utf-8")
    
    def __to_word_dict_list(self, json_str: str) -> list[dict[str, int | str]]:
        words = []
        json_dict = json.loads(json_str)
        for term, values in json_dict.items():
            words.append({
                "term": term,
                "number": values.get("number"),
                "meaning": values.get("meaning"),
            })
        return words
    
    def __get_system_prompt(self):
        prompt = """
    You are an OCR extractor for vocabulary lists. Input: an image of a word list containing a "number (integer) – word (English or classical Japanese word) – meaning (Japanese)" layout.

    Task: Return ONLY a single JSON object mapping each word to an object with fields "number" (integer) and "meaning" (Japanese string). No extra text, no explanations.

    Rules:
    - Output = JSON object: { "<word>": { "number": <int>, "meaning": "<ja>" }, ... }.
    - Trim whitespace; normalize digits (full-width → ASCII). Keep the word’s original spelling/case.
    - Meanings must be Japanese; join multiple senses with "、" (commas not required).
    - Ignore headers/footers/page numbers, parts of speech (n., v., etc.), examples/sentences, furigana, and decorative symbols.
    - If a line lacks either word or meaning, skip it. If the number is unreadable, set "number": null.
    - Deduplicate by word: keep the smallest number; merge meanings with "、".
    - Return valid JSON only.
    """
        return prompt


class GPT4oMini(GPTModel):
    """gpt-4o-miniモデルのクラス."""

    def __init__(self):
        model = "gpt-4o-mini"
        input_price = 0.15
        output_price = 0.60
        super().__init__(model, input_price, output_price)


class GPT5Mini(GPTModel):
    """gpt-5-miniモデルのクラス."""

    def __init__(self):
        model = "gpt-5-mini"
        input_price = 0.25
        output_price = 2.
        super().__init__(model, input_price, output_price)


class GPT5(GPTModel):
    """gpt-5モデルのクラス."""

    def __init__(self):
        model = "gpt-5"
        input_price = 1.25
        output_price = 10.
        super().__init__(model, input_price, output_price)