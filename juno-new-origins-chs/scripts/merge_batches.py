# -*- coding: utf-8 -*-
"""
合并所有批次译文到 translations\\zh_cn.json (已有译文不覆盖), 然后构建语言包。
用法: python merge_batches.py [--check]
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
BATCH_DIR = os.path.join(ROOT, 'batches')
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')

data = json.load(open(TRANS, encoding='utf-8'))
merged_total = 0
for f in sorted(os.listdir(BATCH_DIR)):
    if not f.endswith('.zh.json'):
        continue
    p = os.path.join(BATCH_DIR, f)
    try:
        add = json.load(open(p, encoding='utf-8'))
    except Exception as ex:
        print(f'  !! {f} 读取失败: {ex}')
        continue
    new = {k: v for k, v in add.items() if not k.startswith('_') and k not in data}
    data.update(new)
    merged_total += len(new)
    print(f'  {f}: {len(add)} 条 (新增 {len(new)})')

out = dict(data)
open(TRANS, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print(f'\n合并完成: 新增 {merged_total}, 总计 {len([k for k in out if not k.startswith("_")])} 条')
