# -*- coding: utf-8 -*-
"""
在语言包内嵌入作者署名（多层，防轻易抹除）
-------------------------------------------------
第 2 层 可见署名 : 设置→通用→语言 标签后追加署名（玩家切语言时必见）
第 3 层 隐形水印 : 在 24 条中文译文中嵌入零宽字符编码的作者签名
                 （U+200B=0 / U+200C=1，肉眼与普通编辑器完全不可见）
第 5 层 文件标记 : Strings.xml / Fonts.xml 顶部 + 语言包目录 SIGNATURE.txt

用法:
  python apply_signature.py            # 预览
  python apply_signature.py --write    # 落盘 + 重建
  python apply_signature.py --detect   # 检测水印（用于证明作者身份）
"""
import json, os, re, sys, xml.etree.ElementTree as ET
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')
EN_XML = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'EN-US', 'Strings.xml')
ZH_DIR = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'ZH-CN')

AUTHOR = 'LyuRinYu'
PAYLOAD = 'LyuRinYu-JNO-CHS'          # 水印内容
ZW0, ZW1 = '\u200b', '\u200c'          # 0 / 1

# 可见署名落点：
#  1) 设置页的"语言"标签（切换语言时必见）
#  2) 主菜单「菜单」按钮展开后的"制作人员"条目（必见，且语义上正是署名位置）
VISIBLE = {
    'Settings.General.Language': f'语言（{AUTHOR} 汉化）',
    'Menu.Credits': f'制作人员 · {AUTHOR}汉化',
}

# 隐形水印落点：分散在不同模块、文本较长的条目（末尾标点前插入）
WM_KEYS = [
    'Career.Contracts.UnrejectDialog.Message', 'Career.Milestones.CompleteMessage',
    'Menu.PreviousCrashDialog.Message', 'Menu.Mods.SelectModMessage',
    'Flight.Inspector.Pid.Tooltip', 'Flight.CraftRecovery.ClosestLocationFormat',
    'Design.PartsList.DeleteSubassembly.Confirmation', 'Design.ToggleFingerAid.Tooltip',
    'Settings.Graphics.Quality.Tooltip', 'Settings.Terrain.PlanetCubemapQuality.Tooltip',
    'Parts.FlightProgramScript.Log', 'Parts.InspectorModel.SpoolTime',
    'PlanetStudio.Validation.Failed', 'PlanetStudio.Structures.VillageTerrace2.Name',
    'Vizzy.Operator.Math.Tooltip.sin', 'Vizzy.Operator.Vector.Tooltip.dot',
    'Tutorial.AddPart.OpenPartList', 'Tutorial.Camera.RotateScroll',
    'Ui.AccountDialog.RequestFailed', 'Ui.AxisCalibrator.RangePrompt',
    'Modifier.Flatten.DisplayName', 'PhotoLibrary.BulkMove.MoveToAlbumPluralFormat',
    'Upload.Craft.Visibility.Unlisted', 'Common.AuthorVersionSubtitle',
]


def to_bits(s):
    return ''.join(f'{b:08b}' for b in s.encode('utf-8'))


def encode_bits(bits):
    return ''.join(ZW1 if b == '1' else ZW0 for b in bits)


def decode_text(s):
    bits = ''.join('1' if c == ZW1 else '0' for c in s if c in (ZW0, ZW1))
    out = bytearray()
    for i in range(0, len(bits) - 7, 8):
        out.append(int(bits[i:i + 8], 2))
    try:
        return out.decode('utf-8')
    except Exception:
        return repr(bytes(out))


def strip_watermark(s):
    return ''.join(c for c in s if c not in (ZW0, ZW1))


def embed(text, bits):
    """在译文最后一个标点前插入不可见水印"""
    wm = encode_bits(bits)
    m = list(re.finditer(r'[。！？.!?]', text))
    if m:
        pos = m[-1].start()
        return text[:pos] + wm + text[pos:]
    return text + wm


def write_ids():
    """要写入水印的 key 列表（只取实际存在的）"""
    zh = json.load(open(TRANS, encoding='utf-8'))
    return [k for k in WM_KEYS if k in zh]


def main():
    if '--detect' in sys.argv:
        zh = json.load(open(TRANS, encoding='utf-8'))
        found = []
        for k, v in zh.items():
            if not isinstance(v, str):
                continue
            if ZW0 in v or ZW1 in v:
                found.append((k, decode_text(v)))
        print(f'检测到水印条目: {len(found)} / 期望 {len(to_bits(PAYLOAD))//8*1 + 0 and len(WM_KEYS)}\n')
        for k, d in found:
            print(f'  {k}\n     解码 = {d!r}')
        if found and all(d.startswith(PAYLOAD) or PAYLOAD.startswith(d) for _, d in found):
            print(f'\n== 水印有效：本语言包由 {AUTHOR} 制作 ==')
        return

    zh = json.load(open(TRANS, encoding='utf-8'))
    bits = to_bits(PAYLOAD)
    changes = {}

    # 第 2 层：可见署名
    for k, v in VISIBLE.items():
        if k in zh and zh[k] != v:
            changes[k] = (zh[k], v)
            zh[k] = v

    # 第 3 层：隐形水印（幂等：先去旧水印再嵌）
    wm_count = 0
    for k in WM_KEYS:
        if k not in zh or not isinstance(zh[k], str):
            continue
        clean = strip_watermark(zh[k])
        new = embed(clean, bits)
        if new != zh[k]:
            changes.setdefault(k, (zh[k], f'{clean[:28]}… + [隐形水印{len(bits)}bit]'))
            zh[k] = new
        wm_count += 1

    print(f'可见署名 {len(VISIBLE)} 处 / 隐形水印 {wm_count} 处（每条 {len(bits)} bit，内容 "{PAYLOAD}"）\n')
    for k, (o, n) in list(changes.items())[:8]:
        print(f'  {k}\n     {o!r}  ->  {n!r}')
    if len(changes) > 8:
        print(f'  ... 其余 {len(changes)-8} 处略')

    if '--write' not in sys.argv:
        print('\n(预览模式，加 --write 落盘)')
        return

    open(TRANS, 'w', encoding='utf-8').write(json.dumps(zh, ensure_ascii=False, indent=1))

    # 第 5 层：语言包目录签名文件
    os.makedirs(ZH_DIR, exist_ok=True)
    sig = (
        f'简体中文语言包 —— 作者：{AUTHOR}\n'
        f'Chinese (Simplified) localization pack by {AUTHOR}\n'
        f'\n'
        f'构建日期: {date.today().isoformat()}\n'
        f'条目数: 9318 / 9318 (100%)\n'
        f'翻译源: Juno: New Origins (SimpleRockets 2) EN-US Strings.xml\n'
        f'\n'
        f'本语言包由 {AUTHOR} 制作，遵循游戏官方多语言机制：\n'
        f'  语言目录  %LOCALAPPDATA%Low\\Jundroo\\SimpleRockets 2\\Languages\\ZH-CN\\\n'
        f'  文件组成  Strings.xml + Fonts.xml + SimHei.ttf\n'
        f'\n'
        f'署名信息分布于：\n'
        f'  1) 主菜单版本号（游戏程序内）\n'
        f'  2) 设置 → 通用 → 语言 标签\n'
        f'  3) 多条译文内嵌的零宽字符水印（不可见）\n'
        f'  4) 字体文件的 name 表元数据\n'
        f'  5) Strings.xml / Fonts.xml 文件头\n'
        f'\n'
        f'移除或篡改上述署名后再分发，属于对本作品的剽窃。\n'
        f'Author signature embedded in multiple layers; removing them to redistribute\n'
        f'this translation without credit is plagiarism.\n'
    )
    open(os.path.join(ZH_DIR, 'SIGNATURE.txt'), 'w', encoding='utf-8').write(sig)
    print(f'\n已写入 {TRANS} 与 {os.path.join(ZH_DIR, "SIGNATURE.txt")}')

    import subprocess
    sys.exit(subprocess.run([sys.executable, os.path.join(HERE, 'build_zh_cn.py')], cwd=HERE).returncode)


if __name__ == '__main__':
    main()
