# ============================================================================
#  Juno: New Origins 简体中文汉化包 —— 作者署名验证工具
#  用途: 在别人的电脑上（或看到有人转载本汉化时）验证署名是否来自原作者
#  原理: 扫描语言包译文里内嵌的零宽字符水印（U+200B/U+200C），
#        以及字体 name 表、文件头、语言目录签名文件
#  无需任何依赖，Windows 自带 PowerShell 即可运行
# ============================================================================
$ErrorActionPreference = 'Continue'
$ZW0 = [char]0x200B
$ZW1 = [char]0x200C

function Say($m, $c = 'Gray') { Write-Host $m -ForegroundColor $c }

Write-Host ''
Say '  Juno: New Origins 简体中文汉化包 —— 署名验证' 'White'
Say '  ============================================' 'DarkGray'
Write-Host ''

# --- 定位语言包 ---
$cands = @(
    (Join-Path $env:USERPROFILE 'AppData\LocalLow\Jundroo\SimpleRockets 2\Languages\ZH-CN'),
    (Join-Path $PSScriptRoot 'payload\Languages\ZH-CN'),
    (Join-Path $PSScriptRoot '..\payload\Languages\ZH-CN'),
    (Join-Path $PSScriptRoot '..\..\payload\Languages\ZH-CN')
)
$langDir = $null
foreach ($c in $cands) { if (Test-Path (Join-Path $c 'Strings.xml')) { $langDir = (Resolve-Path $c).Path; break } }
if (-not $langDir) {
    Say '找不到语言包（Strings.xml）。请把本脚本放在补丁包内运行，或确认已安装汉化。' 'Yellow'
    Read-Host '按回车退出'
    exit 1
}
Say "语言包目录: $langDir" 'Gray'
Write-Host ''

# --- 1. 零宽字符水印 ---
Say '[1/4] 扫描译文内嵌的零宽字符水印' 'Cyan'
$strings = Join-Path $langDir 'Strings.xml'
$lines = Get-Content $strings -Encoding UTF8
$wmHits = @()
$decoded = @{}
foreach ($line in $lines) {
    if ($line.IndexOf($ZW0) -lt 0 -and $line.IndexOf($ZW1) -lt 0) { continue }
    $bits = New-Object System.Text.StringBuilder
    foreach ($ch in $line.ToCharArray()) {
        if ($ch -eq $ZW0) { [void]$bits.Append('0') }
        elseif ($ch -eq $ZW1) { [void]$bits.Append('1') }
    }
    $bs = $bits.ToString()
    if ($bs.Length -lt 8) { continue }
    $bytes = New-Object System.Collections.ArrayList
    for ($i = 0; $i + 8 -le $bs.Length; $i += 8) {
        [void]$bytes.Add([Convert]::ToByte($bs.Substring($i, 8), 2))
    }
    try {
        $text = [System.Text.Encoding]::UTF8.GetString($bytes.ToArray())
        $idm = [regex]::Match($line, '<s id="([^"]+)"')
        $key = if ($idm.Success) { $idm.Groups[1].Value } else { '(未知条目)' }
        $wmHits += $key
        if (-not $decoded.ContainsKey($text)) { $decoded[$text] = 0 }
        $decoded[$text]++
    } catch { }
}
if ($wmHits.Count -eq 0) {
    Say '  未发现水印 —— 这可能不是 LyuRinYu 制作的原版汉化包（署名被抹除？）' 'Red'
} else {
    Say ("  发现水印条目: " + $wmHits.Count + " 处") 'Green'
    foreach ($k in $decoded.Keys) {
        Say ("  水印解码内容: 「" + $k + "」  x" + $decoded[$k]) 'Green'
    }
    if ($decoded.ContainsKey('LyuRinYu-JNO-CHS')) {
        Say '  => 水印有效：本语言包由 LyuRinYu 制作' 'Green'
    } else {
        Say '  => 水印内容异常（可能被篡改）' 'Yellow'
    }
    Say ('  含签名条目示例: ' + ($wmHits | Select-Object -First 5 -Unique) -join ', ') 'DarkGray'
}
Write-Host ''

# --- 2. 文件头与签名文件 ---
Say '[2/4] 检查文件头与签名文件' 'Cyan'
$head = (Get-Content $strings -TotalCount 8 -Encoding UTF8) -join ' '
if ($head -match 'LyuRinYu') {
    Say '  Strings.xml 文件头含作者署名: 是' 'Green'
    $m = [regex]::Match($head, '作者[:：]\s*(\S+)')
    if ($m.Success) { Say ('  署名: ' + $m.Groups[1].Value) 'Green' }
} else {
    Say '  Strings.xml 文件头署名已被移除' 'Yellow'
}
$sigFile = Join-Path $langDir 'SIGNATURE.txt'
if (Test-Path $sigFile) {
    Say '  语言目录存在 SIGNATURE.txt: 是' 'Green'
    (Get-Content $sigFile -TotalCount 3 -Encoding UTF8) | ForEach-Object { Say ('    ' + $_) 'DarkGray' }
} else {
    Say '  SIGNATURE.txt 不存在（已被删除？）' 'Yellow'
}
Write-Host ''

# --- 3. 字体元数据 ---
Say '[3/4] 检查字体 name 表署名' 'Cyan'
$font = Get-ChildItem $langDir -Filter *.ttf -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $font) {
    Say '  未找到字体文件' 'Yellow'
} else {
    $bytes = [System.IO.File]::ReadAllBytes($font.FullName)
    $latin = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
    $utf16 = [System.Text.Encoding]::Unicode.GetString($bytes)
    $hit = ($latin -match 'LyuRinYu') -or ($utf16 -match 'LyuRinYu') -or ($utf16 -match '汉化打包')
    if ($hit) {
        Say ('  字体 ' + $font.Name + ' 内含作者署名: 是') 'Green'
        $m = [regex]::Match($utf16, '汉化打包[：:]\s*(\S+)')
        if ($m.Success) { Say ('  字体厂商字段: ' + $m.Groups[1].Value) 'Green' }
        $m2 = [regex]::Match($utf16, '(JNO Sans SC;\S+)')
        if ($m2.Success) { Say ('  字体唯一标识: ' + $m2.Groups[1].Value) 'Green' }
    } else {
        Say '  字体元数据里的署名已被清除' 'Yellow'
    }
}
Write-Host ''

# --- 4. 结论 ---
Say '[4/4] 结论' 'Cyan'
$score = 0
if ($wmHits.Count -gt 0) { $score++ }
if ($head -match 'LyuRinYu') { $score++ }
if (Test-Path $sigFile) { $score++ }
if ($hit) { $score++ }
Say ("  署名证据: $score / 4 项") 'White'
if ($score -ge 2) {
    Say '  => 高度可信：这是 LyuRinYu 制作的简体中文汉化包' 'Green'
} elseif ($score -eq 1) {
    Say '  => 疑似被抹除署名后转载（仍有残留证据）' 'Yellow'
} else {
    Say '  => 未找到作者署名：可能是第三方重新制作的汉化' 'Red'
}
Write-Host ''
Say '  作者声明：本汉化的署名分布在水印、字体二进制与语言包文件多处；' 'DarkGray'
Say '  抹除后再分发属于剽窃。' 'DarkGray'
Write-Host ''
Read-Host '按回车退出'
