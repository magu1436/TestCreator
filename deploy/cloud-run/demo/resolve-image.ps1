#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Image,
    [Parameter(Mandatory)][string]$ManifestJson
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
$name = 'asia-northeast1-docker.pkg.dev/wordtestcreator/webapps/wordtest-demo'
Require ($Image -cmatch '\Aasia-northeast1-docker\.pkg\.dev/wordtestcreator/webapps/wordtest-demo@sha256:[a-f0-9]{64}\z') '固定されたデモイメージのsha256 digestが必要です。'
$manifest = ConvertFrom-Json -InputObject $ManifestJson -AsHashtable -NoEnumerate
Require ($manifest -is [Collections.IDictionary]) 'manifestはJSONオブジェクトが必要です。'
Require (($manifest.schemaVersion -is [long] -or $manifest.schemaVersion -is [int]) -and $manifest.schemaVersion -eq 2) 'manifestのschemaVersionは2が必要です。'
$imageTypes = @('application/vnd.oci.image.manifest.v1+json', 'application/vnd.docker.distribution.manifest.v2+json')
$indexTypes = @('application/vnd.oci.image.index.v1+json', 'application/vnd.docker.distribution.manifest.list.v2+json')
$resolved = $Image
if ($manifest.mediaType -cin $indexTypes) {
    Require ($manifest.manifests -is [array]) 'indexのmanifestsは配列が必要です。'
    $candidates = @(
        foreach ($entry in $manifest.manifests) {
            Require ($entry -is [Collections.IDictionary] -and $entry.mediaType -cin $imageTypes) '未対応の子manifest形式です。'
            Require ($entry.digest -is [string] -and $entry.digest -cmatch '\Asha256:[a-f0-9]{64}\z') '子manifestのdigestが不正です。'
            Require ($entry.platform -is [Collections.IDictionary] -and $entry.platform.os -is [string] -and $entry.platform.architecture -is [string]) '子manifestのplatformが不正です。'
            # unknown/unknownのattestationは実行用イメージとして選択しない。
            if ($entry.platform.os -ceq 'linux' -and $entry.platform.architecture -ceq 'amd64') { $entry.digest }
        }
    )
    Require ($candidates.Count -eq 1) 'linux/amd64の実行用manifestが一意ではありません。'
    $resolved = "$name@$($candidates[0])"
} else {
    Require ($manifest.mediaType -cin $imageTypes) '未対応のmanifest形式です。'
}
if ($env:GITHUB_OUTPUT) { "image=$resolved" >> $env:GITHUB_OUTPUT }
Write-Output $resolved
