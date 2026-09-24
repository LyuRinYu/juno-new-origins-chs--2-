# ============================================================================
#  Juno: New Origins 简体中文汉化包 —— 安装脚本
#  作者: LyuRinYu
#  设计原则: 只做能确定安全的事; 任何检测不通过就跳过, 绝不损坏游戏文件
# ============================================================================
param(
    [string]$GameDir = "",
    [switch]$SkipLanguage,      # 只打署名补丁，不装语言包
    [switch]$SkipSignature,     # 只装语言包，不打署名补丁
    [switch]$Uninstall
)

$ErrorActionPreference = 'Continue'
$Author       = 'LyuRinYu'
$LangCode     = 'ZH-CN'
$VerifiedVer  = '1.4.104'          # 本包验证过的游戏版本
$PatchVersion = '1.0'
$SignatureSuffix = "  ·  LyuRinYu汉化"

$Work      = $PSScriptRoot                             # 程序文件目录(本脚本所在)
$Payload   = Join-Path $Work 'payload'
$ToolsDir  = $Work
$Root      = Split-Path -Parent $Work                  # 补丁包根目录(程序文件目录的上一层)
$LocalLow  = Join-Path $env:USERPROFILE 'AppData\LocalLow\Jundroo\SimpleRockets 2'
$LangDir   = Join-Path $LocalLow 'Languages'
$TargetDir = Join-Path $LangDir $LangCode

$script:report = New-Object System.Collections.ArrayList
function Say($msg, $level = 'info') {
    $prefix = switch ($level) { 'ok' { '[ OK ]' } 'warn' { '[警告]' } 'err' { '[失败]' } 'step' { '====' } default { '[信息]' } }
    Write-Host "$prefix $msg"
    [void]$script:report.Add("$prefix $msg")
}
function Sep($t) { Write-Host ''; Write-Host "==== $t ====" -ForegroundColor Cyan }

Write-Host ''
Write-Host "  Juno: New Origins 简体中文汉化包 v$PatchVersion   by $Author" -ForegroundColor White
Write-Host "  安装脚本 / 支持 Windows 10 与 11、Steam 版与便携版、任意游戏版本" -ForegroundColor DarkGray
Write-Host ''

# ---------------------------------------------------------------- 1. 找游戏
Sep '1/5 定位游戏目录'
function Test-GameDir([string]$d) {
    if (-not $d) { return $false }
    return (Test-Path (Join-Path $d 'SimpleRockets2_Data\Managed\SimpleRockets2.dll'))
}
function Find-GameDir([string]$hint) {
    $cands = New-Object System.Collections.ArrayList
    if ($hint) { [void]$cands.Add($hint) }
    # 从补丁包所在位置向上找（补丁包被放进游戏目录时可直接命中）
    $p = $Root
    for ($i = 0; $i -lt 5 -and $p; $i++) {
        [void]$cands.Add($p)
        [void]$cands.Add((Join-Path $p 'game'))
        $parent = Split-Path -Parent $p
        if ($parent -eq $p) { break }
        $p = $parent
    }
    # 常见安装位置
    $drives = @('C:', 'D:', 'E:', 'F:', 'G:', 'H:')
    foreach ($dv in $drives) {
        [void]$cands.Add("$dv\Program Files (x86)\Steam\steamapps\common\Juno New Origins")
        [void]$cands.Add("$dv\SteamLibrary\steamapps\common\Juno New Origins")
        [void]$cands.Add("$dv\Steam\steamapps\common\Juno New Origins")
        [void]$cands.Add("$dv\Games\Juno New Origins")
        [void]$cands.Add("$dv\Juno New Origins")
    }
    foreach ($c in $cands) { if (Test-GameDir $c) { return $c } }
    return $null
}

$game = Find-GameDir $GameDir
if (-not $game) {
    Say '没有自动找到游戏目录。' 'warn'
    Write-Host '请把游戏安装目录（即包含 SimpleRockets2_Data 文件夹的那一层）拖到本窗口后回车，或直接输入路径：'
    $input_path = Read-Host '游戏目录'
    $input_path = $input_path.Trim('"').Trim("'").Trim()
    if (Test-GameDir $input_path) { $game = $input_path }
}
if (-not $game) {
    Say '未找到游戏目录，安装中止（你的游戏文件未被改动）。' 'err'
    Write-Host '提示：正确目录里应当能看到 SimpleRockets2_Data 文件夹和 SimpleRockets2.exe。'
    Read-Host '按回车退出'
    exit 1
}
Say "游戏目录: $game" 'ok'

$dataDir = Join-Path $game 'SimpleRockets2_Data'
$dllPath = Join-Path $dataDir 'Managed\SimpleRockets2.dll'
$assetsPath = Join-Path $dataDir 'resources.assets'

# ---------------------------------------------------------------- 2. 版本
Sep '2/5 读取游戏版本'
$gameVer = '未知'
try {
    $ggm = Join-Path $dataDir 'globalgamemanagers'
    if (Test-Path $ggm) {
        $bytes = [System.IO.File]::ReadAllBytes($ggm)
        $head = $bytes[0..[Math]::Min(8191, $bytes.Length - 1)]
        $text = [System.Text.Encoding]::GetEncoding(28591).GetString($head)
        $m = [regex]::Matches($text, '(?<![0-9.])(\d{1,2}\.\d{1,3}\.\d{1,5})(?![0-9.])')
        foreach ($mm in $m) {
            $v = $mm.Groups[1].Value
            if ($v -notmatch '^2022\.' -and $v -notmatch '^20[0-9][0-9]\.') { $gameVer = $v; break }
        }
    }
} catch { }
if ($gameVer -eq '未知') { Say '无法读取游戏版本（不影响语言包安装）' 'warn' }
elseif ($gameVer -eq $VerifiedVer) { Say "游戏版本 $gameVer（本包完整验证过的版本）" 'ok' }
else { Say "游戏版本 $gameVer —— 与本包验证版本($VerifiedVer)不同：语言包仍然可用（未翻译项自动回落英文），署名补丁会自动检测、不匹配则跳过" 'warn' }

# ---------------------------------------------------------------- 3. 语言包
if (-not $Uninstall -and -not $SkipLanguage) {
    Sep '3/5 安装语言包'
    $srcLang = Join-Path $Payload "Languages\$LangCode"
    if (-not (Test-Path $srcLang)) { Say "补丁包内缺少语言包文件: $srcLang" 'err'; Read-Host '按回车退出'; exit 1 }
    if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    $copied = 0
    foreach ($f in (Get-ChildItem $srcLang -File)) {
        Copy-Item $f.FullName (Join-Path $TargetDir $f.Name) -Force
        $copied++
    }
    Say "已安装 $copied 个文件 -> $TargetDir" 'ok'
    Say '语言包是纯数据文件，不影响存档 / 成就 / 云同步；未翻译的条目会自动显示英文' 'info'

    # 语言设置
    $settings = Join-Path $LocalLow 'Settings.xml'
    if (Test-Path $settings) {
        try {
            $bak = "$settings.bak_chs"
            if (-not (Test-Path $bak)) { Copy-Item $settings $bak -Force }
            $xml = Get-Content $settings -Raw -Encoding UTF8
            if ($xml -match 'language="[^"]*"') {
                $new = [regex]::Replace($xml, 'language="[^"]*"', "language=""$LangCode""")
                if ($new -ne $xml) { Set-Content $settings $new -Encoding UTF8 -NoNewline; Say '已把游戏语言设置为中文' 'ok' }
                else { Say '游戏语言已是中文' 'info' }
            }
        } catch { Say '设置语言失败（可在游戏内 设置→通用→语言 手动选择 ZH-CN）' 'warn' }
    } else {
        Say '尚未生成 Settings.xml：请在游戏内 设置→通用→语言 选择 ZH-CN' 'info'
    }
} else {
    Sep '3/5 语言包（本次跳过）'
}

# ---------------------------------------------------------------- 4. 署名补丁
if (-not $Uninstall -and -not $SkipSignature) {
    Sep '4/5 署名补丁（可选增强，失败自动跳过）'

    # 4a. dll：主菜单版本号后缀
    try {
        $cecil = Join-Path $ToolsDir 'lib\Mono.Cecil.dll'
        if (-not (Test-Path $cecil)) { throw '缺少 Mono.Cecil.dll' }
        Add-Type -Path $cecil
        $resolver = [Mono.Cecil.DefaultAssemblyResolver]::new()
        $resolver.AddSearchDirectory((Split-Path -Parent $dllPath))
        $rp = [Mono.Cecil.ReaderParameters]::new()
        $rp.ReadingMode = [Mono.Cecil.ReadingMode]::Immediate
        $rp.ReadSymbols = $false
        $rp.InMemory = $true
        $rp.AssemblyResolver = $resolver
        $asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($dllPath, $rp)
        $script:already = $false
        $script:target = $null
        function Patch-Type($t) {
            if ($script:target) { return }
            foreach ($m in $t.Methods) {
                if ($script:target) { return }
                if (-not $m.HasBody) { continue }
                $ins = $m.Body.Instructions
                for ($i = 0; $i -lt $ins.Count; $i++) {
                    if ($ins[$i].OpCode.Name -ne 'ldstr' -or $ins[$i].Operand -ne 'version-number-text') { continue }
                    for ($j = $i + 1; $j -lt $ins.Count; $j++) {
                        $op = $ins[$j]
                        if (-not $op.Operand) { continue }
                        if (($op.OpCode.Name -eq 'callvirt' -or $op.OpCode.Name -eq 'call') -and $op.Operand.Name -eq 'set_text') {
                            for ($k = [Math]::Max(0, $j - 5); $k -lt $j; $k++) {
                                if ($ins[$k].OpCode.Name -eq 'ldstr' -and $ins[$k].Operand -is [string] -and $ins[$k].Operand.Contains($Author)) { $script:already = $true }
                            }
                            if ($script:already) { $script:target = 'ALREADY'; return }
                            $strType = $asm.MainModule.TypeSystem.String
                            $concat = [Mono.Cecil.MethodReference]::new('Concat', $strType, $strType)
                            $concat.HasThis = $false
                            $concat.Parameters.Add([Mono.Cecil.ParameterDefinition]::new($strType))
                            $concat.Parameters.Add([Mono.Cecil.ParameterDefinition]::new($strType))
                            $imported = $asm.MainModule.ImportReference($concat)
                            $il = $m.Body.GetILProcessor()
                            $il.InsertBefore($op, $il.Create([Mono.Cecil.Cil.OpCodes]::Ldstr, [string]$SignatureSuffix))
                            $il.InsertBefore($op, $il.Create([Mono.Cecil.Cil.OpCodes]::Call, $imported))
                            $script:target = $t.FullName + '.' + $m.Name
                            return
                        }
                    }
                }
            }
            foreach ($n in $t.NestedTypes) { Patch-Type $n }
        }
        foreach ($t in $asm.MainModule.Types) { Patch-Type $t }

        if ($script:target -eq 'ALREADY') {
            Say '主菜单版本号署名已存在（跳过）' 'info'
            $asm.Dispose()
        } elseif (-not $script:target) {
            Say "本版本的主菜单代码结构与验证版本不同，已安全跳过 dll 补丁（游戏文件未改动）" 'warn'
            $asm.Dispose()
        } else {
            $bak = "$dllPath.orig"
            if (-not (Test-Path $bak)) { Copy-Item $dllPath $bak -Force; Say "已备份原 dll -> SimpleRockets2.dll.orig" 'info' }
            $tmp = "$dllPath.chs_new"
            $asm.Write($tmp)
            $asm.Dispose()
            # 回读校验后才替换（避免写出坏文件）
            $check = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($tmp, [Mono.Cecil.ReaderParameters]::new())
            $typeCount = $check.MainModule.Types.Count
            $check.Dispose()
            if ($typeCount -gt 0) {
                Copy-Item $tmp $dllPath -Force
                Remove-Item $tmp -Force
                Say "已打补丁: $($script:target) -> 版本号后显示「$SignatureSuffix」" 'ok'
            } else {
                Remove-Item $tmp -Force
                Say '补丁文件自检未通过，已放弃（游戏文件未改动）' 'warn'
            }
        }
    } catch {
        Say "dll 补丁跳过（$($_.Exception.Message)）——游戏文件未改动" 'warn'
    }

    # 4b. resources.assets —— 已弃用，不再修改
    #
    # 原用途：把主菜单版本号从被遮挡的右上角移到右下角。
    # 弃用原因：实测该元素在游戏里根本不会渲染（无任何可见收益），却需要直接改写
    #           Unity 二进制资源文件；在游戏版本与验证版本不一致的机器上，寻找对齐
    #           属性的 300 字节窗口可能命中别的元素，存在损坏资源的风险（表现为黑屏）。
    #           零收益 + 有风险 ⇒ 移除。
    #
    # 若旧版安装包已经改过该文件，双击「② 卸载还原.bat」会从 resources.assets.orig 恢复。
    Say '布局调整已弃用（不影响汉化效果，避免改动游戏二进制资源）' 'info'
} else {
    Sep '4/5 署名补丁（本次跳过）'
}

# ---------------------------------------------------------------- 5. 完成
Sep '5/5 完成'
Write-Host ''
Write-Host '  安装完成。启动游戏后：' -ForegroundColor Green
Write-Host '   - 设置 → 通用 → 语言 → 选择 ZH-CN（若已自动设置则会直接是中文）'
Write-Host '   - 主菜单「菜单」→「制作人员」应显示「制作人员 · LyuRinYu汉化」'
Write-Host '   - 主菜单右下角应显示版本号 + 汉化署名'
Write-Host ''
Write-Host "  卸载：双击文件夹里的「② 卸载还原.bat」，或直接删除 $TargetDir" -ForegroundColor DarkGray
Write-Host ''
$logFile = Join-Path $Work 'install-log.txt'
try { $script:report | Set-Content $logFile -Encoding UTF8 } catch { }
Read-Host '按回车退出'
