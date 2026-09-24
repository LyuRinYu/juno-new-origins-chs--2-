# -*- coding: utf-8 -*-
"""
Juno: New Origins (SimpleRockets 2) 简体中文语言包 构建脚本
------------------------------------------------------------
流程:
  1. 读取游戏英文源 %LocalLow%\\Jundroo\\SimpleRockets 2\\Languages\\EN-US\\Strings.xml
  2. 读取 translations\\zh_cn.json 中累积的 id->中文 映射
  3. 用 checklib 强校验(占位符/@记号/plural分支/结构字符/裸&)
  4. 生成 ZH-CN\\Strings.xml + Fonts.xml 并安装到游戏语言目录

用法:
  python build_zh_cn.py            # 校验 + 构建 + 安装
  python build_zh_cn.py --check    # 只校验不安装
"""
import json, os, re, sys, shutil, xml.etree.ElementTree as ET
from html import unescape
from xml.sax.saxutils import escape as xml_escape

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
sys.path.insert(0, HERE)
from checklib import check_pair

HOME = os.path.expanduser('~')
GAME_LANG_DIR = os.path.join(HOME, 'AppData', 'LocalLow', 'Jundroo', 'SimpleRockets 2', 'Languages')
EN_XML = os.path.join(GAME_LANG_DIR, 'EN-US', 'Strings.xml')
ZH_DIR = os.path.join(GAME_LANG_DIR, 'ZH-CN')
TRANS_JSON = os.path.join(ROOT, 'translations', 'zh_cn.json')

FONT_ID = 'ZH-Sans'
FONT_FILE = 'JNOSansSC-Regular.ttf'          # 由 prepare_font.py 生成（OFL 许可，可自由署名）
FONT_FALLBACK_FILE = 'SimHei.ttf'
DEFAULT_FONT_SRC = r'C:\Windows\Fonts\simhei.ttf'


def load_en(path):
    root = ET.fromstring(open(path, encoding='utf-8-sig').read())
    order, vals = [], {}
    for el in root.findall('s'):
        i = el.get('id')
        if i is None:
            continue
        order.append(i)
        vals[i] = el.text or ''
    return order, vals


def load_zh(path):
    data = json.load(open(path, encoding='utf-8'))
    return {k: v for k, v in data.items() if not k.startswith('_')}


def check(en_vals, zh):
    errors, warns = [], []
    for i, z in zh.items():
        if i not in en_vals:
            errors.append(f'[未知 id] {i}  (英文源中不存在, 会被游戏忽略)')
            continue
        for msg in check_pair(en_vals[i], z):
            errors.append(f'[{msg}] {i}')
        e = unescape(en_vals[i])
        if isinstance(z, str) and unescape(z) == e and re.search(r'[a-z]{2,}', e):
            warns.append(f'[未翻译?] {i} = {e!r}')
    return errors, warns


def build(zh, en_order):
    """按英文源顺序生成 XML。id 与译文都做属性/文本转义, 保证输出 XML 恒合法。
    注意: 英文源里存在含空格与 & 的 id (如 'Design.PartsList.Category.Control & Descent.Name'),
    因此 id 必须转义, 否则整个 Strings.xml 非法、游戏直接读不到语言包。"""
    # 注意：XML 注释中不允许出现连续两个连字符（--），否则整个文件非法。
    # 早前的版本在这里写了命令行参数 --detect，导致 Strings.xml 变成非法 XML —— 
    # 严格解析器会拒绝整份语言包（表现为游戏加载语言包失败、黑屏）。
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<Strings>',
             '   <!-- 简体中文语言包 (ZH-CN) · 作者 LyuRinYu',
             '        Chinese (Simplified) localization pack by LyuRinYu',
             '        基于游戏官方多语言机制; 译文内含不可见零宽字符水印,',
             '        可用 apply_signature.py 的 detect 参数验证作者身份。',
             '        移除署名后再次分发属于剽窃。请勿手工编辑本文件。 -->']
    for i in en_order:
        if i in zh:
            safe_id = xml_escape(i, {'"': '&quot;'})
            safe_val = xml_escape(unescape(zh[i]), {"'": "&apos;"})
            lines.append(f'   <s id="{safe_id}">{safe_val}</s>')
    lines.append('</Strings>')
    return '\n'.join(lines) + '\n'


def install(xml_text, zh_count, en_count):
    os.makedirs(ZH_DIR, exist_ok=True)
    dst_font = os.path.join(ZH_DIR, FONT_FILE)
    if not os.path.exists(dst_font):
        fb = os.path.join(ZH_DIR, FONT_FALLBACK_FILE)
        if not os.path.exists(fb) and os.path.exists(DEFAULT_FONT_SRC):
            shutil.copy2(DEFAULT_FONT_SRC, fb)
        if os.path.exists(fb):
            print(f'  [字体] 未找到 {FONT_FILE}，本次用回退字体 {FONT_FALLBACK_FILE}'
                  f'（建议先运行 python prepare_font.py）')
            dst_font = fb
        else:
            print(f'  [字体] 警告: 无可用字体，请运行 python prepare_font.py')
    font_name = os.path.basename(dst_font)
    # Fonts.xml 一律不带注释：避免任何编码/解析歧义。
    # samplingPointSize 决定每个字形在图集里占多大 —— 48 + padding 6 时
    # 2048x2048 图集约可容纳 1160 个字形（60 时只有约 800，容易触发「图集已满」）。
    fonts_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Fonts>\n'
        f'  <Font id="{FONT_ID}" file="{font_name}" atlasPopulationMode="Dynamic" '
        'atlasResolution="2048,2048" samplingPointSize="48" padding="6" />\n'
        '</Fonts>\n'
    )
    open(os.path.join(ZH_DIR, 'Fonts.xml'), 'w', encoding='utf-8').write(fonts_xml)
    out = os.path.join(ZH_DIR, 'Strings.xml')
    open(out, 'w', encoding='utf-8').write(xml_text)
    ET.fromstring(open(out, encoding='utf-8').read())  # XML 合法性
    pct = zh_count / en_count * 100
    print(f'  [安装] {out}  ({zh_count}/{en_count} 条, 覆盖率 {pct:.1f}%)')


def main():
    check_only = '--check' in sys.argv
    en_order, en_vals = load_en(EN_XML)
    zh = load_zh(TRANS_JSON)
    print(f'英文源条目: {len(en_order)}   中文译文: {len(zh)}')
    errors, warns = check(en_vals, zh)
    if warns:
        print(f'\n-- 警告 ({len(warns)}) --')
        for w in warns[:20]:
            print('  ' + w)
        if len(warns) > 20:
            print(f'  ... 其余 {len(warns)-20} 条略')
    if errors:
        print(f'\n!! 校验失败, 共 {len(errors)} 个错误 !!')
        for e in errors[:60]:
            print('  ' + e)
        if len(errors) > 60:
            print(f'  ... 其余 {len(errors)-60} 个略')
        sys.exit(1)
    print('\n[OK] 占位符/@记号/plural分支/结构字符 校验全部通过')
    if check_only:
        return
    install(build(zh, en_order), len(zh), len(en_order))
    print('\n完成。启动游戏 -> 设置 -> 通用 -> 语言 -> 选择 ZH-CN 即可。')


if __name__ == '__main__':
    main()
