# registryやクラウドを呼ばず、実行用manifestの選択を検証する。
$ErrorActionPreference = 'Stop'
function Assert($Condition, $Message) { if (-not $Condition) { throw $Message } }
$resolve = Join-Path $PSScriptRoot 'resolve-image.ps1'
Assert (Test-Path $resolve) 'resolve-image.ps1が未実装です'
$name = 'asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo'
$parent = "$name@sha256:76189fb36d92b3e2b294e437e393317000a13c6f885c5f0b5cfe173fb76223e1"
$childDigest = 'sha256:12b19d6d9cd8f1a53a831c95f56781c25f221581df5644bc5900b35138e15e68'
$ociManifest = 'application/vnd.oci.image.manifest.v1+json'
$dockerManifest = 'application/vnd.docker.distribution.manifest.v2+json'
function New-Index {
    return @{schemaVersion=2;mediaType='application/vnd.oci.image.index.v1+json';manifests=@(
        @{digest=$childDigest;mediaType=$ociManifest;platform=@{os='linux';architecture='amd64'}},
        @{digest='sha256:c2573cf3d66fc1f161f80a3a81b131fe775aab17ebd3ff7bb07af374c96160bb';mediaType=$ociManifest;platform=@{os='unknown';architecture='unknown'}}
    )}
}
# 実際のindexとattestationの組み合わせからCloud Runの実行manifestを選ぶ。
$index = New-Index
$result = & $resolve -Image $parent -ManifestJson ($index | ConvertTo-Json -Depth 10)
Assert ($result -ceq "$name@$childDigest") 'OCI indexからlinux/amd64の子digestを解決できません'
# Docker manifest listと、attestationを含まない1要素のlistも同様に扱う。
$index.mediaType = 'application/vnd.docker.distribution.manifest.list.v2+json'
$index.manifests = @($index.manifests[0]); $index.manifests[0].mediaType=$dockerManifest
$result = & $resolve -Image $parent -ManifestJson ($index | ConvertTo-Json -Depth 10)
Assert ($result -ceq "$name@$childDigest") 'Docker manifest listを解決できません'
foreach ($type in @($ociManifest,$dockerManifest)) {
    $result = & $resolve -Image $parent -ManifestJson (@{schemaVersion=2;mediaType=$type;config=@{};layers=@()} | ConvertTo-Json)
    Assert ($result -ceq $parent) '直接manifestのdigestを変更しています'
}
foreach ($case in @('attestation-only','arm64-only','multiple','digest','media-type','schema','array','null','json','nested','manifests-object')) {
    $index = New-Index
    switch ($case) {
        attestation-only { $index.manifests=@($index.manifests[1]) }
        arm64-only { $index.manifests=@($index.manifests[0]); $index.manifests[0].platform.architecture='arm64' }
        multiple { $index.manifests=@($index.manifests[0],$index.manifests[0]) }
        digest { $index.manifests[0].digest='sha256:invalid' }
        media-type { $index.mediaType='application/unknown' }
        schema { $index.schemaVersion=1 }
        nested { $index.manifests[0].mediaType='application/vnd.oci.image.index.v1+json' }
        manifests-object { $index.manifests=$index.manifests[0] }
    }
    $json = $index | ConvertTo-Json -Depth 10
    if ($case -eq 'array') { $json='[]' }
    if ($case -eq 'null') { $json='null' }
    if ($case -eq 'json') { $json='{' }
    $failed=$false; try { & $resolve -Image $parent -ManifestJson $json } catch { $failed=$true }
    Assert $failed "不正なmanifest $case を拒否していません"
}
foreach ($bad in @($parent.Replace('wordtest-demo@','wordtest@'),$parent.Replace('webapps/','other/'),"${name}:latest", "$name@sha256:invalid")) {
    $failed=$false; try { & $resolve -Image $bad -ManifestJson ((New-Index) | ConvertTo-Json -Depth 10) } catch { $failed=$true }
    Assert $failed '別repositoryまたは不正なdigestを拒否していません'
}
$outputFile = Join-Path ([IO.Path]::GetTempPath()) ('resolve-image-' + [guid]::NewGuid() + '.txt')
$previousOutput = $env:GITHUB_OUTPUT
try {
    $env:GITHUB_OUTPUT=$outputFile
    $null = & $resolve -Image $parent -ManifestJson ((New-Index) | ConvertTo-Json -Depth 10)
    Assert ((Get-Content -LiteralPath $outputFile) -ceq "image=$name@$childDigest") 'Actions出力のデプロイimageが一致しません'
} finally {
    $env:GITHUB_OUTPUT=$previousOutput
    if (Test-Path -LiteralPath $outputFile) { Remove-Item -LiteralPath $outputFile }
}
Write-Output 'resolve-image.Tests.ps1: 全テスト成功'
