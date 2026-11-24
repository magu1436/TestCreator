#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Ref,
    [Parameter(Mandatory)][string]$Repository
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
# branch名や短縮SHA、revision式、改行を受け付けない。
if ($Ref -cmatch '^[a-fA-F0-9]{40}$') { $candidate = $Ref.ToLowerInvariant() }
elseif ($Ref -cmatch '^refs/tags/[A-Za-z0-9][A-Za-z0-9._/-]*$') {
    & git check-ref-format $Ref
    if ($LASTEXITCODE -ne 0) { throw 'タグ名が不正です。' }
    $candidate = $Ref
} else { throw '40桁commit SHAまたはrefs/tags/タグ名を指定してください。' }
$sha = & git -C $Repository rev-parse --verify --end-of-options "$candidate^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or $sha -cnotmatch '^[a-f0-9]{40}$') { throw '取得済みリポジトリ内のcommitへ解決できません。' }
if ($Ref -cmatch '^[a-fA-F0-9]{40}$' -and $sha -cne $candidate) { throw 'commit自体のSHAを指定してください。' }
if ($env:GITHUB_OUTPUT) { "sha=$sha" >> $env:GITHUB_OUTPUT }
Write-Output $sha
