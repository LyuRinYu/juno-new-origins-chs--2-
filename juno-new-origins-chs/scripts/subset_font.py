# -*- coding: utf-8 -*-
"""
字体子集化：把中文字体裁剪到「游戏实际需要的字符 + GB2312 常用字」

为什么必须做：
  原始 Noto Sans SC 含 31036 个字形 / 30890 个字符映射。TextMeshPro 加载时
  要为这些字符建查找表，并在 Dynamic 模式下往图集里塞字形 —— 2048x2048 图集
  在 60px 采样下大约只容得下 800 个字形。字形规模过大是「字体加载失败 / 图集
  溢出 / 内存分配失败」进而黑屏的主要嫌疑。

保留范围（宁可多留，避免玩家自己输入的名字变方框）：
  · GB2312 全集 6763 字（覆盖日常输入的一级+二级汉字）
  · 译文与键里出现过的所有字符（含超纲符号）
  · ASCII 可打印字符
  · 常用中文标点与符号

用法:
  python subset_font.py <源字体.ttf> <输出.ttf> [--reference-json translations/zh_cn.json]
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
from fontTools import subset
from fontTools.ttLib import TTFont

PUNCT = ('　、。，！？；：“”‘’（）〔〕《》〈〉【】—…·～￥×÷±°′″←→↑↓'
         '●○■□★☆◆◇▲▼■①②③④⑤⑥⑦⑧⑨⑩§№℃‰∞≈≠≤≥∑√⊥∥∠⊙')
SYMBOLS = ''.join(chr(c) for c in range(0x20, 0x7F))


def build_charset(reference_json: Path):
    gb = set()
    for hi in range(0xB0, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                gb.add(bytes([hi, lo]).decode('gb2312'))
            except Exception:
                pass
    txt = set()
    if reference_json and reference_json.exists():
        data = json.loads(reference_json.read_text(encoding='utf-8'))
        for k, v in data.items():
            txt |= set(v) | set(k)
    # 零宽水印字符也要保留（否则水印字形缺失）
    txt |= {'\u200b', '\u200c', '\u200d', '\ufeff'}
    return gb | txt | set(SYMBOLS) | set(PUNCT), len(gb), len(txt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--reference-json', default='translations/zh_cn.json')
    a = ap.parse_args()

    src, dst = Path(a.src), Path(a.dst)
    chars, ngb, ntxt = build_charset(Path(a.reference_json))
    print(f'[字符集] GB2312 {ngb} 字 + 译文/键 {ntxt} 字符 → 合计 {len(chars)} 个唯一字符')
    print(f'[源字体] {src.name}  {src.stat().st_size/1024/1024:.2f} MB')

    before = TTFont(src, lazy=True)
    n_before = before['maxp'].numGlyphs
    cmap_before = len(before.getBestCmap())
    before.close()

    opts = subset.Options()
    opts.layout_features = ['*']          # 保留 GPOS/GSUB 排版特性
    opts.name_IDs = ['*']                 # 保留全部 name 记录（含作者署名）
    opts.name_legacy = True
    opts.name_languages = ['*']
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.recalc_timestamp = False         # 保持确定性
    opts.drop_tables += ['vhea', 'vmtx', 'VORG']   # 竖排表，游戏用不到
    opts.desubroutinize = True

    font = subset.load_font(str(src), opts, lazy=False)
    ss = subset.Subsetter(options=opts)
    ss.populate(unicodes=[ord(c) for c in chars])
    ss.subset(font)
    subset.save_font(font, str(dst), opts)

    after = TTFont(dst, lazy=True)
    n_after = after['maxp'].numGlyphs
    cmap_after = len(after.getBestCmap())
    names = after['name']
    sig = [r for r in names.names if 'LyuRinYu' in str(r.toUnicode())]
    after.close()

    print(f'[输出]   {dst.name}  {dst.stat().st_size/1024/1024:.2f} MB')
    print(f'  字形数: {n_before} → {n_after}  (减少 {(1-n_after/n_before)*100:.0f}%)')
    print(f'  字符映射: {cmap_before} → {cmap_after}')
    print(f'  体积: {src.stat().st_size/1024/1024:.2f} MB → {dst.stat().st_size/1024/1024:.2f} MB')
    print(f'  name 表署名记录: {len(sig)} 条' + ('  ✓ 保留' if sig else '  ✗ 丢失!'))

    # 抽样校验：译文里每个字符都必须能映射到字形
    miss = [c for c in chars if ord(c) > 0x1F and ord(c) not in TTFont(dst, lazy=True).getBestCmap()]
    print(f'  字符覆盖校验: {"全部命中 ✓" if not miss else "缺失 " + str(len(miss)) + " 个: " + "".join(miss[:30])}')


if __name__ == '__main__':
    main()
