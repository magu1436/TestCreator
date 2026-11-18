#Requires -Version 7.0
[CmdletBinding(SupportsShouldProcess, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory)][string]$Image,
    [Parameter(Mandatory)][string]$ServiceAccount,
    [Parameter(Mandatory)][string]$DjangoSecret,
    [Parameter(Mandatory)][string]$DemoPasswordSecret,
    [Parameter(Mandatory)][string]$OpenAiSecret
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
# 対象を固定し、本番サービスや別プロジェクトへの流用を防止する。
$project = 'wordtestcreator'
$region = 'asia-northeast1'
$service = 'wordtest-demo'
if ($Image -cnotmatch '^asia-northeast1-docker\.pkg\.dev/wordtestcreator/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$') {
    throw 'Imageにはwordtestcreatorのasia-northeast1 Artifact Registryイメージをsha256 digest付きで指定してください。'
}
if ($ServiceAccount -cnotmatch '^wordtest-demo(?:-[a-z0-9-]+)?@wordtestcreator\.iam\.gserviceaccount\.com$') {
    throw 'デモ専用サービスアカウント（wordtest-demo または wordtest-demo-接尾辞）が必要です。'
}
foreach ($reference in @($DjangoSecret, $DemoPasswordSecret, $OpenAiSecret)) {
    if ($reference -cnotmatch '^[A-Za-z][A-Za-z0-9_-]*:[1-9][0-9]*$' -or $reference -match '(?i)placeholder|replace|example') {
        throw 'Secretは実際のID:数値バージョンを指定してください。latestやプレースホルダーは使用できません。'
    }
}
if ($DjangoSecret -notmatch '^wordtest-demo-' -or $DemoPasswordSecret -notmatch '^wordtest-demo-' -or
    $DjangoSecret.Split(':')[0] -eq $DemoPasswordSecret.Split(':')[0] -or
    $OpenAiSecret.Split(':')[0] -in @($DjangoSecret.Split(':')[0], $DemoPasswordSecret.Split(':')[0])) {
    throw 'Django秘密鍵と共有パスワードは別々のwordtest-demo-専用Secret、OCRは別Secretを指定してください。'
}
$environment = Join-Path $PSScriptRoot 'environment.example.yaml'
if (-not (Test-Path -LiteralPath $environment -PathType Leaf)) { throw 'デモ環境変数ファイルがありません。' }
# WhatIfではgcloudの探索も実行もしない。承認後だけ外部コマンドへ進む。
if (-not $PSCmdlet.ShouldProcess("$project/$region/$service", '非公開デプロイと実URLの環境変数反映')) { return }
$null = Get-Command gcloud -ErrorAction Stop
function Invoke-Gcloud([string[]]$Arguments) {
    # PowerShell 7.3以降でも.cmdはLegacy方式を使う。配列の各要素を1引数として渡す。
    # 空白や引用符を必要とする値は入力に許可しない。Invoke-Expressionは使わない。
    $PSNativeCommandArgumentPassing = 'Legacy'
    $PSNativeCommandUseErrorActionPreference = $false
    $output = & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) { throw "gcloudが終了コード $LASTEXITCODE で失敗しました。後続処理は実行していません。" }
    return $output
}
$common = @("--project=$project", "--region=$region", '--quiet')
$null = Invoke-Gcloud (@('run', 'deploy', $service, "--image=$Image", "--service-account=$ServiceAccount",
    '--no-allow-unauthenticated', '--invoker-iam-check', '--ingress=internal', '--min=0', '--max=1', '--cpu=2', '--memory=2Gi', '--concurrency=1', '--timeout=120',
    "--env-vars-file=$environment", "--set-secrets=DJANGO_SECRET_KEY=$DjangoSecret,DEMO_PASSWORD=$DemoPasswordSecret,OPENAI_API_KEY=$OpenAiSecret") + $common)
function Get-PublicBindings {
    $raw = Invoke-Gcloud (@('run', 'services', 'get-iam-policy', $service, '--format=json') + $common)
    $policy = ($raw | Out-String) | ConvertFrom-Json -AsHashtable -ErrorAction Stop
    if ($policy -isnot [System.Collections.IDictionary]) { throw 'IAMポリシーがJSONオブジェクトではありません。ingressはinternalのまま停止します。' }
    if (-not $policy.Contains('bindings')) { return }
    if ($policy.bindings -isnot [array]) { throw 'IAM bindingsが配列ではありません。' }
    foreach ($binding in $policy.bindings) {
        if ($binding -isnot [System.Collections.IDictionary] -or
            $binding.role -isnot [string] -or $binding.role -notmatch '^roles/[A-Za-z0-9.]+$' -or
            $binding.members -isnot [array] -or @($binding.members | Where-Object { $_ -isnot [string] }).Count -gt 0) {
            throw 'IAM bindingの形式を検証できません。ingressはinternalのまま停止します。'
        }
        foreach ($member in $binding.members) {
            # Invokerを含む任意ロールの公開principalを除去する。条件付きは自動変更せず停止する。
            if ($member -in @('allUsers', 'allAuthenticatedUsers')) {
                if ($binding.Contains('condition')) { throw '条件付き公開IAMがあります。手動で確認・除去後に再実行してください。' }
                [pscustomobject]@{ Role = $binding.role; Member = $member }
            }
        }
    }
}
# deployはIAM変更失敗を警告だけで終了する場合があるため、別コマンドと再読込で確認する。
$publicBindings = @(Get-PublicBindings)
foreach ($binding in $publicBindings) {
    $null = Invoke-Gcloud (@('run', 'services', 'remove-iam-policy-binding', $service,
        "--member=$($binding.Member)", "--role=$($binding.Role)", '--condition=None') + $common)
}
if (@(Get-PublicBindings).Count -ne 0) { throw '公開IAMが残っています。ingressはinternalのまま停止します。' }
$description = (Invoke-Gcloud (@('run', 'services', 'describe', $service, '--format=json') + $common) | Out-String) | ConvertFrom-Json -AsHashtable -ErrorAction Stop
if ($description -isnot [System.Collections.IDictionary] -or $description.metadata -isnot [System.Collections.IDictionary] -or
    $description.status -isnot [System.Collections.IDictionary]) { throw 'サービス状態を検証できません。' }
if ($description.metadata.Contains('annotations')) {
    $annotations = $description.metadata.annotations
    if ($annotations -isnot [System.Collections.IDictionary]) { throw 'サービスannotationsが不正です。' }
    if ($annotations.Contains('run.googleapis.com/invoker-iam-disabled') -and
        ($annotations['run.googleapis.com/invoker-iam-disabled'] -isnot [string] -or
         $annotations['run.googleapis.com/invoker-iam-disabled'] -cne 'false')) {
        throw 'Invoker IAMチェックが有効であることを確認できません。ingressはinternalのまま停止します。'
    }
}
$url = $description.status.url
if ($url -isnot [string]) { throw 'サービスURLが文字列ではありません。' }
if ($url -cnotmatch '^https://wordtest-demo-[a-z0-9-]+\.(?:a\.|asia-northeast1\.)?run\.app$') { throw 'Cloud Runから期待するデモサービスのHTTPS URLを取得できませんでした。非公開のまま停止します。' }
$hostname = ([uri]$url).Host
$null = Invoke-Gcloud (@('run', 'services', 'update', $service,
    '--ingress=all', "--update-env-vars=ALLOWED_HOSTS=$hostname,CSRF_TRUSTED_ORIGINS=$url") + $common)
Write-Output "非公開デプロイ完了: $url"
Write-Output '匿名公開は許可していません。再実行時も非公開に戻します。'
