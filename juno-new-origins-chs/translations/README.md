# 译文数据

## 文件

| 文件 | 说明 |
|---|---|
| `zh_cn.json` | **唯一权威数据源**：`{ "键": "中文译文" }`，9318 条 |
| `glossary.tsv` | 术语表：`英文<TAB>统一译法<TAB>说明` |
| `校对对照表.tsv` | 全量中英对照表，Excel 可直接打开 |

## 为什么未翻译项不用管

游戏按 key 查表，查不到会自动回落英文。所以：

- **缺少**某些 key → 游戏里显示英文，不会出错
- **多出**某些 key → 游戏直接忽略，不会出错

因此译文数据天然支持**渐进式汉化**与**跨游戏版本兼容**。

## 修改流程

```bash
# 方式一：改单个术语（全局替换 + 自动重建）
python scripts/replace_term.py 载具 飞行器          # 预览
python scripts/replace_term.py 载具 飞行器 --write  # 执行

# 方式二：逐条精修
python scripts/export_review.py                    # 生成 校对对照表.tsv
#   编辑「修改列」后：
python scripts/import_revisions.py                 # 回灌 + 校验 + 重建

# 方式三：直接编辑 zh_cn.json，然后
python scripts/build_zh_cn.py
```

改完**务必**跑一次 `python scripts/build_zh_cn.py --check`，确认格式校验通过。
