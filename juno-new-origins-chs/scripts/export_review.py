# -*- coding: utf-8 -*-
"""
导出全量校对对照表 -> 校对对照表.tsv
列: key <TAB> 英文原文 <TAB> 当前中文 <TAB> 修改列(留空则不覆盖) <TAB> 备注

用 Excel / VSCode / 记事本打开都行(UTF-8 带 BOM, Excel 双击不乱码)。
改完 -> 运行 import_revisions.py 回灌。

用法:
  python export_review.py              # 全部条目
  python export_review.py --module Career   # 只导出某一模块(按 key 前缀)
  python export_review.py --untranslated    # 只导出还没翻译的条目
"""
import json, os, sys, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
EN_XML = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'EN-US', 'Strings.xml')
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')
OUT = os.path.join(ROOT, 'translations', '校对对照表.tsv')

args = sys.argv[1:]
module = None
only_unt = False
if '--module' in args:
    module = args[args.index('--module') + 1]
if '--untranslated' in args:
    only_unt = True

en_items = [(e.get('id'), e.text or '') for e in ET.fromstring(open(EN_XML, encoding='utf-8-sig').read()).findall('s')]
zh = {k: v for k, v in json.load(open(TRANS, encoding='utf-8')).items() if not k.startswith('_')}

rows = []
for i, e in en_items:
    cur = zh.get(i, '')
    if module and not i.startswith(module + '.'):
        continue
    if only_unt and cur:
        continue
    note = '' if cur else '【未翻译】'
    rows.append((i, e, cur, '', note))

with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    f.write('key\t英文原文\t当前中文\t修改列(填这里覆盖)\t备注\n')
    for r in rows:
        f.write('\t'.join(x.replace('\t', ' ').replace('\n', '\\n') for x in r) + '\n')

done = sum(1 for i, _ in en_items if zh.get(i))
print(f'导出 {len(rows)} 行 -> {OUT}')
print(f'当前进度: {done}/{len(en_items)} ({done/len(en_items)*100:.1f}%)')
print('编辑后运行: python import_revisions.py')
