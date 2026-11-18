# デモアクセス設定

`DEMO_MODE=true` の明示指定時だけデモ表示・SQLite・管理画面の拒否を有効にします。既定は `false` です。値は大文字小文字を区別しません。`DEBUG` やログイン状態からデモモードを推測しません。

| 設定 | 既定 | 用途 |
| --- | --- | --- |
| `DEMO_MODE` | `false` | デモモードの明示的な切替 |
| `DEMO_USERNAME` | `demo` | 共有アカウント名 |
| `DEMO_PASSWORD` | 空 | デモ専用の共有パスワード。デモ起動時に必須 |

本番の管理者パスワード、SECRET_KEY、APIキーを共有パスワードに流用しないでください。ホームとログイン画面に共有資格情報を表示します。共通画面にはデータ共有・予告なしの消失・個人情報と実データの入力禁止を案内します。問題／解答PDFには案内を含めません。

共有アカウントは起動時に作成し、通常のログインフォームを利用します。自動ログインは行いません。既存の同名ユーザーもactive・非staff・非superuserに揃え、グループと個別権限を削除します。設定パスワードの変更は次回起動時に反映し、変更がなければハッシュを維持します。デモでは既存のstaff・superuserセッションを含め、`/admin` と `/admin/` 以下を全HTTPメソッドで拒否します。通常モードの管理権限は従来どおりです。

## 対応する操作

[公開デモ仕様書（正本）](https://docs.google.com/document/d/1ZziDbjLtnwCEcHECjoDa0XChiCCFmQQpeR4HQblHsH4/edit)と[Issue #28](https://github.com/magu1436/TestCreator/issues/28)に基づき、単語帳の一覧・閲覧・作成・削除、配下の単語の追加・更新・削除、OCR、プレビュー、問題／解答PDFの生成を既存フローで扱います。

ここでいう単語帳の編集は、配下の単語の編集を指します。単語帳名変更機能の新設はIssue #28の対象外です。

## DBと起動時初期化

`DEMO_MODE=true` の場合は、`DB_*` によるMySQL/TiDB設定や証明書を参照せず、コンテナの一時ディレクトリの `testcreator-demo.sqlite3`（標準のLinuxイメージでは `/tmp/testcreator-demo.sqlite3`）を利用します。DBパスを外部の永続DBに切り替える環境変数は設けていません。コンテナ内の書き込み可能な領域を確保してください。

起動順序は設定検証 → `migrate --noinput` → `initialize_runtime`（デモでは `ensure_demo_user` → `seed_demo`）→ Gunicornです。分岐は `.env` と派生設定を反映したDjangoの `DEMO_MODE` に従います。DB選択後、`HomeConfig.ready()` が全DBのSQLite指定と共有資格情報をDB操作前に検証します。派生設定でも検証を無効にしないでください。初期化で失敗すると起動処理を停止し、Webサーバーを開始しません。非デモ時は従来のMySQL/TiDB選択と `ensure_superuser` を維持し、デモ専用コマンドはDB操作前に拒否します。

DB不要の `collectstatic` だけはこの検証を除外し、共有資格情報なしでdummy DB経路を利用します。

`seed_demo` は既存 `scripts/seed_words.py` の50語を暫定サンプルとして利用します。投入と完了記録を同一トランザクションで保存し、同じDBで再実行しても重複作成せず、利用者が編集・削除した単語や単語帳を復元しません。公開向けの内容整備と適合性確認は[Issue #30](https://github.com/magu1436/TestCreator/issues/30)の残作業です。既存の開発用seedスクリプトの実行方法・挙動は変更していません。

単語のCRUD、セッション、`APICostLog` は同じSQLiteに保存します。共有ユーザーのため、利用者ごとのデータ分離や単語数制限は設けません。コンテナの再作成でSQLiteが失われると、セッション・編集・ログも失われ、次回起動時に初期データへ戻ります。独立したインスタンスやリビジョン間でDBを共有しません。最大インスタンス数を1にしても、リビジョン切替等を含めた単一状態は保証できません。定期リセットも保証しません。公開先への設定反映はIssue #31、実環境の再初期化確認はIssue #34で扱います。

## 隔離された検証

`python manage.py test --settings=TestCreator.demo_test_settings --noinput` はテスト専用の一時SQLiteとテスト内ユーザーを利用します。ファイルDBの初期化テストは独立した一時ファイルでマイグレーション・ユーザー作成・サンプル投入を実行し、同じファイルでの再実行と別ファイルへの初期化を確認します。

統合テストはCSRF検証を有効にして通常ログイン、単語帳・単語操作、OCR、プレビュー、実WeasyPrintによる日本語PDFを確認します。OCRは外部API応答境界だけを置換するため実API料金は発生しません。既存のOCR戻り値 `cost=None` と保存する `estimated_cost` の不整合はIssue #33で扱います。公開環境の実OCRや再初期化の確認はIssue #34の範囲です。
