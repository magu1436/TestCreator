

from pathlib import Path
from typing import TypedDict, Any
from dataclasses import dataclass

import sqlite3
import pandas as pd

from ..testcreator.utilities import get_config_value

DATABASE_NAME_KEY = "database_name"

@dataclass
class ColumnConfig:
    """列データの設定を示すデータクラス.  
    
    制約を細かく指定する場合に使用する."""
    name: str
    type: str | None = None
    primary_key: bool = False
    not_null: bool = False
    unique: bool = False
    check: str | None = None
    default: str | None = None
    collate: str | None = None
    references: str | None = None

    def to_args(self) -> str:
        arg_str = "name "
        if self.type is not None:
            arg_str += self.type + " "
        if self.primary_key:
            arg_str += "PRIMARY KEY "
        if self.not_null:
            arg_str += "NOT NULL "
        if self.unique:
            arg_str += "UNIQUE "
        for k, v in vars(self).items():
            if k in ("name", "type", "primary_key", "not_null", "unique"):
                continue
            if v is None:
                continue
            arg_str += k.upper() + " " + v + " "
        arg_str += ");"
        return arg_str


class ColumnDict(TypedDict):
    """列データの設定を示す辞書の型ヒント用のクラス"""
    name: str
    type: str


class DatabaseController:
    database_path: Path = Path(get_config_value(DATABASE_NAME_KEY))

    @classmethod
    def create_table(cls, table_name: str, *columns: ColumnConfig | ColumnDict) -> None:
        """データベース内にテーブルを作成するメソッド"""
        db = sqlite3.connect(
            cls.database_path,
            isolation_level=None,
        )

        sql = "CREATE TABLE "
        sql += table_name + "("
        for i in range(len(columns)):
            col = columns[i]
            if isinstance(col, ColumnConfig):
                sql += col.to_args()
            else:
                sql += f"{col['name']} {col['type']}"
            if i != len(columns) - 1:
                sql += ", "
        sql +=");"

        db.execute(sql)
        db.close()

    @classmethod
    def insert(cls, table_name: str, *values: Any) -> None:
        """データベースにレコードを追加するメソッド"""
        db = sqlite3.connect(
            cls.database_path,
            isolation_level=None,
        )

        sql = f"INSERT FROM {table_name} VALUES({', '.join(['?' for _ in range(len(values))])});"

        db.executemany(sql, [values])
        db.close()
    
    @classmethod
    def get_table(cls, table_name: str) -> pd.DataFrame:
        db = sqlite3.connect(
            cls.database_path,
            isolation_level=None,
        )

        df = pd.read_sql_query(f"SELECT * FROM {table_name}", db)

        db.close()
        return df
    