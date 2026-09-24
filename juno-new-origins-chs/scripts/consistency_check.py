# -*- coding: utf-8 -*-
"""
术语一致性 + 漏译扫描
多译手并行翻译最大的风险是同一个词被译成不同说法(如 Crew 被译成"机组"/"乘员"),
本工具扫全量译文, 输出报告 + 可直接编辑的修正表。

用法:
  python consistency_check.py            # 打印报告
  python consistency_check.py --tsv      # 同时导出 术语修正候选.tsv(只含问题条目)
"""
import json, os, re, sys, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
EN_XML = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'EN-US', 'Strings.xml')
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')
OUT_TSV = os.path.join(ROOT, 'translations', '术语修正候选.tsv')

# (禁止的变体, 建议标准译法, 原因)
VARIANT_RULES = [
    ('机组', '乘员', 'Crew 统一译「乘员」'),
    ('组员', '乘员', 'Crew 统一译「乘员」'),
    ('宇航员组', '乘员', 'Crew 统一译「乘员」'),
    ('着陆腿', '起落架', 'Landing Gear 统一译「起落架」'),
    ('远地点', '远拱点', 'Apoapsis 统一译「远拱点」'),
    ('近地点', '近拱点', 'Periapsis 统一译「近拱点」'),
    ('操作节点', '机动节点', 'Maneuver Node 统一译「机动节点」'),
    ('航天器', '载具', 'Craft 统一译「载具」'),
    ('飞行器', '载具', 'Craft 统一译「载具」（除非原文为 Aircraft）'),
    ('太空船', '载具', 'Craft 统一译「载具」'),
    ('模组包', '模组', 'Mod 统一译「模组」'),
    ('插件', '模组', 'Mod 统一译「模组」'),
    ('缩略图', '缩略图', '仅供参考'),  # 占位示例
    ('大气制动', '气动减速', 'aero braking 统一译「气动减速」'),
    ('时间加速', '时间加速', '占位'),
]

# 允许保留的英文/缩写白名单(误报过滤)
WHITELIST = set("""FPS CPU GPU RAM MS OS ISP RCS SAS TP RTG HUD VAB SPH NaN
Vizzy Juno Droo Cylero Tydos Urados Nebra Luna Herma Jastrus Brigo Boreas Cladh
Handrews Drood Roboto Pirulen Nexus Cross Riptide Soyuz Vortex Komodo Vroz
Delta-V Delta SpaceX Steam Jundroo SimpleRockets Mod Mods OK UI ID
Alpha Bravo Charlie Delta Echo Foxtrot Golf Hotel India Juliet Kilo Lima
Mike November Oscar Papa Quebec Romeo Sierra Tango Uniform Victor Whiskey
Xray Yankee Zulu""".split())

en = {e.get('id'): (e.text or '') for e in ET.fromstring(open(EN_XML, encoding='utf-8-sig').read()).findall('s')}
zh = {k: v for k, v in json.load(open(TRANS, encoding='utf-8')).items() if not k.startswith('_')}

variant_hits, untranslated, semi = [], [], []

for i, z in zh.items():
    if not isinstance(z, str):
        continue
    e = en.get(i, '')
    # 1. 术语变体
    for bad, good, why in VARIANT_RULES:
        if bad in z and bad != good:
            variant_hits.append((i, bad, good, z, e))
    # 2. 完全未翻译(非纯记号/专名)
    if z == e and re.search(r'[a-z]{2,}', e) and not e.startswith('@'):
        # 单个大写开头的单词视为专名(行星名/公司名等), 属设计意图, 不计入
        if not re.fullmatch(r'[A-Z][A-Za-z0-9\'\-]*( [A-Z][A-Za-z0-9\'\-]*)*', e.strip()):
            untranslated.append((i, e))
    # 3. 半翻译: 中文字很少而英文单词多
    else:
        cjk = len(re.findall(r'[\u4e00-\u9fff]', z))
        words = [w for w in re.findall(r'[A-Za-z][A-Za-z0-9\-\+]{2,}', z) if w not in WHITELIST]
        if cjk and len(words) >= 4 and len(words) > cjk / 3:
            semi.append((i, z, e))

print(f'译文总数: {len(zh)}')
print(f'\n=== ① 术语变体 {len(variant_hits)} 处 ===')
seen = {}
for i, bad, good, z, e in variant_hits:
    seen.setdefault((bad, good), []).append(i)
for (bad, good), ids in sorted(seen.items(), key=lambda x: -len(x[1])):
    print(f'  「{bad}」→ 建议「{good}」  共 {len(ids)} 条   例: {ids[0]}')
    print(f'       现译: {zh[ids[0]][:70]}')

print(f'\n=== ② 完全未翻译 {len(untranslated)} 条 ===')
for i, e in untranslated[:15]:
    print(f'  {i} = {e[:70]}')

print(f'\n=== ③ 疑似半翻译 {len(semi)} 条 ===')
for i, z, e in semi[:15]:
    print(f'  {i}\n     英文: {e[:70]}\n     中文: {z[:70]}')

if '--tsv' in sys.argv:
    with open(OUT_TSV, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('key\t英文原文\t当前中文\t修改列(填这里覆盖)\t问题\n')
        for i, bad, good, z, e in variant_hits:
            f.write(f'{i}\t{e}\t{z}\t\t术语变体: 「{bad}」应为「{good}」\n')
        for i, e in untranslated:
            f.write(f'{i}\t{e}\t\t\t未翻译\n')
        for i, z, e in semi:
            f.write(f'{i}\t{e}\t{z}\t\t疑似半翻译\n')
    print(f'\n已导出 {OUT_TSV}（编辑后运行 python import_revisions.py 回灌）')
