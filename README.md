# WordTestCreator

このアプリケーションは単語帳を管理し, それをもとに単語テストを作成するWebアプリケーションです.  
サーバーサイドは主に `Django` フレームワークを使用して `Python` で記述されています.  
フロントエンドの処理は `Bootstrap` を利用して `HTML` + `CSS` で記述されており, 動的処理は `TypeScript` で記述したものをコンパイルした `JavaScript` で記述されています.  

# 開発環境の構築

DevContainerを使用した環境構築・起動・管理者の作成手順は、[DevContainerでの環境構築](docs/devcontainer.md) を参照してください。

# 本番環境の構築

本番イメージのビルド・実行環境の設定・接続確認は、[本番環境の構築と実行](docs/deployment.md) を参照してください。

# OCR機能
単語帳の登録は `OpenAI` のAPIを用いて, ChatGPTによるOCRにより, 写真から登録することができます.  
APIを利用するにはAPIキーを取得し, ルートディレクトに `.env` ファイルを配置して以下のように記述してください.  
```
API_KEY = "your_api_key"
```
