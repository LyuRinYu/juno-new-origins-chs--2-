# ============================================================================
#  Juno: New Origins 简体中文汉化包 —— 卸载 / 还原脚本
#  作者: LyuRinYu
#  作用: 移除语言包 + 把被补丁的游戏文件还原为原始版本
# ============================================================================
param([string]$GameDir = "")

$ErrorActionPreference = 'Continue'
$Root     = Split-Path -Parent $PSScriptRoot           # 补丁包根目录(本脚本位于 程序文件 子目录内)
$LocalLow = Join-Path $env:USERPROFILE 'AppData\LocalLow\Jundroo\SimpleRockets 2'
$LangDir  = Join-Path $LocalLow 'Languages'
$TargetDir = Join-Path $LangDir 'ZH-CN'

function Say($m, $lvl = 'info') {
    $p = switch ($lvl) { 'ok' { '[ OK ]' } 'warn' { '[警告]' } 'err' { '[失败]' } default { '[信息]' } }
    Write-Host "$p $m"
}

Write-Host ''
Write-Host '  Juno: New Origins 简体中文汉化包 —— 卸载' -ForegroundColor White
Write-Host ''

function Test-GameDir([string]$d) {
    if (-not $d) { return $false }
    return (Test-Path (Join-Path $d 'SimpleRockets2_Data\Managed\SimpleRockets2.dll'))
}
function Find-GameDir([string]$hint) {
    $cands = New-Object System.Collections.ArrayList
    if ($hint) { [void]$cands.Add($hint) }
    $p = $Root
    for ($i = 0; $i -lt 5 -and $p; $i++) {
        [void]$cands.Add($p); [void]$cands.Add((Join-Path $p 'game'))
        $parent = Split-Path -Parent $p
        if ($parent -eq $p) { break }
        $p = $parent
    }
    $drives = @('C:', 'D:', 'E:', 'F:', 'G:', 'H:')
    foreach ($dv in $drives) {
        [void]$cands.Add("$dv\Program Files (x86)\Steam\steamapps\common\Juno New Origins")
        [void]$cands.Add("$dv\SteamLibrary\steamapps\common\Juno New Origins")
        [void]$cands.Add("$dv\Steam\steamapps\common\Juno New Origins")
    }
    foreach ($c in $cands) { if (Test-GameDir $c) { return $c } }
    return $null
}

# 1. 语言包
if (Test-Path $TargetDir) {
    Remove-Item $TargetDir -Recurse -Force
    Say "已删除语言包目录: $TargetDir" 'ok'
    # 清掉空的语言根目录（若已空）
    if ((Test-Path $LangDir) -and ((Get-ChildItem $LangDir -ErrorAction SilentlyContinue).Count -eq 0)) {
        Remove-Item $LangDir -Force -ErrorAction SilentlyContinue
    }
} else {
    Say '未找到语言包目录（可能已卸载）'
}

# 2. 游戏文件还原
$game = Find-GameDir $GameDir
if (-not $game) {
    Say '未找到游戏目录：跳过游戏文件还原（若你打过署名补丁，请手动把 *.orig 改名回去）' 'warn'
} else {
    Say "游戏目录: $game"
    $pairs = @(
        @{ name = 'SimpleRockets2.dll'; path = (Join-Path $game 'SimpleRockets2_Data\Managed\SimpleRockets2.dll') },
        @{ name = 'resources.assets';   path = (Join-Path $game 'SimpleRockets2_Data\resources.assets') }
    )
    foreach ($p in $pairs) {
        $bak = "$($p.path).orig"
        if (Test-Path $bak) {
            Copy-Item $bak $p.path -Force
            Say "已还原 $($p.name)（来自 .orig 备份）" 'ok'
        } else {
            Say "$($p.name) 没有 .orig 备份，未改动（说明当时未打补丁）"
        }
    }
}

# 3. 语言设置还原
$settings = Join-Path $LocalLow 'Settings.xml'
$bak = "$settings.bak_chs"
if (Test-Path $bak) {
    Copy-Item $bak $settings -Force
    Remove-Item $bak -Force
    Say '已还原游戏语言设置' 'ok'
} elseif (Test-Path $settings) {
    Say '语言设置未改过（无需还原）'
}

Write-Host ''
Write-Host '  卸载完成。游戏已恢复原状。' -ForegroundColor Green
Write-Host ''
Read-Host '按回车退出'
