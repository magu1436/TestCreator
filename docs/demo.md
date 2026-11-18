# デモアクセス設定

`DEMO_MODE=true` の明示指定時だけデモ表示・SQLite・管理画面の拒否を有効にします。既定は `false` です。値は大文字小文字を区別しません。`DEBUG` やログイン状態からデモモードを推測しません。

| 設定 | 既定 | 用途 |
| --- | --- | --- |
| `DEMO_MODE` | `false` | デモモードの明示的な切替 |
| `DEMO_USERNAME` | `demo` | 共有アカウント名 |
| `DEMO_PASSWORD` | 空 | デモ専用の共有パスワード。デモ起動時に必須 |

本番の管理者パスワード、SECRET_KEY、APIキーを共有パスワードに流用しないでください。ホームとログイン画面に共有資格情報を表示します。共通画面にはデータ共有・予告なしの消失・個人情報と実データの入力禁止を案内します。問題／解答PDFには案内を含めません。

`DEMO_USERNAME` は前後の空白がなく、UnicodeのNFKC正規化済みで、既存ログインフォームの入力制約（最大150文字、NULL文字不可）を満たす値を指定してください。ログインフォームがユーザー名の空白除去とNFKC正規化を行うため、` demo ` や全角英数字の `ｄｅｍｏ` はDB操作前に構成エラーにします。設定値の自動変換は行いません。`collectstatic` は共有資格情報の検証を除外します。

共有アカウントは起動時に作成し、通常のログインフォームを利用します。自動ログインは行いません。既存の同名ユーザーもactive・非staff・非superuserに揃え、グループと個別権限を削除します。設定パスワードの変更は次回起動時に反映し、変更がなければハッシュを維持します。デモでは既存のstaff・superuserセッションを含め、`/admin` と `/admin/` 以下を全HTTPメソッドで拒否します。通常モードの管理権限は従来どおりです。

## 対応する操作

[公開デモ仕様書（正本）](https://docs.google.com/document/d/1ZziDbjLtnwCEcHECjoDa0XChiCCFmQQpeR4HQblHsH4/edit)と[Issue #28](https://github.com/magu1436/TestCreator/issues/28)に基づき、単語帳の一覧・閲覧・作成・削除、配下の単語の追加・更新・削除、OCR、プレビュー、問題／解答PDFの生成を既存フローで扱います。

ここでいう単語帳の編集は、配下の単語の編集を指します。単語帳名変更機能の新設はIssue #28の対象外です。

## DBと起動時初期化

`DEMO_MODE=true` の場合は、`DB_*` によるMySQL/TiDB設定や証明書を参照せず、コンテナの一時ディレクトリの `testcreator-demo.sqlite3`（標準のLinuxイメージでは `/tmp/testcreator-demo.sqlite3`）を利用します。DBパスを外部の永続DBに切り替える環境変数は設けていません。コンテナ内の書き込み可能な領域を確保してください。

起動順序は設定検証 → `migrate --noinput` → `initialize_runtime`（デモでは `ensure_demo_user` → `seed_demo`）→ Gunicornです。分岐は `.env` と派生設定を反映したDjangoの `DEMO_MODE` に従います。DB選択後、`HomeConfig.ready()` が全DBのSQLite指定と共有資格情報をDB操作前に検証します。派生設定でも検証を無効にしないでください。初期化で失敗すると起動処理を停止し、Webサーバーを開始しません。非デモ時は従来のMySQL/TiDB選択と `ensure_superuser` を維持し、デモ専用コマンドはDB操作前に拒否します。

デモ専用の `demo.apps.DemoConfig` は `DEMO_MODE=true` の場合だけ登録し、初回投入記録 `demo.DemoInitialization`（`demo_demoinitialization` テーブル）とそのマイグレーションだけを管理します。通常モードには専用モデル・テーブル・マイグレーション・ContentType・権限を追加しません。`seed_demo` は引き続き `accounts` に配置し、モード検証後に専用モデルを取得します。

派生設定で `DEMO_MODE` を上書きする場合は `INSTALLED_APPS` の `demo.apps.DemoConfig` 登録と `DATABASES` も揃えて選択し直してください。`HomeConfig.ready()` は最終モードと実際のアプリ登録が一致しない場合、DB操作前に構成エラーにします。通常モードで予約済みのデモSQLiteパスを残した場合も、DB操作前に拒否します。`.env` よりプロセス環境変数を優先します。

DB不要の `collectstatic` はSQLiteと共有資格情報の検証だけを除外し、共有資格情報なしでdummy DB経路を利用します。モードと専用アプリ登録の整合検証は実施します。

旧 `home.DemoInitialization` を使う未公開版のデモDBは、データ移行せず一時DBを作り直して確認します。旧DBの編集内容は引き継ぎません。通常環境の既存DBに対する専用テーブルの自動削除や、マイグレーションの巻き戻しは行いません。

`seed_demo` は公開デモ専用の [`demo/data/samples.json`](../demo/data/samples.json) から「デモ英単語50」（1〜50番）と「デモ古文単語20」（1〜20番）の2冊70語を投入します。一般的な語彙を選び、語義はこのデモのために短く自作しています。[原稿の由来と公開方針](../demo/data/README.md)も参照してください。実利用者のデータやOCR履歴、本番DBには依存しません。既存の開発用 `scripts/seed_words.py` は変更していません。

投入と完了記録 `initial-samples` を同一トランザクションで保存します。同じDBで再実行しても重複作成せず、利用者の編集・削除を維持します。単語帳と単語を全削除した場合も復元しません。原稿を変更しただけでは、投入済みDBは更新されません。2冊目の投入途中で失敗した場合は、1冊目と完了記録もロールバックします。空の新しいSQLiteへマイグレーションと初期化を実行した場合は、2冊70語の初期状態を再生成します。

単語のCRUD、セッション、`APICostLog` は同じSQLiteに保存します。共有ユーザーのため、利用者ごとのデータ分離や単語数制限は設けません。コンテナの再作成でSQLiteが失われると、セッション・編集・ログも失われ、次回起動時に初期データへ戻ります。独立したインスタンスやリビジョン間でDBを共有しません。最大インスタンス数を1にしても、リビジョン切替等を含めた単一状態は保証できません。定期リセットも保証しません。公開先への設定反映はIssue #31、実環境の再初期化確認はIssue #34で扱います。

## 隔離された検証

`python manage.py test --settings=TestCreator.demo_test_settings --noinput` はテスト専用の一時SQLiteとテスト内ユーザーを利用します。ファイルDBの初期化テストは独立した一時ファイルでマイグレーション・ユーザー作成・サンプル投入を実行し、同じファイルでの再実行と別ファイルへの初期化を確認します。

統合テストはCSRF検証を有効にして通常ログイン、単語帳・単語操作、OCR、プレビュー、実WeasyPrintによる日本語PDFを確認します。OCRは外部API応答境界だけを置換するため実API料金は発生しません。既存のOCR戻り値 `cost=None` と保存する `estimated_cost` の不整合はIssue #33で扱います。公開環境の実OCRや再初期化の確認はIssue #34の範囲です。

日本語フォントとPDF用ネイティブライブラリを含むリポジトリのDockerfileで、以下のように検証できます。リポジトリのルートで実行してください。本番のDB設定・資格情報・APIキーは不要です。指定したダミー値はプロセス環境変数として `.env` より優先します。

```sh
docker build -t testcreator:demo-verification .
docker run --rm --env OPENAI_API_KEY=test-only --env DEMO_MODE=true \
  --env DEMO_PASSWORD=test-demo-password testcreator:demo-verification \
  python manage.py test --settings=TestCreator.demo_test_settings --noinput
```

同一ファイル維持と新しい空ファイルへの復元だけを確認する場合は、末尾のテストコマンドを次に置き換えます。

```sh
python manage.py test TestCreator.test_demo_initialization.DemoFileDatabaseTests \
  --settings=TestCreator.demo_test_settings --noinput
```

このテストは一時ディレクトリ内の `first.sqlite3` で `migrate` → `initialize_runtime` を実行し、70語から1語編集・1語削除後に再初期化して69語と編集内容が維持されることを確認します。次に別の空の `second.sqlite3` で2冊70語が再生成され、セッションとOCRログが空であることを確認します。テスト終了時に一時ファイルを片付け、既存DBは削除しません。実インスタンスの定期リセットやCloud Run再生成の保証ではありません。

## サンプルで体験する

ログイン後、2冊の切替と単語の編集・追加・削除を試せます。出題設定では英語帳の範囲1〜10番から11〜20番へ移動し、番号順またはランダム10問、単語→意味・意味→単語の両方向、プレビューと問題／解答PDFを確認できます。古文帳も同じ操作に対応します。

OCRには[練習画像の取得・利用手順](demo-samples/README.md)を利用してください。初期英語帳と番号が重ならない51〜60番の10語をJPEGで用意しています。画像をリポジトリから保存して既存OCR画面へアップロードし、結果を確認・編集して英語帳へ追記します。素材の取得先は共有ログインID・パスワードとともにデモ紹介時に案内します。

画像の原稿は同じJSONの `ocr_samples` です。生成CLIと日本語フォントの指定例は[素材README](demo-samples/README.md#原稿と再生成)にあります。Pillowで作成したJPEGをGit管理しており、Web起動時の生成は不要です。

自動テストでは共有アカウントの別セッションへの編集反映、範囲内のランダム10問（重複なし）、2冊と両方向のプレビュー・実PDF、画像の生成、OCR応答の確認・編集・保存を検証します。別セッションの共有は同一インスタンスのDB内での動作です。独立インスタンス間の共有は保証しません。実APIによる画像認識精度、公開先での操作・再生成はIssue #34で確認し、GitHub上の画像取得は素材のpush後に最終確認します。
