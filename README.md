# WordTestCreator

## 概要
WordTestCreator は、塾講師が中高生向けの小テストを効率よく作成するための Web アプリケーションです。登録済みの単語帳から出題範囲や出題数を指定すると、英単語や古文単語などの単語テストを自動生成し、印刷しやすい PDF 形式で出力できます。

単語帳の内容はデータベースで管理されるため、講師は毎回問題を手作業で作り直す必要がありません。授業や宿題に合わせて範囲を指定するだけで、ランダム出題や番号順出題、出題方向の切り替えを行いながら、解答付きのテストをすばやく用意できます。

また、管理者は単語帳や単語データを編集でき、画像アップロードと OpenAI API を用いた OCR によって、紙面や画像から単語情報を登録する作業も補助できます。

## 主な機能
- 単語テストの作成
    - 単語帳を選択し、出題範囲と出題数を指定
    - 複数範囲を組み合わせた出題に対応
    - 「単語 → 意味」と「意味 → 単語」の出題形式を切り替え
    - ランダム順または番号順での出題を選択
    - 解答付き PDF を生成
- 単語帳・単語データの閲覧
    - データベースに登録された単語帳の一覧を確認
    - 単語帳ごとの単語番号、語、意味を確認
- 単語帳・単語データの管理
    - 管理者ユーザーによる単語の追加・編集・削除
    - 編集者情報の記録
- OCR による単語登録補助
    - 画像をアップロードして単語情報を抽出
    - OpenAI API を用いた OCR 結果を確認・修正して保存

## スクリーンショット
### ホーム画面
![ホーム画面](docs/images/home.png)
### テスト作成画面
![テスト作成画面](docs/images/create-test.png)
### 作成されたテスト
![単語テスト](docs/images/word-test.png)
[実際に作成された単語テストのPDFファイルはこちら](docs/sample/word-test.pdf)
### 単語帳編集画面
![単語帳編集画面](docs/images/edit-wordbank.png)
### 写真から単語帳を登録する画面
![OCR登録画面](docs/images/registered-by-ocr.png)

## 使用技術
- バックエンド
    - Python
    - Django 5.2.4
    - Django Template
    - Django 認証機能（カスタム管理者ユーザー）
- フロントエンド
    - HTML / CSS
    - TypeScript
    - Bootstrap 5.3
    - Bootstrap Icons
- PDF 生成
    - WeasyPrint 66.0
    - HTML / CSS で作成したテスト画面を PDF に変換
- OCR / 外部 API
    - OpenAI API
    - OpenAI Python SDK
    - 画像アップロードした単語帳から単語番号・語・意味を抽出
- データベース
    - MySQL（ローカル開発環境）
    - TiDB（デプロイ環境）
- 開発・ビルド
    - npm
    - TypeScript Compiler
    - tsc-alias
    - python-dotenv
- デプロイ・運用
    - GCP（Google Cloud Platform）
    - Django static / media ファイル管理

## アーキテクチャ
WordTestCreator は Django プロジェクトを中心に、機能ごとにアプリケーションを分割した構成になっています。画面表示は Django Template で行い、単語帳編集やテスト生成などの画面内操作は TypeScript で実装したフロントエンドから Django の各ビューへリクエストを送る形で処理しています。

### アプリケーション構成
- `home`
    - ホーム画面を担当
    - テスト作成、単語帳閲覧、単語帳編集、ログイン画面への導線を提供
- `accounts`
    - 管理者ユーザーの認証を担当
    - Django の認証機能をベースに、ユーザー名とパスワードでログインするカスタムユーザー `AdminUser` を管理
- `wordbank`
    - 単語帳 `WordList` の作成・削除・取得を担当
    - フロントエンドから単語帳一覧を取得するためのエンドポイントも提供
- `vocab`
    - 単語 `Word` の閲覧・追加・編集・削除を担当
    - 単語帳ごとの単語一覧表示と、管理者向けの編集画面を提供
- `ocr`
    - 画像アップロードと OpenAI API を用いた OCR 処理を担当
    - 抽出した単語情報を画面上で確認・修正できる形で返す
- `quiz`
    - テスト作成条件の入力、プレビュー、PDF 生成を担当
    - 指定された単語帳・範囲・出題形式をもとに問題データを作成し、WeasyPrint で PDF に変換

### データ構成
- `AdminUser`
    - 管理者ユーザーを表すカスタムユーザーモデル
    - 単語帳作成者や単語の最終編集者として記録される
- `WordList`
    - 単語帳を表すモデル
    - 単語帳名、作成者、作成日時を保持
- `Word`
    - 単語データを表すモデル
    - 単語番号、語、意味、所属単語帳、最終編集者、最終更新日時を保持
    - `WordList` と 1 対多の関係を持つ

### 主な処理の流れ
- テスト作成
    - ユーザーが `quiz` の設定画面で単語帳、範囲、出題数、出題形式を指定
    - `quiz` が `WordList` と `Word` から対象データを取得し、問題用のコンテキストを生成
    - Django Template で HTML を組み立て、WeasyPrint で PDF に変換
    - 生成された PDF をブラウザで表示またはダウンロード
- 単語帳編集
    - 管理者ユーザーが `vocab` の編集画面から単語を追加・編集・削除
    - フロントエンドは編集結果を画面に反映し、Django 側へ非同期に保存リクエストを送信
    - 保存時にログイン中のユーザーが最終編集者として記録される
- OCR 登録
    - 管理者ユーザーが `ocr` 画面で単語帳画像をアップロード
    - `ocr` が OpenAI API に画像を送信し、単語番号・語・意味を JSON として抽出
    - 抽出結果を画面で確認・修正したうえで、単語データとして保存

## 実装上のポイント
- 編集作業を止めにくい単語帳管理
    - 単語帳には大量の単語を登録・修正するため、編集のたびに画面全体を再読み込みすると作業効率が落ちる
    - 単語の追加・編集・削除は TypeScript 側で画面表示を更新し、Django 側への保存は `fetch` による非同期通信で行う
    - 連続して単語を登録しやすいように、登録後は次の単語番号を自動で入力し、単語・意味の入力欄だけをリセットする
- OCR による単語登録の補助
    - 単語帳の内容をすべて手入力すると時間がかかり、入力ミスも起こりやすい
    - OpenAI API に画像を送信し、単語番号・語・意味を JSON として抽出することで、紙面や画像からの登録作業を短縮している
    - OCR 結果はそのまま保存せず、画面上で確認・修正してから単語データとして登録できる流れにしている
    - API のリクエストID、使用モデル、推定費用、利用者を記録し、OCR 利用状況をあとから確認できるようにしている
- 権限管理と編集履歴
    - 単語データの誤編集・誤削除は影響が大きいため、単語帳や単語の編集はログイン済みの管理者ユーザーに限定している
    - Django の認証機能をベースに、管理用のカスタムユーザーモデル `AdminUser` を定義している
    - 単語を編集した際は、ログイン中のユーザーを最終編集者として保存し、誰が最後に更新したかを追跡できるようにしている
- 柔軟なテスト生成
    - 複数の出題範囲を指定できるようにし、Django の `Q` オブジェクトで範囲条件をまとめて検索している
    - 「単語 → 意味」と「意味 → 単語」の切り替えは、PDF 生成前のコンテキスト作成時に問題文と解答を入れ替えることで実現している
    - ランダム出題と番号順出題を選べるようにし、授業内容や確認テストの用途に合わせて使い分けられるようにしている
- HTML / CSS ベースの PDF 生成
    - テスト用の HTML を Django Template で作成し、それを WeasyPrint で PDF に変換している
    - Web 画面と同じ HTML / CSS の考え方でレイアウトを調整できるため、問題用紙の見た目を管理しやすい
    - 生成した PDF はブラウザでそのまま表示できるようにし、印刷までの手順を少なくしている

## セットアップ
### DevContainer での開発

Docker Desktop（Linux コンテナ）と VS Code の Dev Containers 拡張機能を使用します。

1. `.env.example` を `.env` にコピーします。既存の `.env` がある場合は MySQL の項目を追記します。
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

### 環境セットアップと管理者の初期作成

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

### 開発用データベース

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

### OCR 機能を使う場合
OpenAI API を利用するため、API キーを環境変数に設定する。デプロイ環境では `OPENAI_API_KEY` を使用する。

現在の `main` ブランチのローカル設定では `settings.py` が `API_KEY` を参照しているため、ローカルで OCR を動かす場合は `API_KEY` にも同じ値を設定する。

```env
OPENAI_API_KEY=sk-...
API_KEY=sk-...
```

### デプロイ
GCP などにコンテナとしてデプロイする場合は、`deploy` ブランチを利用する。`deploy` ブランチには `Dockerfile`、`.dockerignore`、`entrypoint.sh` が含まれており、起動時に次の処理を行う構成になっている。

- `python manage.py migrate --noinput` によるマイグレーション
- `DJANGO_SUPERUSER_USERNAME` と `DJANGO_SUPERUSER_PASSWORD` が設定されている場合のスーパーユーザー作成
- Gunicorn による Django アプリケーションの起動
- WhiteNoise による static ファイル配信

デプロイ時は、下記の環境変数を実行環境に設定する。

## 環境変数
|環境変数名|概要|
|:---:|:---|
|TIDB_ENABLE|TiDB を使用するかどうかを切り替えるためのフラグ|
|TIDB_NAME|接続先 TiDB のデータベース名|
|TIDB_USER|TiDB に接続するユーザー名|
|TIDB_HOST|TiDB のホスト名|
|TIDB_PORT|TiDB のポート番号。未指定の場合は `4000` を想定|
|ALLOWED_HOSTS|Django がリクエストを許可するホスト名。複数指定する場合はカンマ区切り|
|CSRF_TRUSTED_ORIGINS|Django の CSRF 検証で信頼するオリジン。複数指定する場合はカンマ区切り|
|DJANGO_SUPERUSER_USERNAME|起動時に作成するスーパーユーザーのユーザー名|
|TIDB_SSL_CA|TiDB への SSL 接続で使用する CA 証明書ファイルのパス|
|DJANGO_DEBUG|Django をデバッグモードで動作させるかどうか。`true` の場合に有効|
|DJANGO_SECRET_KEY|Django の署名や暗号化に使用するシークレットキー|
|TIDB_PASSWORD|TiDB に接続するユーザーのパスワード|
|OPENAI_API_KEY|OCR 機能で使用する OpenAI API キー|
|DJANGO_SUPERUSER_PASSWORD|起動時に作成するスーパーユーザーのパスワード|

## 今後の改善予定
- 単語データ閲覧機能の改善
    - 登録済みの単語が増えると目的の単語を探しにくくなるため、単語帳閲覧画面に検索機能を追加する
    - 単語番号、語、意味を条件に絞り込めるようにし、データ確認の手間を減らす
- ログイン画面・管理画面の整理
    - 現在のログイン画面を見直し、管理者向けの導線や表示を分かりやすくする
    - スーパー管理者が管理者ユーザーを作成・管理できる画面を実装する
    - 現状は Django 標準の管理サイトで代替している管理操作を、アプリ内で扱いやすくする
- フロントエンド構成の見直し
    - 現在は Django Template と TypeScript を組み合わせて画面ごとの処理を実装している
    - 将来的には React などのフロントエンドフレームワークを導入し、状態管理やコンポーネント分割の見通しを良くする
- 単語登録作業の効率化
    - 手動登録や OCR 登録後の修正作業にかかる時間をさらに短縮する
    - 連続入力、入力補助、OCR 結果の確認 UI を改善し、大量の単語を登録しやすくする
- PDF レイアウトの安定化
    - 生成された単語テストで、単語や意味が長い場合にレイアウトが崩れることがある
    - 改ページ、カラム分割、文字サイズ、余白の調整を行い、印刷時に読みやすい PDF を安定して出力できるようにする
