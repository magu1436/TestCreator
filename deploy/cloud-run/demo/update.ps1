#Requires -Version 7.0
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Image)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($Image -cnotmatch '^asia-northeast1-docker\.pkg\.dev/wordtestcreator/webapps/wordtest-demo@sha256:[a-f0-9]{64}$') {
    throw '固定されたデモイメージのsha256 digestを指定してください。'
}
$common = @('--project=wordtestcreator','--region=asia-northeast1','--quiet')
function Invoke-Gcloud([string[]]$Arguments) {
    $PSNativeCommandUseErrorActionPreference = $false
    $output = & gcloud @Arguments
    if ($LASTEXITCODE -ne 0) { throw "gcloudが終了コード $LASTEXITCODE で失敗しました。後続処理は停止しました。" }
    return $output
}
function Read-Gcloud([string[]]$Arguments) {
    return (Invoke-Gcloud ($Arguments + $common + @('--format=json')) | Out-String) | ConvertFrom-Json -AsHashtable
}
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
$before = Read-Gcloud @('run','services','describe','wordtest-demo')
Require ($before.metadata.name -ceq 'wordtest-demo') '対象サービスを検証できません。'
$template = $before.spec.template.spec
Require ($template.serviceAccountName -ceq 'wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com') '専用デモ実行サービスアカウントではありません。'
Require ($template.containers.Count -eq 1) 'コンテナが1個の既存デモサービスだけを更新できます。'
$environment = @{}
foreach ($entry in $template.containers[0].env) {
    Require ($entry.name -cnotmatch '^DB_') 'DB_*が残っています。更新を拒否します。'
    Require (-not $environment.ContainsKey($entry.name)) '環境変数の重複があります。'
    $environment[$entry.name] = $entry
}
Require ($environment.DEMO_MODE.value -ceq 'true') 'DEMO_MODE=trueが必要です。'
# APIが返した当該サービスのURLだけを候補にし、別形式の公開URLも維持する。
$serviceUrls = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
function Add-ServiceUrl($Value) {
    Require ($Value -is [string] -and $Value -cmatch '\Ahttps://wordtest-demo-[a-z0-9-]+\.(?:a\.|asia-northeast1\.)?run\.app\z') '期待するデモURLではありません。'
    $null = $serviceUrls.Add($Value)
}
Add-ServiceUrl $before.status.url
if ($before.metadata.Contains('annotations')) {
    $annotations = $before.metadata.annotations
    Require ($annotations -is [Collections.IDictionary]) 'サービスannotationsが不正です。'
    if ($annotations.Contains('run.googleapis.com/urls')) {
        $rawUrls = $annotations['run.googleapis.com/urls']
        Require ($rawUrls -is [string]) 'サービスURL一覧はJSON文字列が必要です。'
        # -NoEnumerateで配列1要素や空配列の型も維持する。不正JSONは更新前に停止する。
        $urls = ConvertFrom-Json -InputObject $rawUrls -AsHashtable -NoEnumerate
        Require ($urls -is [array]) 'サービスURL一覧はJSON配列が必要です。'
        foreach ($candidate in $urls) { Add-ServiceUrl $candidate }
    }
}
$origin = $environment.CSRF_TRUSTED_ORIGINS.value
Require ($origin -is [string] -and $serviceUrls.Contains($origin)) 'CSRF_TRUSTED_ORIGINSがサービスの実URLと一致しません。'
Require ($environment.ALLOWED_HOSTS.value -is [string] -and $environment.ALLOWED_HOSTS.value -ceq ([uri]$origin).Host) 'ALLOWED_HOSTSとCSRF_TRUSTED_ORIGINSが同じ実URLに対応していません。'
$secretNames = @{}
foreach ($pair in @(@('DJANGO_SECRET_KEY','DJANGO_DEMO_SECRET_KEY'),@('DEMO_PASSWORD','DEMO_ADMIN_PASSWORD'),@('OPENAI_API_KEY','OPENAI_API_KEY'))) {
    $entry = $environment[$pair[0]]
    Require ($null -ne $entry -and -not $entry.ContainsKey('value')) "$($pair[0])にはSecret参照が必要です。"
    $secret = $entry.valueFrom.secretKeyRef
    Require ($secret.key -cmatch '^[1-9][0-9]*$') 'Secretは固定数値バージョンが必要です。'
    $expected = if ($pair[0] -eq 'OPENAI_API_KEY') { '^(?:OPENAI_API_KEY|wordtest-demo-[a-z0-9-]+)$' } else { '^(?:' + $pair[1] + '|wordtest-demo-[a-z0-9-]+)$' }
    Require ($secret.name -cmatch $expected) '専用デモSecret参照を確認できません。'
    Require (-not $secretNames.ContainsKey($secret.name)) '用途間でSecretを共有できません。'
    $secretNames[$secret.name] = $true
}
# 固定revision・分割配信は自動変更しない。image以外の設定を維持するため事前に拒否する。
$traffic = @($before.spec.traffic)
Require ($traffic.Count -eq 1 -and $traffic[0].latestRevision -eq $true -and $traffic[0].percent -eq 100) '最新revisionへの100%配信が必要です。固定revision/分割配信は管理者が別途確認してください。'
$null = Invoke-Gcloud (@('run','services','update','wordtest-demo',"--image=$Image") + $common)
$after = Read-Gcloud @('run','services','describe','wordtest-demo')
$revision = $after.status.latestCreatedRevisionName
# 更新後の検証が失敗しても調査対象のrevisionをActions出力に残す。
if ($env:GITHUB_OUTPUT -and $revision -cmatch '^wordtest-demo-[a-z0-9-]+$') { "revision=$revision" >> $env:GITHUB_OUTPUT }
Require ($revision -cmatch '^wordtest-demo-[a-z0-9-]+$') '更新対象revisionを確認できません。'
Require ($after.status.latestReadyRevisionName -ceq $revision) '新しいrevisionがReadyではありません。'
Require (@($after.status.conditions | Where-Object { $_.type -ceq 'Ready' -and $_.status -ceq 'True' }).Count -eq 1) 'サービスがReadyではありません。'
$actualTraffic = @($after.status.traffic | Where-Object { $_.percent -gt 0 })
Require ($actualTraffic.Count -eq 1 -and $actualTraffic[0].revisionName -ceq $revision -and $actualTraffic[0].percent -eq 100) '新しいrevisionへ100%配信されていません。'
$detail = Read-Gcloud @('run','revisions','describe',$revision)
Require ($detail.metadata.name -ceq $revision -and $detail.status.imageDigest -ceq $Image) '稼働revisionのイメージdigestが一致しません。'
Require (@($detail.status.conditions | Where-Object { $_.type -ceq 'Ready' -and $_.status -ceq 'True' }).Count -eq 1) '新しいイメージの起動に失敗しました。'
Write-Output $revision
