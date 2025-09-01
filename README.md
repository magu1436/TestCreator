# WordTestCreator

このアプリケーションは単語帳を管理し, それをもとに単語テストを作成するWebアプリケーションです.  
サーバーサイドは主に `Django` フレームワークを使用して `Python` で記述されています.  
フロントエンドの処理は `Bootstrap` を利用して `HTML` + `CSS` で記述されており, 動的処理は `TypeScript` で記述したものをコンパイルした `JavaScript` で記述されています.  

# OCR機能
単語帳の登録は `OpenAI` のAPIを用いて, ChatGPTによるOCRにより, 写真から登録することができます.  
APIを利用するにはAPIキーを取得し, ルートディレクトに `.env` ファイルを配置して以下のように記述してください.  
```
API_KEY = "your_api_key"
```