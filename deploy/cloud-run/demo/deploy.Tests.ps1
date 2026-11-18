# 実クラウドを呼ばず、渡される引数と停止条件を検証する単独テスト。
$ErrorActionPreference = 'Stop'
$global:DemoTestCalls = [System.Collections.Generic.List[object]]::new()
$global:DemoTestFailAt = 0
$global:DemoTestUrl = 'https://wordtest-demo-123.asia-northeast1.run.app'
function global:gcloud {
    $global:DemoTestCalls.Add(@($args))
    $global:LASTEXITCODE = 0
    if ($global:DemoTestFailAt -eq $global:DemoTestCalls.Count) { $global:LASTEXITCODE = 7; return }
    if ($args[1] -eq 'services' -and $args[2] -eq 'describe') { return $global:DemoTestUrl }
}
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$deploy = Join-Path $PSScriptRoot 'deploy.ps1'
Assert (Test-Path $deploy) 'デプロイスクリプトが未実装です'
$valid = @{
    Image = 'asia-northeast1-docker.pkg.dev/wordtestcreator/demo/app@sha256:' + ('a' * 64)
    ServiceAccount = 'wordtest-demo@wordtestcreator.iam.gserviceaccount.com'
    DjangoSecret = 'wordtest-demo-django-secret-key:1'
    DemoPasswordSecret = 'wordtest-demo-password:2'
    OpenAiSecret = 'openai-api-key:3'
}
& $deploy @valid -WhatIf
Assert ($global:DemoTestCalls.Count -eq 0) 'WhatIfでgcloudが呼ばれました'
& $deploy @valid -Confirm:$false
Assert ($global:DemoTestCalls.Count -eq 3) 'deploy、describe、updateの順に3回必要です'
$first = $global:DemoTestCalls[0]
Assert (($first[0..2] -join ' ') -eq 'run deploy wordtest-demo') '本番とは別サービスに限定してください'
foreach ($arg in @('--project=wordtestcreator','--region=asia-northeast1','--no-allow-unauthenticated','--invoker-iam-check','--min=0','--max=1','--cpu=2','--memory=2Gi','--concurrency=1','--timeout=120','--service-account=wordtest-demo@wordtestcreator.iam.gserviceaccount.com','--set-secrets=DJANGO_SECRET_KEY=wordtest-demo-django-secret-key:1,DEMO_PASSWORD=wordtest-demo-password:2,OPENAI_API_KEY=openai-api-key:3')) {
    Assert ($first -contains $arg) "引数がありません: $arg"
}
Assert (($global:DemoTestCalls[1][0..2] -join ' ') -eq 'run services describe') '実URLを取得してください'
Assert ($global:DemoTestCalls[2] -contains '--update-env-vars=ALLOWED_HOSTS=wordtest-demo-123.asia-northeast1.run.app,CSRF_TRUSTED_ORIGINS=https://wordtest-demo-123.asia-northeast1.run.app') '実URLの完全一致設定が必要です'
foreach ($case in @(
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
foreach ($index in 1..3) {
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
Assert ($global:DemoTestCalls.Count -eq 2) '不正URLで更新しました'
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
if (args[0] === 'run' && args[2] === 'describe') console.log('https://wordtest-demo-abc-an.a.run.app');
'@ | Set-Content (Join-Path $temporary 'capture.cjs')
        $nodePath = (Get-Command node -ErrorAction Stop).Source
        ('@echo off' + "`r`n" + '"' + $nodePath + '" "%~dp0capture.cjs" %*' + "`r`n" + 'exit /b %errorlevel%') | Set-Content (Join-Path $temporary 'gcloud.cmd')
        $env:PATH = $temporary + [IO.Path]::PathSeparator + $oldPath
        & (Join-Path $temporary 'deploy.ps1') @valid -Confirm:$false
        $nativeCalls = @(Get-Content $env:DEMO_TEST_LOG | ForEach-Object { ,(ConvertFrom-Json $_) })
        Assert ($nativeCalls.Count -eq 3) '.cmd経由の呼び出し回数が違います'
        Assert ($nativeCalls[0] -contains ('--env-vars-file=' + (Join-Path $temporary 'environment.example.yaml'))) '.cmdで空白を含むパスが分割されました'
        Assert ($nativeCalls[0] -contains '--set-secrets=DJANGO_SECRET_KEY=wordtest-demo-django-secret-key:1,DEMO_PASSWORD=wordtest-demo-password:2,OPENAI_API_KEY=openai-api-key:3') '.cmdでSecret引数が分割されました'
        Assert ($nativeCalls[2] -contains '--update-env-vars=ALLOWED_HOSTS=wordtest-demo-abc-an.a.run.app,CSRF_TRUSTED_ORIGINS=https://wordtest-demo-abc-an.a.run.app') '旧形式URLを反映できませんでした'
        Write-Host 'PASS: Windows gcloud.cmd argument boundary'
    } finally {
        $env:PATH = $oldPath; $env:DEMO_TEST_LOG = $oldLog
        # テストで生成した一意な一時ディレクトリだけを削除する。
        if ($temporary.StartsWith([IO.Path]::GetTempPath())) { Remove-Item -LiteralPath $temporary -Recurse -Force }
    }
}
