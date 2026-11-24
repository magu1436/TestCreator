# 実クラウドを呼ばず、既存サービスの更新と停止条件を検証する。
$ErrorActionPreference = 'Stop'
function Assert($Value, $Message) { if (-not $Value) { throw $Message } }
$script = Join-Path $PSScriptRoot 'update.ps1'
Assert (Test-Path $script) 'update.ps1が未実装です'
$global:Calls = [Collections.Generic.List[object]]::new()
$global:FailureAt = 0
$image = 'asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo@sha256:' + ('a' * 64)
function Reset-Fixture {
    $global:Calls.Clear(); $global:FailureAt = 0
    $global:Before = @{
        metadata = @{name='wordtest-demo'}
        spec = @{traffic=@(@{latestRevision=$true;percent=100});template=@{spec=@{
            serviceAccountName='wordtestcreator-demo@wordtestcreator.iam.gserviceaccount.com'
            containers=@(@{env=@(
                @{name='DEMO_MODE';value='true'},
                @{name='ALLOWED_HOSTS';value='wordtest-demo-123.asia-northeast1.run.app'},
                @{name='CSRF_TRUSTED_ORIGINS';value='https://wordtest-demo-123.asia-northeast1.run.app'},
                @{name='DJANGO_SECRET_KEY';valueFrom=@{secretKeyRef=@{name='DJANGO_DEMO_SECRET_KEY';key='1'}}},
                @{name='DEMO_PASSWORD';valueFrom=@{secretKeyRef=@{name='DEMO_ADMIN_PASSWORD';key='2'}}},
                @{name='OPENAI_API_KEY';valueFrom=@{secretKeyRef=@{name='OPENAI_API_KEY';key='3'}}}
            )})
        }}}
        status=@{url='https://wordtest-demo-123.asia-northeast1.run.app'; latestCreatedRevisionName='wordtest-demo-old';latestReadyRevisionName='wordtest-demo-old'}
    }
    $global:After = @{metadata=@{name='wordtest-demo'};status=@{url=$global:Before.status.url;latestCreatedRevisionName='wordtest-demo-new';latestReadyRevisionName='wordtest-demo-new';conditions=@(@{type='Ready';status='True'});traffic=@(@{revisionName='wordtest-demo-new';percent=100})}}
    $global:Revision = @{metadata=@{name='wordtest-demo-new'};status=@{imageDigest=$image;conditions=@(@{type='Ready';status='True'})}}
}
function global:gcloud {
    $global:Calls.Add(@($args)); $global:LASTEXITCODE=0
    if ($global:Calls.Count -eq $global:FailureAt) { $global:LASTEXITCODE=9; return }
    if ($args[1] -eq 'revisions') { return ($global:Revision | ConvertTo-Json -Depth 20 -Compress) }
    if ($args[2] -eq 'describe') {
        if ($global:Calls.Count -eq 1) { return ($global:Before | ConvertTo-Json -Depth 20 -Compress) }
        return ($global:After | ConvertTo-Json -Depth 20 -Compress)
    }
}
Reset-Fixture
$result = & $script -Image $image
Assert ($result -eq 'wordtest-demo-new') '検証済みrevisionを返してください'
Assert ($global:Calls.Count -eq 4) 'describe/update/describe/revision describeが必要です'
Assert (($global:Calls[1][0..3] -join ' ') -eq 'run services update wordtest-demo') '既存デモサービスだけ更新してください'
Assert ($global:Calls[1] -contains "--image=$image") 'digest固定が必要です'
Assert (@($global:Calls[1] | Where-Object { $_ -match 'env|secret|ingress|memory|cpu|account|traffic' }).Count -eq 0) 'image以外の設定を変更しています'
# 実応答ではstatus.urlと公開設定が別形式でも、同じサービスの有効URLになる。
$hashUrl = 'https://wordtest-demo-derix6hqia-an.a.run.app'
$numberUrl = 'https://wordtest-demo-1033430002089.asia-northeast1.run.app'
foreach ($configuredUrl in @($numberUrl, $hashUrl)) {
    Reset-Fixture
    $global:Before.status.url = $hashUrl
    $global:Before.metadata.annotations = @{'run.googleapis.com/urls' = (@($numberUrl, $hashUrl) | ConvertTo-Json -Compress)}
    $global:Before.spec.template.spec.containers[0].env[1].value = ([uri]$configuredUrl).Host
    $global:Before.spec.template.spec.containers[0].env[2].value = $configuredUrl
    $result = & $script -Image $image
    Assert ($result -eq 'wordtest-demo-new') '同じサービスの別形式URLを拒否しています'
    Assert ($global:Calls.Count -eq 4) '有効URLで更新まで完了していません'
}
# 注釈なしの旧URL形式もそのまま受け入れる。
Reset-Fixture
$global:Before.status.url = $hashUrl
$global:Before.spec.template.spec.containers[0].env[1].value = ([uri]$hashUrl).Host
$global:Before.spec.template.spec.containers[0].env[2].value = $hashUrl
$result = & $script -Image $image
Assert ($result -eq 'wordtest-demo-new') '注釈なしの旧URL形式を拒否しています'
# JSON配列1要素を文字列へ展開せず、注釈なしの従来形式も維持する。
Reset-Fixture
$global:Before.metadata.annotations = @{'run.googleapis.com/urls' = ('["' + $global:Before.status.url + '"]')}
$result = & $script -Image $image
Assert ($result -eq 'wordtest-demo-new') 'URL配列1要素を拒否しています'
foreach ($case in @('unknown','wildcard','production','http','path','csrf-mismatch','invalid-json','json-string','json-object','json-null','non-string','production-entry','http-entry','invalid-status','non-string-annotation','multiple-hosts','invalid-url-entry')) {
    Reset-Fixture
    $global:Before.status.url = $hashUrl
    $global:Before.metadata.annotations = @{'run.googleapis.com/urls' = (@($numberUrl, $hashUrl) | ConvertTo-Json -Compress)}
    $global:Before.spec.template.spec.containers[0].env[1].value = ([uri]$numberUrl).Host
    $global:Before.spec.template.spec.containers[0].env[2].value = $numberUrl
    switch ($case) {
        unknown { $global:Before.spec.template.spec.containers[0].env[1].value='wordtest-demo-999.asia-northeast1.run.app'; $global:Before.spec.template.spec.containers[0].env[2].value='https://wordtest-demo-999.asia-northeast1.run.app' }
        wildcard { $global:Before.spec.template.spec.containers[0].env[1].value='*' }
        production { $global:Before.spec.template.spec.containers[0].env[1].value='wordtest-1033430002089.asia-northeast1.run.app'; $global:Before.spec.template.spec.containers[0].env[2].value='https://wordtest-1033430002089.asia-northeast1.run.app' }
        http { $global:Before.spec.template.spec.containers[0].env[2].value=$numberUrl.Replace('https:', 'http:') }
        path { $global:Before.spec.template.spec.containers[0].env[2].value="$numberUrl/path" }
        csrf-mismatch { $global:Before.spec.template.spec.containers[0].env[2].value=$hashUrl }
        invalid-json { $global:Before.metadata.annotations['run.googleapis.com/urls']='[' }
        json-string { $global:Before.metadata.annotations['run.googleapis.com/urls']='"https://wordtest-demo-1033430002089.asia-northeast1.run.app"' }
        json-object { $global:Before.metadata.annotations['run.googleapis.com/urls']='{}' }
        json-null { $global:Before.metadata.annotations['run.googleapis.com/urls']='null' }
        non-string { $global:Before.metadata.annotations['run.googleapis.com/urls']='[123]' }
        production-entry { $global:Before.metadata.annotations['run.googleapis.com/urls']='["https://wordtest-1033430002089.asia-northeast1.run.app"]' }
        http-entry { $global:Before.metadata.annotations['run.googleapis.com/urls']='["http://wordtest-demo-1033430002089.asia-northeast1.run.app"]' }
        invalid-status { $global:Before.status.url='https://wordtest-derix6hqia-an.a.run.app' }
        non-string-annotation { $global:Before.metadata.annotations['run.googleapis.com/urls']=123 }
        multiple-hosts { $global:Before.spec.template.spec.containers[0].env[1].value=@(([uri]$numberUrl).Host, 'evil.example') }
        invalid-url-entry { $global:Before.metadata.annotations['run.googleapis.com/urls']='["https://wordtest-demo-1033430002089.asia-northeast1.run.app/path"]' }
    }
    $failed=$false; try { & $script -Image $image } catch { $failed=$true }
    Assert $failed "不正なURL設定 $case を拒否していません"
    Assert ($global:Calls.Count -eq 1) "不正なURL設定 $case で更新を実行しました"
}
# 同じdigestの再実行で新revisionが作られなくても、実際の稼働状態で判定する。
Reset-Fixture
$global:Before.status.latestCreatedRevisionName='wordtest-demo-new'
$result = & $script -Image $image
Assert ($result -eq 'wordtest-demo-new') '同じdigestの安全な再実行を拒否しています'
foreach ($step in 1..4) {
    Reset-Fixture; $global:FailureAt=$step; $failed=$false
    try { & $script -Image $image } catch { $failed=$true }
    Assert $failed "gcloud失敗 $step が成功扱いです"
    Assert ($global:Calls.Count -eq $step) '失敗後に後続処理が動きました'
}
foreach ($case in @('account','db','mode','url','django','password','pinned','split','notready','oldready','wrongdigest','revisionfailed','oldtraffic')) {
    Reset-Fixture
    switch ($case) {
        account { $global:Before.spec.template.spec.serviceAccountName='run-wordtestcreator@wordtestcreator.iam.gserviceaccount.com' }
        db { $global:Before.spec.template.spec.containers[0].env += @{name='DB_HOST';value='production'} }
        mode { $global:Before.spec.template.spec.containers[0].env[0].value='false' }
        url { $global:Before.status.url='https://wordtest-123.asia-northeast1.run.app' }
        django { $global:Before.spec.template.spec.containers[0].env[3].valueFrom.secretKeyRef.name='DJANGO_SECRET_KEY' }
        password { $global:Before.spec.template.spec.containers[0].env[4].valueFrom.secretKeyRef.key='latest' }
        pinned { $global:Before.spec.traffic=@(@{revisionName='wordtest-demo-old';percent=100}) }
        split { $global:Before.spec.traffic=@(@{latestRevision=$true;percent=90},@{revisionName='wordtest-demo-old';percent=10}) }
        notready { $global:After.status.conditions[0].status='False' }
        oldready { $global:After.status.latestReadyRevisionName='wordtest-demo-old' }
        wrongdigest { $global:Revision.status.imageDigest=$image.Replace('a' * 64,'b' * 64) }
        revisionfailed { $global:Revision.status.conditions[0].status='False' }
        oldtraffic { $global:After.status.traffic[0].revisionName='wordtest-demo-old' }
    }
    $failed=$false; try { & $script -Image $image } catch { $failed=$true }
    Assert $failed "不正な状態 $case を拒否していません"
    if ($case -in @('account','db','mode','url','django','password','pinned','split')) { Assert ($global:Calls.Count -eq 1) '事前検証失敗後に更新しました' }
}
foreach ($bad in @($image.Replace('wordtest-demo@','wordtest@'),$image.Replace('webapps/','other/'),'tag:latest')) {
    Reset-Fixture; $failed=$false; try { & $script -Image $bad } catch { $failed=$true }
    Assert $failed '本番/別repository/tag入力を拒否していません'; Assert ($global:Calls.Count -eq 0) '入力不正でgcloudを呼びました'
}
Remove-Item Function:\gcloud
Write-Output 'update.Tests.ps1: 全テスト成功'
