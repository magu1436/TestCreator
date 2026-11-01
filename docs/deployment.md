# 本番環境の構築と実行

このリポジトリから本番用コンテナを構築するための手順です。開発環境は [DevContainerでの環境構築](devcontainer.md) を参照してください。

## ビルド

```sh
docker build -t testcreator:production .
```

依存バージョンは `requirements.txt`、OS依存はルートの `Dockerfile` を参照してください。
mysqlclientはビルド用ステージでコンパイルし、実行用ステージには接続ライブラリとCAストアを配置します。
ビルド時の `collectstatic` はDB接続情報なしで実行できます。DB接続不能なdummy backendを使用し、別のDBを作成しません。
`.env` と証明書はイメージに含めず、実行時に渡します。

## 実行環境の設定

|変数|設定内容|
|---|---|
|DJANGO_SETTINGS_MODULE|TestCreator.production（イメージの既定値）|
|DJANGO_SECRET_KEY|実行環境で生成・管理する秘密鍵。必須|
|DJANGO_DEBUG|通常false。省略時false|
|ALLOWED_HOSTS|公開ホスト名のカンマ区切り。必ず対象ホストを指定|
|CSRF_TRUSTED_ORIGINS|必要な公開オリジンをスキーム付きでカンマ区切り|
|DB_BACKEND|mysql または tidb|
|DB_HOST / DB_PORT|接続ホストとポート|
|DB_NAME / DB_USER / DB_PASSWORD|DB名、ユーザー、パスワード|
|DB_SSL_CA|コンテナ内のCAファイルパス。tidbでは必須|
|DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD|初回管理者を自動作成する場合、両方指定|
|OPENAI_API_KEY|OCRを使用する場合のAPIキー。API_KEYも入力可能で、両方ある場合はこちらが優先|
|PORT|HTTP待受ポート。省略時8080|

DB設定はDEBUGと独立しています。必須項目の不足、不正なバックエンド・ポート、存在しないCAはエラーになります。
TLS指定時はCAとホスト名を検証します。CAを指定しないMySQL接続はTLSなしです。
SQLiteや他ドライバーへの自動フォールバックはありません。認証情報の前後空白は保持します。
アプリユーザーには対象DBへのマイグレーションと読み書きに必要な権限を与えてください。

例えば、実際の値をGit管理外の `.env.production` に記入し、証明書を配置してから起動します。
次のコマンドはプロジェクトルートで実行します。証明書の保存先は自分の環境に合わせて変更してください。

```sh
docker run --rm --name testcreator \
  --env-file .env.production \
  --mount "type=bind,source=$(pwd)/certs/db-ca.pem,target=/run/certs/db-ca.pem,readonly" \
  -p 127.0.0.1:8080:8080 \
  testcreator:production
```

上記はPOSIXシェル用です。PowerShellでは行継続記号を変更するか、一行で実行してください。
`DB_SSL_CA=/run/certs/db-ca.pem` と指定します。TLSを使用しないローカルMySQLではマウントを省略できます。
コンテナからDBへ到達可能なネットワークと、公開用のHTTPS／リバースプロキシを別途用意してください。
アップロードデータを保持する場合は `/app/media` の永続ストレージを用意します。

起動順はマイグレーション→管理者初期作成→Gunicornです。既存管理者のパスワードは変更しません。
静的ファイルはimport mapのディレクトリURLを維持する、ハッシュなしのWhiteNoise圧縮ストレージで配信します。
公開前にはクリーンなチェックアウトから生成したJavaScriptがイメージに含まれることと、各画面のJS／CSS配信を確認してください。

## DB接続と操作の確認

本番データを含まない検証用DBに同じ環境変数とCAを設定して実行します。

```sh
python manage.py check --database default
python manage.py migrate --noinput
python manage.py test accounts TestCreator --noinput
```

テスト実行ユーザーには通常のDB権限に加え、`test_<DB_NAME>` の作成・削除権限が必要です。検証環境だけに付与してください。
テストはログイン、日本語保存、単語帳／単語の基本操作と設定の検証を含みます。
TLS接続では `SHOW STATUS LIKE 'Ssl_cipher'` が空でないこと、不正なCAとホスト名不一致で接続が拒否されることも確認します。
