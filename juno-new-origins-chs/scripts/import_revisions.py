# -*- coding: utf-8 -*-
"""
回灌: 读取 校对对照表.tsv, 把「修改列」里有内容的值覆盖到 translations\\zh_cn.json
然后自动校验 + 重建语言包。

用法:
  python import_revisions.py            # 回灌 + 校验 + 重建
  python import_revisions.py --dry-run  # 只看会改什么, 不落盘
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
TSV = os.path.join(ROOT, 'translations', '校对对照表.tsv')
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')

if not os.path.exists(TSV):
    print(f'找不到 {TSV}，请先运行 python export_review.py')
    sys.exit(1)

dry = '--dry-run' in sys.argv
data = json.load(open(TRANS, encoding='utf-8'))
changed, added = [], []

with open(TSV, encoding='utf-8-sig') as f:
    header = f.readline()
    for line in f:
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 4:
            continue
        key, en, cur, rev = parts[0], parts[1], parts[2], parts[3]
        if not key or not rev.strip():
            continue
        rev = rev.replace('\\n', '\\n')
        if key not in data:
            added.append(key)
        elif data[key] != rev:
            changed.append((key, data[key], rev))
        data[key] = rev

print(f'共读取修改 {len(changed) + len(added)} 条 (改动 {len(changed)}, 新增 {len(added)})')
for k, o, n in changed[:15]:
    print(f'  {k}\n    旧: {o}\n    新: {n}')
if len(changed) > 15:
    print(f'  ... 其余 {len(changed)-15} 条略')

if dry:
    print('\n--dry-run: 未写入任何文件')
    sys.exit(0)

open(TRANS, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
print(f'\n已写回 {TRANS}')

# 自动走一遍构建(内含强校验, 校验不过会报错退出)
import subprocess
r = subprocess.run([sys.executable, os.path.join(HERE, 'build_zh_cn.py')], cwd=HERE)
sys.exit(r.returncode)
