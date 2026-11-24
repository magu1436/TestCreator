$ErrorActionPreference = 'Stop'
$resolve = Join-Path $PSScriptRoot 'resolve-source.ps1'
if (-not (Test-Path $resolve)) { throw 'resolve-source.ps1が未実装です' }
$repo = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory $repo | Out-Null
try {
    git -C $repo init --quiet
    git -C $repo -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -m test --quiet
    git -C $repo tag -a release/demo -m demo
    $sha = git -C $repo rev-parse HEAD
    foreach ($ref in @($sha,'refs/tags/release/demo')) {
        $actual = & $resolve -Ref $ref -Repository $repo
        if ($actual -cne $sha) { throw 'SHA/tagをcommit SHAに解決できません' }
    }
    foreach ($ref in @('main','HEAD','refs/heads/main','--help','refs/tags/missing','refs/tags/$(touch x)','refs/tags/foo..bar','refs/tags/foo@{bar}',('a'*40),"$sha`nINJECT=yes")) {
        $failed=$false; try { & $resolve -Ref $ref -Repository $repo } catch { $failed=$true }
        if (-not $failed) { throw "不正なrefを拒否していません: $ref" }
    }
    Write-Output 'resolve-source.Tests.ps1: 全テスト成功'
} finally {
    # 自分で生成した一時ディレクトリのみ削除する。
    $resolved = [IO.Path]::GetFullPath($repo)
    if ($resolved.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
