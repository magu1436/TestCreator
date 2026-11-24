# Cloud Run 公開デモ（Issue #31 Step 1）

対象はプロジェクト `wordtestcreator`、リージョン `asia-northeast1`、サービス `wordtest-demo` に固定します。本番サービス、DB、Secret値は変更しません。既存の [デモ実装](../../../docs/demo.md) と共通Dockerfileを利用します。GCP操作はユーザーが実施します。この変更では実環境への適用・公開確認を行いません。

## 設定と前提

PowerShell 7、認証済みGoogle Cloud CLI、Artifact Registryへのビルド・配布権限が必要です。実行者にはCloud Run更新権限、対象サービスの `run.services.getIamPolicy` / `run.services.setIamPolicy`、デモ専用SAへの `iam.serviceAccounts.actAs` が必要です。Secret作成・IAM設定は権限を持つ担当者が下記の対象単位で実施します。スクリプトはSAやSecretを作成せず、対象サービスの公開IAM削除だけを行います。

`environment.example.yaml` はこのデモスクリプトがそのまま使用する非秘密設定です。通常環境向けの親ディレクトリのexampleとは扱いが異なります。秘密値と `DB_*` は書き込まないでください。

| 項目 | 値 |
| --- | --- |
| 実行SA | `wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com` |
| Secret参照 | `DJANGO_DEMO_SECRET_KEY:1` / `DEMO_ADMIN_PASSWORD:1` / `OPENAI_API_KEY:2`（使用前に確認） |
| イメージリポジトリ | `asia-northeast1-docker.pkg.dev/wordtestcreator/webapps` |
| モード | `DEMO_MODE=true` / `DJANGO_DEBUG=false` |
| DB | `/tmp/testcreator-demo.sqlite3`（アプリが選択） |
| 初期化 | migrate → initialize_runtime → Gunicorn |
| PDF | `/tmp/exports` |
| スケール | 最小0、最大1、同時リクエスト1 |
| リソース | CPU 2、メモリ2GiB |
| タイムアウト | Cloud Run 120秒 / Gunicorn 120秒（暫定、実測して調整） |
| OCR | `OCR_DAILY_LIMIT=10`（`ocr/quota.py` と設定で実装済み。実環境での動作・監視は要確認） |

一時SQLiteのため再作成で編集・セッション・OCRログ・利用回数が失われ、OCR上限もリセットされます。OCR回数上限は厳密な課金上限ではありません。最大1でもリビジョン切替等で複数インスタンスが共存でき、厳密な単一DB状態は保証しません。同時リクエスト1も全リビジョンを通じた排他制御ではありません。共有ユーザーに個人情報や実データを入力しないでください。

## 1. 専用SAとSecret（手動）

以下のSAとSecretはユーザーが作成済みです。重複作成は不要です。以下の作成例は再構築時に存在確認のうえ必要な場合だけユーザーが実行します。API有効化やArtifact Registryリポジトリ準備は既存構成を確認し、必要なものだけ行います。

```powershell
gcloud iam service-accounts create wordtestcreator-demo --project=wordtestcreator --display-name='WordTest public demo runtime'
gcloud secrets create DJANGO_DEMO_SECRET_KEY --project=wordtestcreator --replication-policy=automatic
gcloud secrets create DEMO_ADMIN_PASSWORD --project=wordtestcreator --replication-policy=automatic
```

秘密鍵・共有パスワードは新しいデモ専用値を安全な入力手段で生成し、Secret Managerコンソールから各Secretの新バージョンへ登録します。秘密値をコマンド引数、シェル履歴、Git、画面キャプチャに残しません。共有パスワードはデモ画面に表示される前提です。Django秘密鍵やAPIキーは表示しません。

OCRは既存の本番用 `OPENAI_API_KEY` に対応するSecret **ID** と数値バージョンを担当者が確認し、参照だけを共有します。既存Secret IDは `OPENAI_API_KEY` です。値を読み出す必要はなく、本番Secretへの追加・更新・削除は行いません。本番OCRキーと利用枠・課金を共有するため、実装済みのOCR制限と実環境の監視・失敗時挙動を確認するまで匿名公開しません。

```powershell
$demoMember = 'serviceAccount:wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com'
gcloud secrets add-iam-policy-binding DJANGO_DEMO_SECRET_KEY --project=wordtestcreator --member=$demoMember --role=roles/secretmanager.secretAccessor
gcloud secrets add-iam-policy-binding DEMO_ADMIN_PASSWORD --project=wordtestcreator --member=$demoMember --role=roles/secretmanager.secretAccessor
gcloud secrets add-iam-policy-binding OPENAI_API_KEY --project=wordtestcreator --member=$demoMember --role=roles/secretmanager.secretAccessor
```

Secret単位の付与だけを行い、プロジェクト全体のSecret AccessorやEditorは付与しません。実行SAへの不要な既存ロールがないことも確認します。既存本番SecretのIAMへの変更は上記デモSAの参照追加だけです。

## 2. codex/31-cloud-run-demoの固定コミットからイメージを作成

このブランチ `codex/31-cloud-run-demo` のデプロイ対象コミットSHAを記録し、クリーンな別チェックアウトでそのSHAに固定してユーザーがビルドします。`DEPLOY_COMMIT_SHA` をレビュー済みの実SHAへ置き換えます。developへの包含は条件にしません。リポジトリ作成やトリガー変更はこの手順に含めません。

```powershell
git rev-parse codex/31-cloud-run-demo
git merge-base --is-ancestor DEPLOY_COMMIT_SHA codex/31-cloud-run-demo
# 上の終了コードが0のときだけ続行する。
git worktree add --detach ../TestCreator-demo-build DEPLOY_COMMIT_SHA
Set-Location ../TestCreator-demo-build
gcloud builds submit --project=wordtestcreator --tag=asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo:DEPLOY_COMMIT_SHA .
gcloud artifacts docker images describe asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo:DEPLOY_COMMIT_SHA --project=wordtestcreator --format='value(image_summary.digest)'
```

ビルドが成功したことを確認し、得られた `sha256:...` と元コミットを記録します。以下のスクリプトはビルドせず、`asia-northeast1-docker.pkg.dev/wordtestcreator/...@sha256:...` の固定イメージだけを受け入れます。

## 3. 非公開で作成し、実URLを設定

リポジトリルートで実行します。Secretは `ID:数値バージョン`、SAは作成済みの `wordtestcreator-demo` を指定します。互換性のため従来の `wordtest-demo` または `wordtest-demo-` で始まる専用IDも受け入れます。`latest` やプレースホルダーは拒否します。

```powershell
$parameters = @{
    Image = 'asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo@sha256:ACTUAL_DIGEST'
    ServiceAccount = 'wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com'
    DjangoSecret = 'DJANGO_DEMO_SECRET_KEY:1'
    DemoPasswordSecret = 'DEMO_ADMIN_PASSWORD:1'
    OpenAiSecret = 'OPENAI_API_KEY:2'
}
./deploy/cloud-run/demo/deploy.ps1 @parameters -WhatIf
./deploy/cloud-run/demo/deploy.ps1 @parameters
```

SA、Secret ID、Artifact Registryの `webapps` は作成済み構成に合わせています。例のSecretバージョン `1` / `1` / `2` は2026-11-24に確認された非秘密メタデータです。使用直前にユーザーが現在の有効バージョンを確認してください。秘密値は記録しません。`ACTUAL_DIGEST` は対象コミットのビルドで取得した64桁digestへ置き換えてください。`DEMO_ADMIN_PASSWORD` はSecret IDだけで、Djangoには `DEMO_PASSWORD` として渡します。staff権限やsuperuser権限を付与する設定ではありません。`-WhatIf` は入力を検証し、gcloudの探索・呼び出しを一切行いません。通常実行では確認後、`ingress=internal` とInvoker IAMチェック有効でデプロイし、外部からの到達を制限します。`--no-allow-unauthenticated` はIAM削除失敗を警告だけで終える場合があるため、終了コード0だけでは非公開と判断しません。

サービスIAMをJSONで読み、`allUsers` / `allAuthenticatedUsers` を含む無条件bindingをロールごとに独立した削除コマンドで除去します。条件付きの公開bindingは自動変更せず停止します。再取得で公開bindingが残っていないことを確認し、サービスJSONでInvoker IAMチェックが有効（無効化annotationが未設定または文字列 `false`）であることと `status.url` を検証します。最後にそのホストだけを `ALLOWED_HOSTS`、そのHTTPSオリジンだけを `CSRF_TRUSTED_ORIGINS` へ反映し、`ingress=all` に戻します。この時点でも呼び出しにはIAM認証が必要です。

最初のリビジョンは `bootstrap.invalid` を設定して起動し、実URLを推測しません。更新は既存のデモ環境変数を保持します。旧形式・新形式のCloud Run URLに対応します。

各gcloudの非ゼロ終了時には後続処理を停止します。IAMの読込・JSON形式・除去・残存確認やサービス状態の検証に失敗した場合は、`ingress=internal` のまま停止し、完了とは表示しません。最後の更新自体に失敗した場合は実際の状態を確認してください。失敗時は匿名公開せず、設定を確認して再実行してください。スクリプトは実行するたびにInvoker IAMチェックを有効化し、公開principalを外して **非公開に戻します**。実行中の並行IAM変更は避け、プロジェクトから継承した権限などサービスIAM以外に広い呼び出し権限がないことも確認します。Windowsの `gcloud.cmd` に引数配列を渡し、Invoke-Expressionは使用しません。

## 4. 公開は別操作（OCR制限の実環境検証後）

実装済みのOCR上限（Issue #33）・失敗時挙動・監視を実環境で確認し、非公開状態で起動・ログイン・初期サンプル・PDF・実URL/CSRF設定を検証してから公開します。公開を許可する最終操作は次だけです。組織ポリシーで拒否された場合は制限を迂回せず、担当者へ確認してください。

```powershell
gcloud run services add-iam-policy-binding wordtest-demo --project=wordtestcreator --region=asia-northeast1 --member=allUsers --role=roles/run.invoker
```

公開後の受入確認はIssue #34、即時停止・復旧の運用はIssue #32、OCR制限・監視はIssue #33で扱います。この準備だけで公開可とは判断しません。

## 適用時の記録

- 固定したcodex/31-cloud-run-demoのコミット、ビルド結果、イメージdigest。
- プロジェクト・リージョン・サービス名、実URL、反映したホストとCSRFオリジン。
- 非秘密環境変数、CPU・メモリ・インスタンス・同時実行数・タイムアウト。
- 実行SA、Secret IDと数値バージョン（値は記録しない）、Secret単位のIAM付与と不要権限の確認。
- 非公開確認、Issue #33の完了根拠、匿名公開の実施日時と承認、Issue #34の受入結果。

## ローカル検証

PowerShell 7で実行します。Windowsのネイティブ引数テストはNode.jsも必要です。Pester、gcloud、GCP資格情報は不要です。テストは外部コマンドの境界だけをスタブ化し、実クラウドへアクセスしません。

```powershell
pwsh -NoProfile -File deploy/cloud-run/demo/deploy.Tests.ps1
```

WhatIfの無呼び出し、対象固定、入力拒否、実URLの反映、リソース/Secret引数、各段階の失敗停止、deploy成功後の公開IAM残存・除去失敗・不正JSON・条件付きbindingでの停止、Invoker IAMチェック状態の検証と、Windows `.cmd` 経由の空白付きパス・カンマを検証します。

公式仕様: [Cloud Run HTTPS URL](https://docs.cloud.google.com/run/docs/triggering/https-request)、[gcloud run deploy](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)、[Secret設定](https://docs.cloud.google.com/run/docs/configuring/services/secrets)。
