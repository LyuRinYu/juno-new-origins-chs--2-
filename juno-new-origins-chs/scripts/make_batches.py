# -*- coding: utf-8 -*-
"""
把 EN-US 全量条目切成可并行翻译的批次 (每批 ≤ BATCH_SIZE 条)
排除已翻译的条目, 输出到 batches\\batch_XX.json  (格式: {"id": "英文", ...})
"""
import json, os, sys, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
HOME = os.path.expanduser('~')
EN_XML = os.path.join(HOME, 'AppData', 'LocalLow', 'Jundroo', 'SimpleRockets 2', 'Languages', 'EN-US', 'Strings.xml')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
OUT = os.path.join(ROOT, 'batches')
BATCH_SIZE = 450

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith('.json'):
        os.remove(os.path.join(OUT, f))

root = ET.fromstring(open(EN_XML, encoding='utf-8-sig').read())
items = [(e.get('id'), e.text or '') for e in root.findall('s')]

done = set()
tpath = os.path.join(ROOT, 'translations', 'zh_cn.json')
if os.path.exists(tpath):
    done = {k for k in json.load(open(tpath, encoding='utf-8')) if not k.startswith('_')}
print(f'英文源 {len(items)} 条, 已翻译 {len(done)} 条')

todo = [(i, v) for i, v in items if i not in done]
print(f'待翻译 {len(todo)} 条')

batches = [todo[i:i + BATCH_SIZE] for i in range(0, len(todo), BATCH_SIZE)]
for n, b in enumerate(batches, 1):
    p = os.path.join(OUT, f'batch_{n:02d}.json')
    json.dump(dict(b), open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    prefixes = sorted({k.split('.')[0] for k, _ in b})
    print(f'  batch_{n:02d}.json  {len(b):4d} 条   模块: {", ".join(prefixes[:6])}{"..." if len(prefixes) > 6 else ""}')
print(f'\n共 {len(batches)} 个批次 -> {OUT}')
