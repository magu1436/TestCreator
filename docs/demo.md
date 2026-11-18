# デモアクセス設定

`DEMO_MODE=true` の明示指定時だけデモ表示と管理画面の拒否を有効にします。既定は `false` です。`DEBUG` やログイン状態からデモモードを推測しません。

| 設定 | 既定 | 用途 |
| --- | --- | --- |
| `DEMO_MODE` | `false` | デモモードの明示的な切替 |
| `DEMO_USERNAME` | `demo` | 共有アカウント名 |
| `DEMO_PASSWORD` | 空 | デモ専用の共有パスワード。デモ起動時に必須 |

本番の管理者パスワード、SECRET_KEY、APIキーを共有パスワードに流用しないでください。ホームとログイン画面に共有資格情報を表示します。共通画面にはデータ共有・予告なしの消失・個人情報と実データの入力禁止を案内します。問題／解答PDFには案内を含めません。

共有アカウントは通常のログインフォームを利用します。自動ログインやユーザーの自動作成は行いません。デモでは既存のstaff・superuserセッションを含め、`/admin` と `/admin/` 以下を全HTTPメソッドで拒否します。通常モードの管理権限は従来どおりです。

## 対応する操作

[公開デモ仕様書（正本）](https://docs.google.com/document/d/1ZziDbjLtnwCEcHECjoDa0XChiCCFmQQpeR4HQblHsH4/edit)と[Issue #28](https://github.com/magu1436/TestCreator/issues/28)に基づき、単語帳の一覧・閲覧・作成・削除、配下の単語の追加・更新・削除、OCR、プレビュー、問題／解答PDFの生成を既存フローで扱います。

ここでいう単語帳の編集は、配下の単語の編集を指します。単語帳名変更機能の新設はIssue #28の対象外です。

## OCR利用上限

デモでは `OCR_DAILY_LIMIT` が未設定のとき、OCRを全利用者の合計で1日10回までに制限します。上限の設定、回数の数え方、SQLite再生成による利用回数のリセット、ログの確認、デモだけを止める手順は[OCR利用上限と公開デモの運用](ocr-usage-limit.md)を参照してください。

## 後続のDB・初期化実装との契約

Issue #28はDB選択や初期化を追加しません。Issue #29で最終的な `DATABASES` をSQLiteに設定し、同じ `DEMO_USERNAME` / `DEMO_PASSWORD` でactive・非staff・非superuserの共有ユーザーを準備します。DB選択の完了後、`HomeConfig.ready()` が全DBのSQLite指定と共有資格情報を検証します。`migrate` を含むコマンドのDB操作前に不正な構成を拒否します。派生設定を利用する場合も、この検証を無効にしないでください。

DB不要の `collectstatic` だけはこの検証を除外し、既存のdummy DB経路を利用します。通常のMySQL/TiDB設定のままデモをONにして起動することはできません。#29導入前は公開デモとして起動・公開しないでください。

## 隔離された検証

`python manage.py test --settings=TestCreator.demo_test_settings --noinput` はテスト専用の一時SQLiteとテスト内ユーザーを利用します。この設定は本番のSQLite選択や起動時ユーザー生成を実装するものではありません。

統合テストはCSRF検証を有効にして通常ログイン、単語帳・単語操作、OCR、プレビュー、実WeasyPrintによる日本語PDFを確認します。OCRは外部API応答境界だけを置換するため実API料金は発生しません。公開環境の実OCRや再初期化の確認はIssue #34の範囲です。
