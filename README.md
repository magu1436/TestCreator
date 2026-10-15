# WordTestCreator

このアプリケーションは単語帳を管理し, それをもとに単語テストを作成するWebアプリケーションです.  
サーバーサイドは主に `Django` フレームワークを使用して `Python` で記述されています.  
フロントエンドの処理は `Bootstrap` を利用して `HTML` + `CSS` で記述されており, 動的処理は `TypeScript` で記述したものをコンパイルした `JavaScript` で記述されています.  

# 開発用データベース

`DEBUG=True` の場合は MySQL を使用します。`.env.example` を `.env` にコピーし、
接続情報を設定してください。既存の `.env` がある場合は MySQL の項目を追記します。
`MYSQL_HOST=db` は Compose の DB サービス名を想定しています。
ホスト側で Django を実行する場合は、公開ポートに合わせてホストを `127.0.0.1`、
ポートを変更してください。`DEBUG=False` の設定は従来の SQLite のままです。

ドライバーは `mysqlclient` を使用します。Linux でソースからインストールする際は、
Python の開発用ヘッダーと `default-libmysqlclient-dev`、`build-essential`、`pkg-config`
が必要です。これらは今後、開発用 Dockerfile に追加します。

Compose の DB 定義は今後追加します。MySQL 8.0.11 以上で、データベースを
`utf8mb4`・InnoDB で作成し、設定したユーザーにその DB の権限を与えてください。
DB の起動後、以下を実行します。

```sh
python -m pip install -r requirements.txt
python manage.py check --database default
python manage.py migrate
python manage.py createsuperuser
```

モデルと既存のマイグレーションはそのまま利用します。SQLite のデータは自動移行されません。
既存データが必要な場合は、切り替え前の SQLite から別途エクスポートして移行してください。
MySQL の照合順序によってはユーザー名などの大文字小文字の区別が変わるため、
データ移行時には一意制約の重複も確認してください。

# OCR機能
単語帳の登録は `OpenAI` のAPIを用いて, ChatGPTによるOCRにより, 写真から登録することができます.  
APIを利用するにはAPIキーを取得し, ルートディレクトに `.env` ファイルを配置して以下のように記述してください.  
```
API_KEY = "your_api_key"
```
