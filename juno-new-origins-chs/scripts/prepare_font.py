# -*- coding: utf-8 -*-
"""
准备语言包字体：把系统里的 Noto Sans SC 可变字体实例化为静态 Regular，
重命名为中性字体名（避开 OFL 保留字体名条款），并在 name 表写入作者署名。
OFL 许可允许修改与再分发，原始版权声明保留。

用法:
  python prepare_font.py          # 生成并署名
  python prepare_font.py --show   # 读回显示
"""
import os, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
AUTHOR = 'LyuRinYu'
SRC = r'C:\Windows\Fonts\NotoSansSC-VF.ttf'
ZH_DIR = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'ZH-CN')
OUT = os.path.join(ZH_DIR, 'JNOSansSC-Regular.ttf')
FAMILY = 'JNO Sans SC'

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

EN_NOTE = f'Chinese (Simplified) localization pack for Juno: New Origins, by {AUTHOR}'
CN_NOTE = f'简体中文语言包作者：{AUTHOR}（Juno: New Origins 汉化）'


def read_name(font, nid):
    for rec in font['name'].names:
        if rec.nameID == nid:
            try:
                return rec.toUnicode()
            except Exception:
                pass
    return ''


def main():
    if '--show' in sys.argv:
        f = TTFont(OUT, lazy=False)
        for nid in (0, 1, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 16):
            print(f'  [{nid:2d}] = {read_name(f, nid)[:100]!r}')
        return

    if not os.path.exists(SRC):
        print(f'找不到源字体 {SRC}')
        sys.exit(1)

    os.makedirs(ZH_DIR, exist_ok=True)
    f = TTFont(SRC, lazy=False)
    inst = instancer.instantiateVariableFont(f, {'wght': 400}, inplace=False, updateFontNames=True)
    name = inst['name']

    # 原始版权与 OFL 许可说明保留（OFL 要求）；仅在其它字段追加 / 新增署名
    orig_copyright = read_name(inst, 0)
    orig_license = read_name(inst, 13)

    plan = {
        # nid: (Windows 文本(UTF-16，可含中文), Mac 文本(ASCII))
        0: ((orig_copyright + f' | Modified instance + metadata by {AUTHOR}').strip(' |'), orig_copyright),
        1: (FAMILY, FAMILY),                          # 中性名（避开 OFL 保留字体名）
        2: ('Regular', 'Regular'),
        3: (f'{FAMILY};{AUTHOR}-JNO-CHS;2026', f'{FAMILY};{AUTHOR}-JNO-CHS;2026'),
        4: (f'{FAMILY} Regular', f'{FAMILY} Regular'),
        5: (f'Version 1.000; {AUTHOR} JNO-CHS pack', f'Version 1.000; {AUTHOR} JNO-CHS pack'),
        6: ('JNOSansSC-Regular', 'JNOSansSC-Regular'),
        8: (f'汉化打包：{AUTHOR}', f'Packed by {AUTHOR}'),
        9: (f'{AUTHOR} (Chinese localization)', f'{AUTHOR} (Chinese localization)'),
        10: (f'{EN_NOTE}. {CN_NOTE}. 9318/9318 strings translated. Based on Noto Sans SC (OFL).', EN_NOTE),
        11: (f'{AUTHOR}/JNO-CHS', f'{AUTHOR}/JNO-CHS'),
        13: (orig_license, orig_license),
        16: (FAMILY, FAMILY),
        17: ('Regular', 'Regular'),
    }
    for nid, (win_text, mac_text) in plan.items():
        if not win_text:
            continue
        recs = [r for r in name.names if r.nameID == nid]
        if not recs:
            name.setName(win_text, nid, 3, 1, 0x409)
            name.setName(mac_text[:255], nid, 1, 0, 0)
            continue
        for rec in recs:
            # Windows 记录(UTF-16)承载中文署名; Mac 记录用 ASCII 等价文本
            rec.string = win_text if rec.platformID == 3 else mac_text

    inst.save(OUT)
    print(f'已生成 {OUT}  ({os.path.getsize(OUT)/1024/1024:.1f} MB)')

    v = TTFont(OUT, lazy=False)
    print('回读验证:', '通过 ✓' if AUTHOR in read_name(v, 3) and read_name(v, 1) == FAMILY else '失败 ✗')
    for nid in (0, 1, 3, 5, 8, 9, 10, 11):
        print(f'  [{nid:2d}] = {read_name(v, nid)[:95]!r}')
    print('\n原始 Noto 版权声明（保留）:', orig_copyright[:80])
    print('OFL 许可说明（保留）:', orig_license[:70], '...')


if __name__ == '__main__':
    main()
