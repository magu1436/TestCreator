# 公開デモの停止・切り戻し・復旧

対象は `wordtestcreator / asia-northeast1 / wordtest-demo` のみです。本番 `wordtest`、TiDB、Secret値・バージョン・IAM、実行SA、環境変数は変更しません。通常更新は[README](README.md#更新の実行)を参照してください。`deploy.ps1` は初期構築用のため復旧には使いません。

通常デプロイとログイン・サンプル・単語編集・PDFの確認は実施済みです。根拠は[Issue #32の運用記録](https://github.com/magu1436/TestCreator/issues/32#issuecomment-7143034536)と[成功したActions run](https://github.com/magu1436/TestCreator/actions/runs/45474860647)を参照してください。**この停止・切り戻し・復旧手順の実環境での実施は未実施です。** 以下はPowerShell 7向けの手順です。各ブロックを順番に、出力と前提を確認して実行します。

## 1. 並行操作を止め、現在の状態を確認

Actionsの新たなデプロイ承認と手動更新を止めます。実行中runはキャンセルして終了を確認するか、完了を待ちます。キャンセル時も既にCloud Runへ変更が届いている可能性があるため、必ず以下で実状態を読みます。承認待ちの古いrunは再承認しません。復旧後は新しいmainのrunで通常更新します。

認証済みの担当者が、次の共通関数を同じPowerShellセッションに読み込みます。終了コード非ゼロ・検証失敗時はそこで停止し、残りをまとめて実行しません。JSONはローカルの変数だけで保持し、定義全体をIssueへ貼らないでください。

```powershell
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$demoCommon = @('--project=wordtestcreator', '--region=asia-northeast1', '--quiet')
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Invoke-DemoGcloud([string[]]$Arguments) {
    $PSNativeCommandUseErrorActionPreference = $false
    $result = & gcloud @Arguments @demoCommon
    if ($LASTEXITCODE -ne 0) { throw "gcloud失敗: $LASTEXITCODE。状態を再確認してください。" }
    return $result
}
function Read-DemoService {
    $value = (Invoke-DemoGcloud @('run','services','describe','wordtest-demo','--format=json') | Out-String) | ConvertFrom-Json -AsHashtable
    Require ($value.metadata.name -ceq 'wordtest-demo') '対象サービスが異なります。'
    Require ($value.spec.template.spec.serviceAccountName -ceq 'wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com') '実行SAが異なります。'
    return $value
}
function Read-DemoRevision([string]$Revision) {
    Require ($Revision -cmatch '\Awordtest-demo-[a-z0-9-]+\z') '実在するデモrevision名が必要です。'
    $value = (Invoke-DemoGcloud @('run','revisions','describe',$Revision,'--format=json') | Out-String) | ConvertFrom-Json -AsHashtable
    Require ($value.metadata.name -ceq $Revision -and $value.metadata.labels['serving.knative.dev/service'] -ceq 'wordtest-demo') '別サービスのrevisionです。'
    return $value
}
function Assert-ReadyImage($Revision, [string]$Image) {
    Require ($Image -cmatch '\Aasia-northeast1-docker\.pkg\.dev/wordtestcreator/webapps/wordtest-demo@sha256:[a-f0-9]{64}\z') '既知正常のデモ用固定digestが必要です。'
    Require (@($Revision.status.conditions | Where-Object { $_.type -ceq 'Ready' -and $_.status -ceq 'True' }).Count -eq 1) 'revisionがReadyではありません。'
    Require ($Revision.spec.containers.Count -eq 1 -and $Revision.spec.containers[0].image -ceq $Image -and $Revision.status.imageDigest -ceq $Image) '稼働image/digestが記録と一致しません。'
}
function Assert-Traffic($Service, [string]$Revision) {
    $traffic = @($Service.status.traffic | Where-Object { $_.percent -gt 0 })
    Require ($traffic.Count -eq 1 -and $traffic[0].revisionName -ceq $Revision -and $traffic[0].percent -eq 100) '対象revisionへの100%配信ではありません。'
}
function Read-DemoPolicy {
    $policy = (Invoke-DemoGcloud @('run','services','get-iam-policy','wordtest-demo','--format=json') | Out-String) | ConvertFrom-Json -AsHashtable
    if (-not $policy.Contains('bindings')) { $policy['bindings'] = @() }
    return $policy
}
function Get-InvokerDisabled($Service) {
    $annotations = $Service.metadata.annotations
    if ($annotations.Contains('run.googleapis.com/invoker-iam-disabled')) { return $annotations['run.googleapis.com/invoker-iam-disabled'] }
    return 'false'
}
$before = Read-DemoService
$originalIngress = $before.metadata.annotations['run.googleapis.com/ingress']
$originalInvokerDisabled = Get-InvokerDisabled $before
$originalPolicy = Read-DemoPolicy
[pscustomobject]@{
    ingress = $originalIngress
    invokerIamDisabled = $originalInvokerDisabled
    latestCreated = $before.status.latestCreatedRevisionName
    latestReady = $before.status.latestReadyRevisionName
    traffic = $before.status.traffic
} | ConvertTo-Json -Depth 5
```

成功/失敗したrunのSummaryのSHA、親index参照、実デプロイ参照、revisionと読み取った実状態を照合します。現在trafficが100%向いているrevisionも `Read-DemoRevision` で読みます。

| 症状 | 判断と次の操作 |
| --- | --- |
| SQLite migrate・サンプル初期化失敗 | 起動ログとReadyを確認。初期化失敗時はWebサーバーを起動しない。旧revisionが配信中かも確認し、必要なら停止・切り戻し。修正済みimageを用意して第4節へ。 |
| revision/サービスがReadyでない | latestCreatedとlatestReady、実trafficを区別する。旧revisionが配信中でも新revisionの成功とは扱わない。 |
| digest不一致でrun失敗 | Readyでも更新済みの場合がある。親indexとLinux/amd64子manifestを区別し、Summaryの実デプロイ参照とrevisionのspec/statusを比較。原因未確定で再実行しない。 |
| run成功後に画面・主要操作が失敗 | 既に新revisionに切り替わっている前提で実trafficを確認し、停止または既知正常revisionへ切り戻す。 |

ログはCloud Runコンソールで `wordtest-demo` と対象revisionに絞って確認します。認証情報や個人データを含むログは公開しません。画像・Secret・環境設定を推測で差し替えないでください。

## 2. 外部公開を止める（必要な場合）

公開状態の記録後、ingressだけをinternalへ変更します。これは外部到達を制限する操作で、インスタンス削除・DBバックアップ・内部経路からの呼び出し停止ではありません。

```powershell
$null = Invoke-DemoGcloud @('run','services','update','wordtest-demo','--ingress=internal')
$stopped = Read-DemoService
Require ($stopped.metadata.annotations['run.googleapis.com/ingress'] -ceq 'internal') '公開停止を確認できません。'
```

外部ブラウザからデモURLに到達できなくなったことも確認します。IAMは変更しません。現行の公開はInvoker IAMチェック無効化方式です。公開復帰のために `allUsers` bindingを追加したり、Secretや本番を変更したりしません。停止だけで終了する場合も、再開責任者と状態をIssueへ記録します。

## 3. 既知正常revisionへ切り戻す

Issueの運用記録と過去の成功runから、実際に主要操作を確認済みのrevisionとLinux/amd64の**子manifest**参照を選びます。最新Readyという理由だけで選びません。プレースホルダーを実値へ置換し、旧revisionの所属・Ready・imageを確認してから切り替えます。

```powershell
$oldRevision = 'REPLACE_WITH_KNOWN_GOOD_REVISION'
$recoveryImage = 'REPLACE_WITH_KNOWN_GOOD_LINUX_AMD64_IMAGE_AT_SHA256'
$old = Read-DemoRevision $oldRevision
Assert-ReadyImage $old $recoveryImage
$null = Invoke-DemoGcloud @('run','services','update-traffic','wordtest-demo',"--to-revisions=$oldRevision=100")
$rolledBack = Read-DemoService
Assert-Traffic $rolledBack $oldRevision
Assert-ReadyImage (Read-DemoRevision $oldRevision) $recoveryImage
```

外部公開中ならログイン、サンプル表示、単語編集、問題/解答PDFを確認します。停止中なら承認済みの内部接続経路で確認します。経路がなければ画面確認は未実施と記録し、公開復帰後に必ず確認します。OCRの追加実行はこの復旧確認に必須ではありません。

切り戻し後のtrafficは旧revisionへ固定されています。`update.ps1` は `latestRevision=true / 100%` 以外を拒否するため、workflowの再実行だけでは通常更新へ戻れません。**壊れたlatestへ無条件に `--to-latest` を実行しないでください。** 次節で正常imageを新たなlatestとして準備します。

## 4. 正常なlatestを作り、通常更新へ復帰

第1節の並行操作停止を維持します。第3節の `$recoveryImage` は既知正常の子manifest参照です。親index参照しかない場合は、[digest解決手順](README.md#更新の実行)と `resolve-image.ps1` で子参照を確定してから続けます。初期化失敗時もまず既知正常imageへ戻します。アプリ修正は通常更新へ復帰後、検証済み変更をmainの新しいrunで適用します。

ここで作成するrevisionは「現在のサービス設定＋正常image」です。旧revisionの設定全体を復元する操作ではありません。実行SA・`DEMO_MODE=true`・DB接続なし・公開host/CSRF・Secret参照が意図どおりであることを、READMEと現在の設定で確認してください。imageが正常でも現在の設定に原因がある場合は、ここで止めて原因を切り分けます。

```powershell
# 一意suffixで新revisionを作る。通常の外部trafficはまだ渡さない。
Assert-ReadyImage (Read-DemoRevision $oldRevision) $recoveryImage
$recoverySuffix = 'recovery-' + [DateTime]::UtcNow.ToString('yyyyMMddHHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
Require ($recoverySuffix -cmatch '\Arecovery-[0-9]{14}-[a-f0-9]{8}\z') '復旧suffixが不正です。'
$recoveryRevision = "wordtest-demo-$recoverySuffix"
$null = Invoke-DemoGcloud @('run','services','update','wordtest-demo',"--image=$recoveryImage","--revision-suffix=$recoverySuffix",'--no-traffic')
$candidateService = Read-DemoService
Require ($candidateService.status.latestCreatedRevisionName -ceq $recoveryRevision -and $candidateService.status.latestReadyRevisionName -ceq $recoveryRevision) '新しい復旧revisionが最新かつReadyではありません。'
Assert-ReadyImage (Read-DemoRevision $recoveryRevision) $recoveryImage
Assert-Traffic $candidateService $oldRevision
# 最新候補が正常と分かってから、候補を指定して100%へ切り替える。
$null = Invoke-DemoGcloud @('run','services','update-traffic','wordtest-demo',"--to-revisions=$recoveryRevision=100")
$recovered = Read-DemoService
Assert-Traffic $recovered $recoveryRevision
Assert-ReadyImage (Read-DemoRevision $recoveryRevision) $recoveryImage
```

`--no-traffic` でもrevisionの起動とSQLite初期化は実行されます。作成・Ready・digest確認のいずれかで失敗したら後続に進まず、実trafficを読み直します。旧revisionへ戻す必要があれば第3節を使います。

候補100%の状態で、接続可能な経路から前節の主要画面・PDFを確認します。確認できない場合は未実施と記録します。画面確認前にlatest追従へ進めません。停止中で内部経路がない場合は第5節で公開復帰し、画面確認を完了してから以下へ戻ります。

```powershell
# 画面確認後も、latestが候補のままであることを再確認する。
$checked = Read-DemoService
Require ($checked.status.latestCreatedRevisionName -ceq $recoveryRevision -and $checked.status.latestReadyRevisionName -ceq $recoveryRevision) '別のlatestが作られています。切替を停止します。'
Assert-Traffic $checked $recoveryRevision
Assert-ReadyImage (Read-DemoRevision $recoveryRevision) $recoveryImage
$null = Invoke-DemoGcloud @('run','services','update-traffic','wordtest-demo','--to-latest')
$following = Read-DemoService
Assert-Traffic $following $recoveryRevision
Require ($following.status.latestCreatedRevisionName -ceq $recoveryRevision -and $following.status.latestReadyRevisionName -ceq $recoveryRevision) 'latestが候補と一致しません。'
$desiredTraffic = @($following.spec.traffic)
Require ($desiredTraffic.Count -eq 1 -and $desiredTraffic[0].latestRevision -eq $true -and $desiredTraffic[0].percent -eq 100) 'latest追従100%へ戻っていません。'
```

古い承認待ちrunを終了し、必要な修正をmainへ取り込んだ新しいrunを、対象SHA確認後に承認します。通常workflowによるReady・実digest・100%traffic確認と主要画面確認まで実施して、復旧完了とします。

## 5. 公開停止を解除する

停止直前の `$originalIngress` が `all` で、公開方式も確認できた場合だけ元へ戻します。PowerShellセッションを失った場合は運用記録から直前値を復元・照合し、推測で `all` を設定しません。第3/4節の配信先・Ready・digestの確認後に実行してください。

```powershell
Require ($originalIngress -ceq 'all') '停止直前がallではありません。公開範囲を拡大しません。'
$beforeReopen = Read-DemoService
Require ((Get-InvokerDisabled $beforeReopen) -ceq $originalInvokerDisabled) '停止直前と公開認証方式が変わっています。'
$currentPolicy = Read-DemoPolicy
Require (($currentPolicy.bindings | ConvertTo-Json -Depth 15 -Compress) -ceq ($originalPolicy.bindings | ConvertTo-Json -Depth 15 -Compress)) '停止直前とIAMが変わっています。'
$null = Invoke-DemoGcloud @('run','services','update','wordtest-demo','--ingress=all')
$reopened = Read-DemoService
Require ($reopened.metadata.annotations['run.googleapis.com/ingress'] -ceq 'all' -and (Get-InvokerDisabled $reopened) -ceq $originalInvokerDisabled) '元の公開状態に戻っていません。'
```

外部ブラウザからログイン・サンプル・単語編集・PDFを再確認します。失敗なら第2節で再停止し、既知正常revisionへの切り戻しを検討します。第4節の途中から来た場合は、確認後にlatest追従への復帰手順へ戻ります。

## SQLiteと操作記録

SQLite DB・セッション・OCRログ・利用回数はインスタンスごとで、revision間でも共有しません。旧revisionへ切り戻しても旧データの復元は保証されず、インスタンス再生成で失われます。最大1インスタンスでもrevision切替の過渡期には複数が存在し得ます。切り戻しはコードの切り戻しであり、編集データのバックアップ復元ではありません。OCR回数上限も再生成でリセットされ、課金上限を保証しません。

実施記録はリポジトリへ保存せず、[Issue #32](https://github.com/magu1436/TestCreator/issues/32)へ記録します。別の運用Google Docsは作成しません。

- 実施者・承認者・日時・理由・対象（固定project/region/service）、run URLとSHA。
- 親index参照・実デプロイ子参照、切替前/後revision、Readyと実traffic、停止直前/後のingressと公開認証方式。
- 初期化・起動・主要画面・PDFの確認結果、失敗時の分類、未実施項目と理由、最終状態と次の担当。

Secret値、APIキー、認証トークン、service定義全体、未加工ログ、個人データは投稿しません。停止・切り戻しを試していない場合は「未実施」と記録し、手順の存在と実地検証を区別します。

コマンドの根拠: [services update（ingress / no-traffic / revision-suffix）](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update)、[update-traffic（to-revisions / to-latest）](https://docs.cloud.google.com/sdk/gcloud/reference/run/services/update-traffic)、[revision describe](https://docs.cloud.google.com/sdk/gcloud/reference/run/revisions/describe)。
