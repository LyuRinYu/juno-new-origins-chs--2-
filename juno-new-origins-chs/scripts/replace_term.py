# -*- coding: utf-8 -*-
"""
术语批量替换工具 —— 改一个统一译法, 全量译文同步更新并重建语言包。

用法:
  python replace_term.py 载具 飞行器            # 预览会改多少条(默认不落盘)
  python replace_term.py 载具 飞行器 --write    # 确认替换 + 重建语言包
  python replace_term.py 载具 飞行器 --count    # 只数条数

注意: 只替换译文, 不动英文源; 占位符/标记不受影响(它们不含中文词)。
"""
import json, os, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
# 数据根：脚本位于 scripts/ 子目录时取上一级，否则与脚本同级（两种布局通用）
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == 'scripts' else HERE
TRANS = os.path.join(ROOT, 'translations', 'zh_cn.json')

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) != 2:
    print(__doc__)
    sys.exit(1)
old, new = args
write = '--write' in sys.argv

data = json.load(open(TRANS, encoding='utf-8'))
hits = [(k, v) for k, v in data.items() if not k.startswith('_') and isinstance(v, str) and old in v]
print(f'含「{old}」的条目: {len(hits)} 条')
for k, v in hits[:20]:
    print(f'  {k}\n    {v}\n -> {v.replace(old, new)}')
if len(hits) > 20:
    print(f'  ... 其余 {len(hits)-20} 条略')

if '--count' in sys.argv or not write:
    print('\n(预览模式, 加 --write 才会真正替换并重建)')
    sys.exit(0)

for k, _ in hits:
    data[k] = data[k].replace(old, new)
open(TRANS, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=1))
print(f'\n已替换 {len(hits)} 条 -> {TRANS}')

import subprocess
r = subprocess.run([sys.executable, os.path.join(HERE, 'build_zh_cn.py')], cwd=HERE)
sys.exit(r.returncode)
