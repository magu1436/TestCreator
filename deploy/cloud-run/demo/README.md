# Cloud Run 公開デモ（Issue #31 Step 1）

対象はプロジェクト `wordtestcreator`、リージョン `asia-northeast1`、サービス `wordtest-demo` に固定します。本番サービス、DB、Secret値は変更しません。既存の [デモ実装](../../../docs/demo.md) と共通Dockerfileを利用します。初期構築のGCP操作はユーザーが実施し、通常更新は承認後のActionsで行います。停止・切り戻し・復旧は[デモ専用runbook](runbook.md)を参照してください。

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

実装済みのOCR上限（Issue #33）・失敗時挙動・監視を実環境で確認し、非公開状態で起動・ログイン・初期サンプル・PDF・実URL/CSRF設定を検証してから公開します。以下は初期構築時にIAM方式で公開する場合の操作例です。現行はInvoker IAMチェック無効化方式で公開済みのため、停止からの復帰でこのIAM追加を再実行せず、[runbook](runbook.md#5-公開停止を解除する)に従って直前の公開方式を保持してください。組織ポリシーで拒否された場合は制限を迂回せず、担当者へ確認してください。

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

## GitHub Actionsによる既存デモサービスの更新（#32）

`.github/workflows/deploy-demo.yml` は `main` へのpush（PRのマージを含む）で起動し、GitHub Environment `demo` の承認後にbuildとdeployを実行します。
既存の `wordtestcreator / asia-northeast1 / wordtest-demo` のimageだけを更新します。
本番 `wordtest`、TiDB、公開設定、環境変数、Secret、CPU・メモリ等は変更しません。
`deploy.ps1` は初期構築用で、再実行時にサービスを非公開へ戻すため、このworkflowでは呼びません。
サービスの初期構築・匿名公開・専用Secretの作成と実行SAへの権限付与は、管理者が別途完了させてください。

GitHub Environment / WIF / IAMは適用済みで、承認後のActionsによるCloud Run更新は[成功run](https://github.com/magu1436/TestCreator/actions/runs/45474860647)で確認済みです。
ユーザーによるログイン・サンプル・単語編集・PDFの確認も完了しています。適用と確認の根拠は[Issue #32の運用記録](https://github.com/magu1436/TestCreator/issues/32#issuecomment-7143034536)を参照してください。
[停止・切り戻し・復旧runbook](runbook.md)は作成済みですが、これらの操作の実環境での実施は未実施です。

### 一度だけ行う設定

**workflowを `main` へ取り込む前に、次のEnvironment保護設定を完了してください。**
YAMLの `environment: demo` だけでは承認を強制できません。Environmentが存在しないと、実行時に保護ルールなしで自動生成されます。

1. リポジトリの **Settings → Environments** で `demo` を作成または開きます。
2. **Required reviewers** を有効にし、リポジトリowner・利用者の `magu1436` を追加して **Save protection rules** で保存します。承認者の設定はこの運用の必須条件です。
3. **Prevent self-review** は無効にします。本人がpushした変更を本人が内容確認して承認する運用なので、有効にすると本人が承認できません。
4. **Allow administrators to bypass configured protection rules** は無効にして保存します。管理者も承認を経由する設定にします。
5. **Deployment branches and tags** で **Selected branches and tags** を選び、Branchの `main` だけを許可します。workflow自身も `push` / `main` の組み合わせだけを許可します。

この承認は、mainへのマージ承認とは別のデプロイ承認です。build・認証・push・Cloud Run更新はすべて `demo` の同じjob内にあり、承認前には実行されません。
Environmentと保護ルールはpublic repositoryでは現行のGitHubプランで利用できます。private repositoryのrequired reviewers等はプランに依存するため、非公開化する場合は承認保護が利用できることを再確認してください。
設定方法・利用条件は[GitHub公式のEnvironment管理手順](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)を参照してください。
以下は再構築・設定確認用です。適用済みの保護設定も、利用時に有効なままであることを確認してください。

Environment `demo` のVariablesへ以下を登録します。サービスアカウントのJSON鍵は登録しません。

| Variable | 内容 |
| --- | --- |
| `WIF_PROVIDER` | デモ専用providerの完全名 `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER` |
| `DEPLOY_SERVICE_ACCOUNT` | デモ更新専用SAのメールアドレス（実行SAや本番デプロイSAを流用しない） |

WIF providerのissuerは `https://token.actions.githubusercontent.com` とし、少なくとも次をmappingします。
`google.subject=assertion.sub`、`attribute.repository_id=assertion.repository_id`、
`attribute.repository_owner_id=assertion.repository_owner_id`、`attribute.workflow_ref=assertion.workflow_ref`、`attribute.event_name=assertion.event_name`。
providerのattribute conditionで、実際の不変なrepository ID・owner ID、`demo` Environment、
`main` 上のこのworkflowだけを許可してください。下記のIDは実値へ置き換えます。

```text
assertion.repository_id == 'REPOSITORY_ID' &&
assertion.repository_owner_id == 'OWNER_ID' &&
assertion.sub == 'repo:magu1436/TestCreator:environment:demo' &&
assertion.workflow_ref == 'magu1436/TestCreator/.github/workflows/deploy-demo.yml@refs/heads/main' &&
assertion.event_name == 'push'
```

`workflow_ref` は通常のworkflowのclaimです。`job_workflow_ref` はreusable workflow用なので使用しません。
GitHub側でOIDC subjectをカスタマイズしている場合（不変IDを含むsubjectを選択した場合を含む）は、
上記 `sub` を実際の `demo` subject完全一致へ変更します。Environmentの照合を省略しないでください。
リポジトリ名・owner名だけの条件では、削除後の名前再取得への対策になりません。
専用SAに対する `roles/iam.workloadIdentityUser` も、このproviderの対象repository IDのprincipalSetだけに限定します。
principalSetは `principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/attribute.repository_id/REPOSITORY_ID` です。`PROJECT_NUMBER` はpoolを所有するプロジェクトの番号を使います。
同じpool内に弱い条件の別providerを混在させないでください。

デプロイSAへの権限は次の単位で付与します。プロジェクト全体のEditor、Owner、Cloud Run Adminは不要です。

| 役割 | 付与対象 |
| --- | --- |
| `roles/artifactregistry.writer` | `asia-northeast1` のArtifact Registry repository `webapps` のみ |
| `roles/run.developer` | 既存Cloud Run service `wordtest-demo` のみ（`wordtest`やプロジェクト全体へ付与しない） |
| `roles/iam.serviceAccountUser`（actAs） | 実行SA `wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com` のみ |

デプロイSAはSecretの値を読みません。Secret AccessorはデプロイSAへ付与せず、既存のデモ実行SAが必要なSecretだけを読める状態にします。
Artifact Registryの上記writerはrepository単位のため `webapps` 内の他イメージにも書き込めます。
workflowはイメージ名を `asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo` に固定しています。
既存のプロジェクト全体の強い権限が継承されている場合は、この一覧だけを追加しても分離できないため、管理者が継承権限も確認してください。

根拠: [GitHubのOIDC claims](https://docs.github.com/en/actions/reference/security/oidc)、
[Google CloudのデプロイパイプラインWIF設定](https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)、
[auth ActionのWIF設定](https://github.com/google-github-actions/auth)。
Actionは公式リリースを確認してcommit SHAで固定しています
（[checkout v6.0.2](https://github.com/actions/checkout/commit/de0fac2e4500dabe0009e67214ff5f5447ce83dd)、
[auth v3.0.0](https://github.com/google-github-actions/auth/commit/7c6bc770dae815cd3e89ee6cdf493a5fab2cc093)、
[setup-gcloud v3.0.1](https://github.com/google-github-actions/setup-gcloud/commit/aa5489c8933f4cc7a4f7d45035b3b1440c9c10db)）。

### 更新の実行

1. 検証済み変更を `main` へマージ、またはpushします。「デモの承認後デプロイ」が起動し、`demo` Environmentの承認待ちになります。手動のRun workflowやref入力は使用しません。
2. `magu1436` がActionsの対象runで **Review deployments** を開き、対象commit SHAと変更内容を確認して `demo` を承認します。承認するとLinux/amd64のbuild、GCP認証、image push、実行用manifestのdigest解決、既存デモサービス更新の順に実行します。
3. 更新後はサービスとrevisionのReady、対象image digest、対象revisionへの100%trafficを検証します。デモ更新は直列実行で、進行中の更新を新規実行がキャンセルすることはありません。
4. Summaryでactor、UTC日時、起動元ref、event名、起動時SHA、解決後SHA、pushした親image digest、実デプロイimage digest、revision、結果、workflow自身のSHA、run URLを確認します。失敗時も取得済み情報を残し、未到達の項目は空になります。
5. 成功後にデモURLでログインと主要操作を確認します。SQLiteの再初期化により既存デモデータがリセットされる点は、初期構築と同じです。

GCP認証前に、起動イベントの `github.sha` を取得済みrepository内のcommitへ解決し、そのSHAを `source/` に別checkoutします。
承認待ちの間にmainへ別のpushがあっても、このrunは起動時のcommitを使います。承認後に最新mainを解決する動作はありません。
制御スクリプトは `main` 上のworkflow自身のSHAを `control/` にcheckoutして実行します。
`source/` 内のデプロイスクリプトは実行せず、`control/` のものを使用します。Docker buildもGCP認証前に `source/` だけをcontextとして実行するため、
その後workspace直下に生成するWIF credential JSONはbuild contextに入りません。checkoutの認証情報も保存しません。
pushにはgcloudのcredential helperを使用します。
pushで得られるdigestは、実行用manifestとattestation等をまとめたOCI indexの場合があります。
Cloud RunはLinux/amd64の実行用manifestを稼働revisionのdigestとして返すため、workflowは親indexのdigestと直接比較しません。
`docker build --platform linux/amd64` で構築後、pushした不変な `イメージ名@親digest` を
[`docker buildx imagetools inspect --raw`](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/)で読み、`resolve-image.ps1` が実行用digestを解決します。
OCI index / Docker manifest listではLinux/amd64の候補を1つだけ選び、unknown/unknownのattestationを除外します。
直接のOCI image manifest / Docker schema2 manifestなら親digestをそのまま使用します。候補なし・複数候補・不正なJSON/schema/digest・未対応の形式はデプロイ前に停止します。
親参照は解決前に記録し、Summaryの `parent_image_digest` と `image_digest` に親参照と実デプロイ参照をそれぞれ残します。
既存の `update.ps1` には解決済みdigestを渡し、稼働revisionとの厳密なdigest一致を引き続き検証します。

更新前に、サービスの存在、専用実行SA、`DEMO_MODE=true`、`DB_*` 不在、Cloud Runが返すサービスURL一覧とhost/CSRF設定、
専用Secretの数値バージョン参照を検証します。Django秘密鍵は `DJANGO_DEMO_SECRET_KEY`、
パスワードは `DEMO_ADMIN_PASSWORD`、OCRは `OPENAI_API_KEY`、または用途ごとに別の `wordtest-demo-` Secretを許可します。
Secret値の取得は行いません。
URL候補は `status.url` と `metadata.annotations["run.googleapis.com/urls"]` のJSON配列から取得します。
[Cloud Runの2形式のサービスURL](https://docs.cloud.google.com/run/docs/triggering/https-request#service_url)のどちらで公開設定されていても、APIが返したURLと一致すれば既存設定を維持して更新します。
注釈がない場合は `status.url` だけを候補にします。単一の `CSRF_TRUSTED_ORIGINS` が候補URLのいずれかと完全一致し、単一の `ALLOWED_HOSTS` が同じURLのホストと完全一致することが必要です。
URLを名前から推測して許可せず、未登録ホスト、ワイルドカード、別サービス、http、不正URL、hostとCSRFの不整合、不正なURL注釈は更新前に拒否します。

image以外の設定を維持するため、更新前のtrafficがlatest revisionへ100%でない場合は拒否します。
切り戻し等で旧revisionへ固定している場合や分割配信の場合は、管理者が配信方針を別途確認する必要があります。
新revision作成後は、サービスとrevisionのReady、対象digestの一致、実際の対象revisionへの100%trafficを確認します。
新イメージの起動失敗・配信先の不一致は失敗となり、後続の変更は行いません。
同digestの再実行で新revisionが作られない場合も、同じ稼働条件を満たせば成功とします。

### ローカルの検証

実GCPを呼ばずに次を実行できます。

```powershell
pwsh -NoProfile -File deploy/cloud-run/demo/resolve-image.Tests.ps1
pwsh -NoProfile -File deploy/cloud-run/demo/resolve-source.Tests.ps1
pwsh -NoProfile -File deploy/cloud-run/demo/update.Tests.ps1
pwsh -NoProfile -File deploy/cloud-run/demo/deploy.Tests.ps1
```

`resolve-image.Tests.ps1` は実際のindexとattestationの組み合わせ、OCI/Dockerの各形式、候補選択失敗、不正入力とActions出力を検証します。
`resolve-source.Tests.ps1` は一時Git repositoryでSHA・annotated tag・不正入力を検証し、
`update.Tests.ps1` はgcloudスタブで正常更新、同digest再実行、失敗後の停止、本番イメージ拒否、
誤った実行SA/DB設定/Secret/URL、固定・分割traffic、起動失敗、digest/traffic不一致を検証します。
workflowの構文は `actionlint .github/workflows/deploy-demo.yml` でも確認してください。
