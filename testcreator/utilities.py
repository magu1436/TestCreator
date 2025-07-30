from pathlib import Path
from typing import Any

import yaml

CONFIG_FILE_PATH: Path = Path("config.yaml")

def load_config() -> dict[str, str]:
    """設定ファイルの値を全て取得して辞書として返すメソッド"""
    with open(CONFIG_FILE_PATH, "r") as file:
        config = yaml.safe_load(file)
    return config

def get_config_value(key: str) -> Any:
    """設定ファイルから指定のキーの値を返すメソッド.
    
    指定のキーの値は設定ファイルにない場合, `ValueError` を投げる.
    
    Args:
        key(str): 設定のキー
    
    Returns:
        ValueError: 指定のキーが `config.yaml` にない場合に生じる"""
    config_value = load_config().get(key, None)
    if config_value is None:
        raise ValueError(f"'{key}' is not registered as a key in config.yaml")
    return config_value