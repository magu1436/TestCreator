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
