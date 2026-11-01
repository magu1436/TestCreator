# DevContainerでの環境構築

このプロジェクトを取得して初めて開発環境を作る方向けの手順です。以下の操作は、指定がなければプロジェクトルートで行います。

## 事前準備

- Gitでこのリポジトリを取得し、VS Codeでフォルダーを開きます。
- Docker Desktopをインストールし、Linuxコンテナが動作する状態で起動します。
- Docker Composeはincludeに対応した2.20以降を使用します。
- VS CodeにDev Containers拡張機能をインストールします。PythonとNode.jsはコンテナ内に用意されます。

## 初回起動

Docker Desktop（Linux コンテナ）と VS Code の Dev Containers 拡張機能を使用します。

1. `.env.example` を `.env` にコピーし、`DB_PASSWORD` に自分で決めたパスワードを設定します。
2. VS Code で `Dev Containers: Reopen in Container` を実行します。
3. 初回は Python 依存のインストール、`npm ci`、TypeScript ビルド、DB のチェック、マイグレーション、管理者の初期作成が自動実行されます。
4. コンテナのターミナルで以下を実行します。

```sh
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
DevContainer でも `.env` の `DB_HOST=db`・`DB_PORT=3306` を使用します。Compose 定義はルートの `compose.yml` です。
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

## セットアップの再実行と管理者の初期作成

DevContainer の初期化は `.devcontainer/post-create.sh` から共通の
`scripts/setup-dev.sh` を呼び出します。DevContainer 以外でも Python・Node.js・
MySQL を用意して、プロジェクトルートで以下を実行できます。

```sh
bash scripts/setup-dev.sh
```

依存のインストール → TypeScript ビルド → DB チェック → マイグレーション →
管理者の初期作成を順に実行します。Web サーバーの起動は別途必要です。
再実行時は TypeScript の監視タスクを先に停止してください。

管理者を自動作成する場合は、`.env` または実行環境の環境変数に次の両方を設定します。

```dotenv
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=ここに自分で決めたパスワードを設定
```

Django の設定読み込み時に `.env` を読み込みます。すでに設定された環境変数が優先されます。
Compose によってコンテナへ渡された値を変更する場合は、コンテナの再作成が必要です。
`.env` は Git 管理対象外です。実際のパスワードを `.env.example` に記入しないでください。

管理者の作成だけを実行することもできます。

```sh
python manage.py ensure_superuser
```

両方未設定ならスキップし、片方だけ設定されている場合はエラーにします。
同名の有効な管理者が存在する場合は何も変更しません。通常ユーザーや無効な管理者が
同名で存在する場合はエラーにし、自動で権限や有効状態を変更しません。
パスワードはハッシュ化して保存し、既存ユーザーのパスワードは更新しません。
対話形式で作成したい場合は従来の `python manage.py createsuperuser` も使用できます。

デプロイ環境でも、マイグレーション後・Web サーバー起動前に
`python manage.py ensure_superuser` を実行することで同じ処理を利用できます。


## 開発用DBの設定と確認

`.env` の以下の値を使用します。実際のパスワードは `.env.example` に書き込まないでください。

|変数|ローカル開発の設定|
|---|---|
|DB_BACKEND|mysql|
|DB_HOST|db|
|DB_PORT|3306|
|DB_NAME|testcreator|
|DB_USER|testcreator|
|DB_PASSWORD|各自で設定。空欄不可|
|DB_SSL_CA|空欄（ローカルMySQLはTLSなし）|

DBの選択はDEBUGとは独立しています。必須値が不足する場合やバックエンド・ポートが不正な場合はエラーになり、SQLiteへ自動で切り替わりません。
ComposeはDB_NAME／DB_USER／DB_PASSWORDをMySQLの初期化用変数に渡します。DBコンテナにはOCRキーや管理者パスワードを渡しません。
ホスト側ですでに設定されたDB_*はComposeの.envより優先されます。意図しない接続先が設定されていないか確認してください。
別の環境ファイルを使用する場合はTESTCREATOR_ENV_FILEとComposeの--env-fileを同じファイルに向けます。
Compose入口は `.devcontainer/compose.yml` で、ルートの `compose.yml` をincludeします。
手動でComposeを操作する場合も同じプロジェクト名を使用してください。名前を変えると別の空ボリュームが作られます。

コンテナ内で接続と設定を確認できます。

```sh
python -m unittest TestCreator.test_database -v
python manage.py check --database default
python manage.py migrate --noinput
```

ログイン・日本語データ保存・単語帳／単語の操作を確認するテストは以下です。

```sh
python manage.py test accounts TestCreator --noinput
```

実行ユーザーには `test_<DB_NAME>` の作成・削除権限も必要です。通常のアプリユーザーにはその権限がないため、隔離した検証環境だけで付与してください。
DB停止時はサービスの起動状態を確認し、認証エラー時は.envと既存ボリューム内の認証情報が一致しているか確認してください。
本番データを含むDBにはテストを実行しないでください。

## 関連ドキュメント

本番環境の構築と実行は [本番環境の構築と実行](deployment.md) を参照してください。
