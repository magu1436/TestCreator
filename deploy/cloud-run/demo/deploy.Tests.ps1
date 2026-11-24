# 実クラウドを呼ばず、渡される引数と停止条件を検証する単独テスト。
$ErrorActionPreference = 'Stop'
$global:DemoTestCalls = [System.Collections.Generic.List[object]]::new()
$global:DemoTestFailAt = 0
$global:DemoTestPolicies = @('{"bindings":[]}', '{"bindings":[]}')
$global:DemoTestPolicyIndex = 0
$global:DemoTestInvokerDisabled = 'false'
$global:DemoTestUrl = 'https://wordtest-demo-123.asia-northeast1.run.app'
function global:gcloud {
    $global:DemoTestCalls.Add(@($args))
    $global:LASTEXITCODE = 0
    if ($global:DemoTestFailAt -eq $global:DemoTestCalls.Count) { $global:LASTEXITCODE = 7; return }
    if ($args[2] -eq 'get-iam-policy') { $value = $global:DemoTestPolicies[[Math]::Min($global:DemoTestPolicyIndex, $global:DemoTestPolicies.Count - 1)]; $global:DemoTestPolicyIndex++; return $value }
    if ($args[1] -eq 'services' -and $args[2] -eq 'describe') { return (@{status=@{url=$global:DemoTestUrl};metadata=@{annotations=@{'run.googleapis.com/invoker-iam-disabled'=$global:DemoTestInvokerDisabled}}} | ConvertTo-Json -Depth 5 -Compress) }
}
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$deploy = Join-Path $PSScriptRoot 'deploy.ps1'
Assert (Test-Path $deploy) 'デプロイスクリプトが未実装です'
$valid = @{
    Image = 'asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo@sha256:' + ('a' * 64)
    ServiceAccount = 'wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com'
    DjangoSecret = 'DJANGO_DEMO_SECRET_KEY:1'
    DemoPasswordSecret = 'DEMO_ADMIN_PASSWORD:1'
    OpenAiSecret = 'OPENAI_API_KEY:2'
}
& $deploy @valid -WhatIf
Assert ($global:DemoTestCalls.Count -eq 0) 'WhatIfでgcloudが呼ばれました'
& $deploy @valid -Confirm:$false
Assert ($global:DemoTestCalls.Count -eq 5) 'deploy、IAM確認2回、describe、updateの順に5回必要です'
$first = $global:DemoTestCalls[0]
Assert (($first[0..2] -join ' ') -eq 'run deploy wordtest-demo') '本番とは別サービスに限定してください'
foreach ($arg in @('--project=wordtestcreator','--region=asia-northeast1','--no-allow-unauthenticated','--invoker-iam-check','--ingress=internal','--min=0','--max=1','--cpu=2','--memory=2Gi','--concurrency=1','--timeout=120','--service-account=wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com','--set-secrets=DJANGO_SECRET_KEY=DJANGO_DEMO_SECRET_KEY:1,DEMO_PASSWORD=DEMO_ADMIN_PASSWORD:1,OPENAI_API_KEY=OPENAI_API_KEY:2')) {
    Assert ($first -contains $arg) "引数がありません: $arg"
}
Assert ($first -contains ('--image=asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo@sha256:' + ('a' * 64))) '固定digestのイメージを渡していません'
Assert (($global:DemoTestCalls[3][0..2] -join ' ') -eq 'run services describe') '実URLを取得してください'
Assert ($global:DemoTestCalls[4] -contains '--update-env-vars=ALLOWED_HOSTS=wordtest-demo-123.asia-northeast1.run.app,CSRF_TRUSTED_ORIGINS=https://wordtest-demo-123.asia-northeast1.run.app') '実URLの完全一致設定が必要です'
# 従来のデモ専用名も引き続き受け入れる。
foreach ($legacyAccount in @('wordtest-demo', 'wordtest-demo-runtime')) {
    $global:DemoTestCalls.Clear()
    $legacy = $valid.Clone()
    $legacy.ServiceAccount = "$legacyAccount@wordtestcreator.iam.gserviceaccount.com"
    $legacy.DjangoSecret = 'wordtest-demo-django-secret-key:1'
    $legacy.DemoPasswordSecret = 'wordtest-demo-password:2'
    & $deploy @legacy -Confirm:$false
    Assert ($global:DemoTestCalls.Count -eq 5) '従来のデモ専用名が拒否されました'
}
foreach ($case in @(
    @{ ServiceAccount = 'run-wordtestcreator@wordtestcreator.iam.gserviceaccount.com' },
    @{ ServiceAccount = 'wordtestcreator-demo-other@wordtestcreator.iam.gserviceaccount.com' },
    @{ DjangoSecret = 'DJANGO_SECRET_KEY:1' }, @{ DemoPasswordSecret = 'ADMIN_PASSWORD:1' },
    @{ DemoPasswordSecret = 'DJANGO_SUPERUSER_PASSWORD:1' },
    @{ DjangoSecret = 'DEMO_ADMIN_PASSWORD:1'; DemoPasswordSecret = 'DJANGO_DEMO_SECRET_KEY:1' },
    @{ DjangoSecret = 'DJANGO_DEMO_SECRET_KEY:latest' }, @{ DemoPasswordSecret = 'DEMO_ADMIN_PASSWORD:0' },
    @{ OpenAiSecret = 'OPENAI_API_KEY:latest' }, @{ OpenAiSecret = 'DJANGO_DEMO_SECRET_KEY:2' },
    @{ OpenAiSecret = 'DEMO_ADMIN_PASSWORD:2' },
    @{ DjangoSecret = 'wordtest-demo-shared:1'; DemoPasswordSecret = 'wordtest-demo-shared:2' },
    @{ Image = 'placeholder' }, @{ ServiceAccount = 'production@wordtestcreator.iam.gserviceaccount.com' },
    @{ DjangoSecret = 'production-key:1' }, @{ DemoPasswordSecret = 'wordtest-demo-password:latest' },
    @{ OpenAiSecret = 'REPLACE_ME:1' }, @{ Project = 'other-project' }, @{ Service = 'wordtest' }
)) {
    $global:DemoTestCalls.Clear()
    $inputValues = $valid.Clone()
    foreach ($key in $case.Keys) { $inputValues[$key] = $case[$key] }
    $failed = $false
    try { & $deploy @inputValues -Confirm:$false } catch { $failed = $true }
    Assert $failed '不正入力を拒否しませんでした'
    Assert ($global:DemoTestCalls.Count -eq 0) '入力検証より先にgcloudを呼びました'
}
foreach ($index in 1..5) {
    $global:DemoTestCalls.Clear(); $global:DemoTestFailAt = $index
    $failed = $false
    try { & $deploy @valid -Confirm:$false } catch { $failed = $true }
    Assert $failed 'gcloud失敗を伝播してください'
    Assert ($global:DemoTestCalls.Count -eq $index) '失敗後に処理を続けました'
}
$global:DemoTestFailAt = 0; $global:DemoTestCalls.Clear(); $global:DemoTestUrl = 'https://unexpected.example.com'
$failed = $false
try { & $deploy @valid -Confirm:$false } catch { $failed = $true }
Assert $failed '想定外のURLを受け入れました'
Assert ($global:DemoTestCalls.Count -eq 4) '不正URLで更新しました'
$global:DemoTestUrl = 'https://wordtest-demo-123.asia-northeast1.run.app'
foreach ($annotation in @('true', 'invalid', 123, $true, $false)) {
    $global:DemoTestInvokerDisabled = $annotation
    $global:DemoTestCalls.Clear()
    $failed = $false
    try { & $deploy @valid -Confirm:$false } catch { $failed = $true }
    Assert $failed 'Invoker IAMチェック無効/不正状態を拒否しませんでした'
    Assert ($global:DemoTestCalls.Count -eq 4) 'Invoker IAMチェック検証失敗後に更新しました'
}
$global:DemoTestInvokerDisabled = 'false'
# deployが成功してもIAMが残るケースを再現する。除去失敗・残存時は外向けingressへ戻さない。
$global:DemoTestUrl = 'https://wordtest-demo-123.asia-northeast1.run.app'
$public = '{"bindings":[{"role":"roles/run.invoker","members":["allUsers","allAuthenticatedUsers"]}]}'
foreach ($scenario in @('removed', 'removeFailure', 'remains', 'invalidJson', 'invalidShape', 'nullPolicy', 'invalidMembers', 'conditional')) {
    $global:DemoTestCalls.Clear(); $global:DemoTestPolicyIndex = 0; $global:DemoTestFailAt = 0
    $global:DemoTestPolicies = @($public, '{"bindings":[]}')
    if ($scenario -eq 'removeFailure') { $global:DemoTestFailAt = 3 }
    if ($scenario -eq 'remains') { $global:DemoTestPolicies = @($public, $public) }
    if ($scenario -eq 'invalidJson') { $global:DemoTestPolicies = @('not json') }
    if ($scenario -eq 'invalidShape') { $global:DemoTestPolicies = @('{"bindings":{}}') }
    if ($scenario -eq 'nullPolicy') { $global:DemoTestPolicies = @('null') }
    if ($scenario -eq 'invalidMembers') { $global:DemoTestPolicies = @('{"bindings":[{"role":"roles/run.invoker","members":"allUsers"}]}') }
    if ($scenario -eq 'conditional') { $global:DemoTestPolicies = @('{"bindings":[{"role":"roles/run.invoker","members":["allUsers"],"condition":{"expression":"true","title":"test"}}]}') }
    $failed = $false
    try { & $deploy @valid -Confirm:$false } catch { $failed = $true }
    $updates = @($global:DemoTestCalls | Where-Object { $_[2] -eq 'update' })
    if ($scenario -eq 'removed') {
        Assert (-not $failed) '公開IAM除去後に完了できませんでした'
        Assert ($global:DemoTestCalls.Count -eq 7) '両公開principalの除去と再確認が必要です'
        Assert ($global:DemoTestCalls[2] -contains '--member=allUsers') 'allUsersを除去していません'
        Assert ($global:DemoTestCalls[3] -contains '--member=allAuthenticatedUsers') 'allAuthenticatedUsersを除去していません'
        Assert ($updates[0] -contains '--ingress=all') '確認後のingress復帰が必要です'
    } else {
        Assert $failed "安全でないIAM状態で成功しました: $scenario"
        Assert ($updates.Count -eq 0) "IAM検証失敗後にingressを戻しました: $scenario"
    }
}
Remove-Item Function:\gcloud
Write-Host 'PASS: Cloud Run demo deployment contract'

# Windowsの実.cmd境界で空白を含むパス、カンマを含む引数を確認する。
if ($IsWindows) {
    $temporary = Join-Path ([IO.Path]::GetTempPath()) ('demo deploy test ' + [guid]::NewGuid())
    $oldPath = $env:PATH
    $oldLog = $env:DEMO_TEST_LOG
    try {
        $null = New-Item -ItemType Directory $temporary
        Copy-Item (Join-Path $PSScriptRoot 'deploy.ps1') $temporary
        Copy-Item (Join-Path $PSScriptRoot 'environment.example.yaml') $temporary
        $env:DEMO_TEST_LOG = Join-Path $temporary 'calls.jsonl'
        @'
const fs = require('fs');
const args = process.argv.slice(2);
fs.appendFileSync(process.env.DEMO_TEST_LOG, JSON.stringify(args) + '\n');
if (args[2] === 'get-iam-policy') console.log('{"bindings":[]}');
if (args[0] === 'run' && args[2] === 'describe') console.log(JSON.stringify({status:{url:'https://wordtest-demo-abc-an.a.run.app'},metadata:{annotations:{}}}));
'@ | Set-Content (Join-Path $temporary 'capture.cjs')
        $nodePath = (Get-Command node -ErrorAction Stop).Source
        ('@echo off' + "`r`n" + '"' + $nodePath + '" "%~dp0capture.cjs" %*' + "`r`n" + 'exit /b %errorlevel%') | Set-Content (Join-Path $temporary 'gcloud.cmd')
        $env:PATH = $temporary + [IO.Path]::PathSeparator + $oldPath
        & (Join-Path $temporary 'deploy.ps1') @valid -Confirm:$false
        $nativeCalls = @(Get-Content $env:DEMO_TEST_LOG | ForEach-Object { ,(ConvertFrom-Json $_) })
        Assert ($nativeCalls.Count -eq 5) '.cmd経由の呼び出し回数が違います'
        Assert ($nativeCalls[0] -contains ('--env-vars-file=' + (Join-Path $temporary 'environment.example.yaml'))) '.cmdで空白を含むパスが分割されました'
        Assert ($nativeCalls[0] -contains '--set-secrets=DJANGO_SECRET_KEY=DJANGO_DEMO_SECRET_KEY:1,DEMO_PASSWORD=DEMO_ADMIN_PASSWORD:1,OPENAI_API_KEY=OPENAI_API_KEY:2') '.cmdでSecret引数が分割されました'
        Assert ($nativeCalls[4] -contains '--update-env-vars=ALLOWED_HOSTS=wordtest-demo-abc-an.a.run.app,CSRF_TRUSTED_ORIGINS=https://wordtest-demo-abc-an.a.run.app') '旧形式URLを反映できませんでした'
        Write-Host 'PASS: Windows gcloud.cmd argument boundary'
    } finally {
        $env:PATH = $oldPath; $env:DEMO_TEST_LOG = $oldLog
        # テストで生成した一意な一時ディレクトリだけを削除する。
        if ($temporary.StartsWith([IO.Path]::GetTempPath())) { Remove-Item -LiteralPath $temporary -Recurse -Force }
    }
}
