# WordTestCreator

このアプリケーションは単語帳を管理し, それをもとに単語テストを作成するWebアプリケーションです.  
サーバーサイドは主に `Django` フレームワークを使用して `Python` で記述されています.  
フロントエンドの処理は `Bootstrap` を利用して `HTML` + `CSS` で記述されており, 動的処理は `TypeScript` で記述したものをコンパイルした `JavaScript` で記述されています.  

# DevContainer での開発

Docker Desktop（Linux コンテナ）と VS Code の Dev Containers 拡張機能を使用します。

1. `.env.example` を `.env` にコピーします。既存の `.env` がある場合は MySQL の項目を追記します。
2. VS Code で `Dev Containers: Reopen in Container` を実行します。
3. 初回は Python 依存のインストール、`npm ci`、TypeScript ビルド、DB のチェックが自動実行されます。
4. コンテナのターミナルで以下を実行します。

```sh
python manage.py migrate
python manage.py createsuperuser  # 初回のみ
python manage.py runserver 0.0.0.0:8000
```

ブラウザーで `http://localhost:8000` を開きます。Django は F5 の既存のデバッグ構成でも起動できます。
`npm run watch` はフォルダーを開くと専用のタスクターミナルで自動起動します。
VS Code が自動タスクの許可を求めた場合は許可してください。
停止は `Tasks: Terminate Task`、再開は `Tasks: Run Task` → `DevContainer: TypeScript watch` を選びます。
同じコンテナでは監視タスクを一つに制限しています。手動で `npm run watch` を重ねて起動しないでください。
Windows の共有フォルダーで変更が検知されない場合は、プロジェクトを WSL 側に置く方法を検討してください。

MySQL 8.4 は `db:3306` で接続し、ホストにはポートを公開しません。
Compose はルートの `.env` を明示的に読み込みます。
DevContainer 内では `MYSQL_HOST=db`・`MYSQL_PORT=3306` を固定します。
文字コードは `utf8mb4`、照合順序は大文字小文字・アクセントを区別する `utf8mb4_0900_as_cs` です。
DB データと `node_modules` は名前付きボリュームに保存します。Python 仮想環境は `/opt/venv` に置きます。
コンテナを再ビルドしても DB は保持され、Python の依存は再インストールされます。
依存定義を変更した場合は `bash .devcontainer/post-create.sh` を再実行してください。
その際は、先に監視タスクを停止し、完了後に再開します。

MySQL のユーザー・パスワード・DB 名はデータ領域が空の初回起動時に設定されます。
初期化後に `.env` を変更するだけでは DB 内の設定は変わりません。
既存の認証情報で接続してユーザーや DB を変更し、その後 `.env` を揃えてください。
通常の停止ではボリュームを削除しません。`docker compose down -v` は DB データも削除するため、
データを破棄して初期化し直す場合にだけ使ってください。

動作確認には DB 接続チェックとマイグレーションに加えて、ログイン・単語帳の登録・日本語 PDF の生成を確認します。
コンテナ定義を変更した場合は `Dev Containers: Rebuild Container` を実行してください。

# 開発用データベース

`DEBUG=True` の場合は MySQL を使用します。`.env.example` を `.env` にコピーし、
接続情報を設定してください。既存の `.env` がある場合は MySQL の項目を追記します。
`MYSQL_HOST=db` は Compose の DB サービス名を想定しています。
ホスト側で Django を実行する場合は、公開ポートに合わせてホストを `127.0.0.1`、
ポートを変更してください。`DEBUG=False` の設定は従来の SQLite のままです。

ドライバーは `mysqlclient` を使用します。Linux でソースからインストールする際は、
Python の開発用ヘッダーと `default-libmysqlclient-dev`、`build-essential`、`pkg-config`
が必要です。これらは `.devcontainer/Dockerfile` に含めています。

DevContainer 以外で DB を用意する場合は、MySQL 8.0.11 以上で、データベースを
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
