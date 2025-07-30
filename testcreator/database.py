
from pathlib import Path
from typing import NoReturn

import sqlite3
import pandas as pd

from .utilities import get_config_value

DATABASE_NAME_KEY = "database_name"

class VocabularyData(pd.DataFrame):
    """語彙データベースを保持するクラス."""
    database_path: Path = Path(get_config_value(DATABASE_NAME_KEY))

    def __init__(self, wordbook_name: str):
        self.wordbook_name: str = wordbook_name
        with sqlite3.connect(self.database_path) as conn:
            sql = self._create_get_table_sql()
            super().__init__(pd.read_sql(sql, conn))
    
    def _create_get_table_sql(self) -> str:
        return f"SELECT * FROM {self.wordbook_name}"
    
    def save(self):
        """データベースへ保存するメソッド."""
        with sqlite3.connect(self.database_path) as conn:
            self.to_sql(
                self.wordbook_name,
                conn,
                if_exists="replace",
                index=True,
            )


class RangedVocabularyData(VocabularyData):
    """限られた範囲の語彙データベースを保持するクラス.
    
    一部のデータを参照するだけの処理では, 処理の軽量化のためにこのクラスを用いる.  
    このクラスはデータの参照のみを行い, データベースの変更を行うことはできない.  """

    def __init__(self, wordbook_name: str, start_index: int, end_index: int):
        self.start_index = start_index
        self.end_index = end_index
        super().__init__(wordbook_name)

    def _create_get_table_sql(self):
        return f"SELECT {self.start_index} <= index, index <= {self.end_index} FROM {self.wordbook_name}"
    
    def save(self) -> NoReturn:
        raise ValueError("'RangedVocabularyData' cannot save data into database.")