# -*- coding: utf-8 -*-
"""
把汉化成果打包成可分发的补丁包（给其他设备安装用）

最终结构（用户打开文件夹一眼就能看出点哪个）:
    Juno新起源-简体中文汉化包-v1.0/
    ├── ① 一键安装汉化.bat          <- 双击这个
    ├── ② 卸载还原.bat
    ├── 使用说明.txt
    └── 程序文件（勿删）/            <- 其余全部收纳在此，眼不见为净
        ├── install.ps1 / uninstall.ps1 / verify_signature.ps1
        ├── 验证署名.bat / 安装-仅语言包.bat / 安装-仅署名补丁.bat
        ├── payload/Languages/ZH-CN/...
        ├── lib/Mono.Cecil.dll
        ├── OFL.txt / optional 文档 / SHA256SUMS.txt

编码规则（否则其他设备中文乱码）: .bat 用 GBK+CRLF；.ps1 用 UTF-8(BOM)；.txt 用 GBK
"""
import hashlib
import os
import shutil
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = HERE.parent if HERE.name == 'scripts' else HERE
LANG_SRC = Path(os.path.expanduser('~')) / 'AppData/LocalLow/Jundroo/SimpleRockets 2/Languages/ZH-CN'
OFL_SRC = Path(os.path.expanduser('~')) / 'AppData/LocalLow/Jundroo/SimpleRockets 2/Languages/Examples/ZH-CN/OFL.txt'
CECIL = (HERE / 'lib' / 'Mono.Cecil.dll') if (HERE / 'lib' / 'Mono.Cecil.dll').exists() \
    else ROOT / 'dll_patch' / 'cecil' / 'lib' / 'net40' / 'Mono.Cecil.dll'
VERSION = '1.0.2'
PKG_NAME = f'Juno新起源-简体中文汉化包-v{VERSION}'
SUBDIR = '程序文件（勿删）'
DIST = ROOT / 'dist_build'
PKG = DIST / PKG_NAME

# ---------------------------------------------------------------- 批处理
BAT_INSTALL = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 安装汉化 - Juno: New Origins\r\n'
    'color 0B\r\n'
    'echo.\r\n'
    'echo   ==================================================\r\n'
    'echo      Juno: New Origins   简体中文汉化包\r\n'
    'echo      正在安装，大约 10 秒，请不要关闭本窗口...\r\n'
    'echo   ==================================================\r\n'
    'echo.\r\n'
    f'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{SUBDIR}\\install.ps1"\r\n'
)
BAT_UNINSTALL = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 卸载还原 - Juno: New Origins\r\n'
    'color 0E\r\n'
    'echo.\r\n'
    'echo   ==================================================\r\n'
    'echo      正在卸载汉化，并把游戏还原为原版...\r\n'
    'echo   ==================================================\r\n'
    'echo.\r\n'
    f'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0{SUBDIR}\\uninstall.ps1"\r\n'
)
BAT_VERIFY = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 验证署名\r\n'
    'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify_signature.ps1"\r\n'
)
BAT_NOLANG = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 安装汉化 - 仅语言包\r\n'
    'color 0B\r\n'
    'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -SkipSignature\r\n'
)
BAT_DIAG = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 诊断 - Juno: New Origins 汉化\r\n'
    'color 0D\r\n'
    'echo.\r\n'
    'echo   ==================================================\r\n'
    'echo      汉化补丁 · 环境诊断\r\n'
    'echo      收集 系统 / 显卡 / 游戏文件 / 语言包 / 运行日志\r\n'
    'echo      只读取信息，不修改任何文件\r\n'
    'echo   ==================================================\r\n'
    'echo.\r\n'
    f'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0诊断.ps1" %*\r\n'
)
BAT_SIGONLY = (
    '@echo off\r\n'
    'chcp 936 >nul\r\n'
    'title 安装汉化 - 仅署名补丁\r\n'
    'color 0B\r\n'
    'powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -SkipLanguage\r\n'
)

USAGE_TXT = """Juno: New Origins 简体中文汉化包 v1.0   by LyuRinYu
=========================================================

  ★ 安装：双击本文件夹里的「① 一键安装汉化.bat」
  ★ 卸载：双击「② 卸载还原.bat」（游戏会恢复成原版）

  装完直接启动游戏就是中文。若仍有英文，进 设置 → 通用 → 语言 → 选 ZH-CN。

---------------------------------------------------------
  本汉化包含什么
---------------------------------------------------------
  完整汉化 9318 条界面文本（100%）：主菜单、设置、建造器、零件、
  行星工坊、生涯合约、教程、飞行界面、Vizzy 可视化编程等全部模块，
  并自带中文字体（OFL 许可，可自由分发）。

---------------------------------------------------------
  版本兼容性（重要）
---------------------------------------------------------
  * 语言包：跨版本可用。游戏里没有的条目自动显示英文，多出来的条目
    自动忽略 —— 低版本/高版本都不会出错、不会崩溃。
  * 署名补丁：安装时自动检测你的游戏文件，结构与验证版本不符就自动
    跳过，绝不修改、绝不损坏。
  * 本包在游戏 1.4.104 上完整验证。

---------------------------------------------------------
  常见问题
---------------------------------------------------------
  问：进游戏有声音，但画面全黑 / 一直黑屏？
  答：按顺序做这两步 ——
      【第一步】双击「② 卸载还原.bat」，然后启动游戏。
                · 游戏恢复正常 → 是署名补丁与你的游戏版本不兼容。
                  用最新版补丁重装；只想看中文的话，改用
                  「程序文件（勿删）\\安装-仅语言包（不改游戏文件）.bat」。
                · 依然黑屏 → 与汉化无关，是系统/显卡环境问题，看第二步。
      【第二步】双击「程序文件（勿删）\\诊断-黑屏排查.bat」，
                它会在桌面生成「JNO汉化诊断报告.txt」，把这个文件发给作者。
      最常见的环境原因（纯净重装系统后高发）：
        · 显卡驱动没装（设备管理器里显示「Microsoft 基本显示适配器」）
        · 缺少 VC++ 2015-2022 运行库
        · 游戏使用全屏独占模式，与显示器分辨率/刷新率不匹配

  问：进游戏还是英文？
  答：设置 → 通用 → 语言 → 手动选 ZH-CN，然后重启游戏。
  问：中文显示成方框？
  答：说明游戏版本过旧、不支持随包字体机制，请反馈给作者。
  问：提示未找到游戏目录？
  答：手动把游戏目录（含 SimpleRockets2_Data 文件夹的那一层）拖进窗口回车。
  问：杀毒软件报警？
  答：安装会修改游戏文件（署名补丁），可能被误判。脚本是纯文本的
      「程序文件（勿删）\\install.ps1」，可自行查看；
      不想改游戏文件就用「程序文件（勿删）\\安装-仅语言包.bat」。

---------------------------------------------------------
  安全与还原
---------------------------------------------------------
  * 语言包是纯数据，放在
    %%USERPROFILE%%\\AppData\\LocalLow\\Jundroo\\SimpleRockets 2\\Languages\\ZH-CN\\
    不影响存档 / 成就 / 云同步。
  * 若动过游戏文件，会自动备份为同名 .orig 文件。
  * 卸载会删掉语言包并把游戏文件按 .orig 还原。

---------------------------------------------------------
  「程序文件（勿删）」里都是什么
---------------------------------------------------------
  install.ps1 / uninstall.ps1    安装与卸载的脚本（纯文本，可查看）
  verify_signature.ps1 + 验证署名.bat   检查汉化出处是否为原作者
  payload\\...                   语言包本体与字体
  lib\\Mono.Cecil.dll            打署名补丁用的库
  OFL.txt                        字体许可
  校对对照表.tsv / glossary.tsv   想自己改词的可以编辑（高级）
  安装-仅语言包.bat              不修改游戏文件的安装方式

---------------------------------------------------------
  作者声明
---------------------------------------------------------
  本汉化的作者信息分布在水印、字体二进制与语言包文件多处。若你在别处
  看到署名被抹除后转载的本汉化，可运行「验证署名.bat」核对。移除署名
  后再分发属于剽窃。
"""


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write_text(p: Path, text: str, encoding: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding=encoding, newline='') as f:
        f.write(text)


def copy_as_ps1(src: Path, dst: Path):
    """PowerShell 脚本转 UTF-8 with BOM（PS 5.1 无 BOM 会把中文按 GBK 读成乱码）"""
    text = src.read_text(encoding='utf-8')
    with open(dst, 'w', encoding='utf-8-sig', newline='\r\n') as f:
        f.write(text.replace('\r\n', '\n').replace('\n', '\r\n'))


def safe_rmtree(p: Path, tries: int = 6):
    """Windows 上刚写完的文件常被杀软/索引器短暂占用，删不掉就等一会儿重试"""
    import time
    for i in range(tries):
        if not p.exists():
            return
        try:
            shutil.rmtree(p)
            return
        except PermissionError:
            print(f'  (目录被占用，{1.5*(i+1):.1f}s 后重试 {i+1}/{tries}...)' if i == 0 else '', end='', flush=True)
            time.sleep(1.5)
    shutil.rmtree(p)          # 最后一次，失败就抛出来


def main():
    safe_rmtree(PKG)
    work = PKG / SUBDIR
    (work / 'payload' / 'Languages' / 'ZH-CN').mkdir(parents=True)
    (work / 'lib').mkdir(parents=True)

    # 1. 语言包 payload（不含 SimHei 回退字体，控制体积）
    n = 0
    size = 0
    for f in sorted(LANG_SRC.iterdir()):
        if f.name == 'SimHei.ttf':
            continue
        shutil.copy2(f, work / 'payload' / 'Languages' / 'ZH-CN' / f.name)
        n += 1
        size += f.stat().st_size
    print(f'[payload] 语言包 {n} 个文件, {size/1024/1024:.1f} MB')

    # 2. 库与许可
    shutil.copy2(CECIL, work / 'lib' / 'Mono.Cecil.dll')
    shutil.copy2(OFL_SRC, work / 'OFL.txt')

    # 3. 脚本（UTF-8 BOM）
    for name in ('install.ps1', 'uninstall.ps1', 'verify_signature.ps1', '诊断.ps1'):
        copy_as_ps1(ROOT / 'packaging' / name, work / name)

    # 4. 收纳在「程序文件」里的批处理
    write_text(work / '验证署名.bat', BAT_VERIFY, 'gbk')
    write_text(work / '安装-仅语言包（不改游戏文件）.bat', BAT_NOLANG, 'gbk')
    write_text(work / '安装-仅署名补丁.bat', BAT_SIGONLY, 'gbk')
    write_text(work / '诊断-黑屏排查.bat', BAT_DIAG, 'gbk')

    # 5. 根目录：只放 3 个一眼能看懂的文件
    write_text(PKG / '① 一键安装汉化.bat', BAT_INSTALL, 'gbk')
    write_text(PKG / '② 卸载还原.bat', BAT_UNINSTALL, 'gbk')
    write_text(PKG / '使用说明.txt', USAGE_TXT, 'gbk')

    # 6. 高级文档
    opt = work / 'optional'
    opt.mkdir(exist_ok=True)
    doc = next((p for p in (ROOT / 'README.md', ROOT / 'docs' / '技术说明.md') if p.exists()), None)
    if doc:
        shutil.copy2(doc, opt / '技术说明.md')
    for name in ('校对对照表.tsv', 'glossary.tsv', '待定术语.md'):
        src = next((p for p in (ROOT / 'translations' / name, ROOT / name) if p.exists()), ROOT / name)
        if src.exists():
            shutil.copy2(src, opt / name)

    # 7. 校验和
    lines = [f'Juno: New Origins 简体中文汉化包 v{VERSION}  文件校验和 (SHA-256)', '']
    for f in sorted(PKG.rglob('*')):
        if f.is_file() and f.name != 'SHA256SUMS.txt':
            lines.append(f'{sha256(f)}  {f.relative_to(PKG).as_posix()}')
    write_text(work / 'SHA256SUMS.txt', '\n'.join(lines) + '\n', 'utf-8')

    # 8. 打包
    zip_path = DIST / f'{PKG_NAME}.zip'
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(PKG.rglob('*')):
            if f.is_file():
                z.write(f, f'{PKG_NAME}/{f.relative_to(PKG).as_posix()}')
    print(f'[打包完成] {zip_path.name}  ({zip_path.stat().st_size/1024/1024:.1f} MB)')

    # 9. 打印根目录样子
    print(f'\n解压后根目录（用户看到的就是这些）:')
    for f in sorted(PKG.iterdir()):
        tag = '  <- 双击这个' if f.name.startswith('①') else ''
        print(f'   {"[目录]" if f.is_dir() else "      "} {f.name}{tag}')


if __name__ == '__main__':
    main()
