# -*- coding: utf-8 -*-
"""
一键还原：把打过署名补丁的游戏 dll 还原为原始文件

用法:
  python restore_dll.py                     # 自动查找游戏目录
  python restore_dll.py --game-dir "<路径>"  # 手动指定游戏目录(含 SimpleRockets2_Data 的那一层)
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None


def find_game_dll(hint=None):
    """按 提示路径 -> 脚本就近目录 -> 各盘常见 Steam 路径 依次查找"""
    cands = []
    if hint:
        cands.append(Path(hint))
    p = Path(__file__).resolve().parent
    for _ in range(5):
        cands += [p, p / 'game']
        p = p.parent
    for d in 'CDEFGH':
        root = Path(f'{d}:/')
        for sub in (r'Program Files (x86)\Steam\steamapps\common\Juno New Origins',
                    r'SteamLibrary\steamapps\common\Juno New Origins',
                    r'Steam\steamapps\common\Juno New Origins',
                    r'Games\Juno New Origins',
                    r'Juno New Origins'):
            cands.append(root / sub)
    for c in cands:
        dll = c / 'SimpleRockets2_Data' / 'Managed' / 'SimpleRockets2.dll'
        if dll.exists():
            return dll
    return None


def main():
    ap = argparse.ArgumentParser(description='还原被补丁的 Juno: New Origins 游戏文件')
    ap.add_argument('--game-dir', default=None, help='游戏目录（含 SimpleRockets2_Data 的那一层）')
    args = ap.parse_args()

    dll = find_game_dll(args.game_dir)
    if not dll:
        print('未找到游戏目录。请用 --game-dir "<游戏目录>" 指定。')
        sys.exit(1)
    print(f'游戏 dll: {dll}')

    targets = [dll, dll.parent.parent / 'resources.assets']
    done = 0
    for t in targets:
        bak = t.with_suffix(t.suffix + '.orig')
        if not bak.exists():
            print(f'  跳过 {t.name}：没有 .orig 备份（说明未打过补丁）')
            continue
        cur, org = sha(t), sha(bak)
        if cur == org:
            print(f'  {t.name} 已是原始文件（sha {cur}）')
            continue
        t.write_bytes(bak.read_bytes())
        ok = sha(t) == org
        print(f'  已还原 {t.name}  校验: {"一致 ✓" if ok else "不一致 ✗"}')
        done += ok

    print(f'\n完成，还原 {done} 个文件。' if done else '\n无需还原（都是原始文件）。')


if __name__ == '__main__':
    main()
