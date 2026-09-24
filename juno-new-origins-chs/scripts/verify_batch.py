# -*- coding: utf-8 -*-
"""
校验单个/多个批次译文文件
用法: python verify_batch.py batches\batch_01.zh.json [more.json...]
退出码 0=通过, 1=有错误
"""
import json, os, sys, xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from checklib import check_pair

EN_XML = os.path.join(os.path.expanduser('~'), 'AppData', 'LocalLow', 'Jundroo',
                      'SimpleRockets 2', 'Languages', 'EN-US', 'Strings.xml')
en = {e.get('id'): (e.text or '') for e in ET.fromstring(open(EN_XML, encoding='utf-8-sig').read()).findall('s')}


def verify(path):
    zh = json.load(open(path, encoding='utf-8'))
    errors = []
    for i, z in zh.items():
        if i not in en:
            errors.append(f'[未知 id] {i}')
            continue
        for msg in check_pair(en[i], z):
            errors.append(f'[{msg}] {i}')
    return len(zh), errors


if __name__ == '__main__':
    total_err = 0
    for p in sys.argv[1:]:
        n, errs = verify(p)
        print(f'{os.path.basename(p)}: {n} 条, {len(errs)} 个错误')
        for e in errs[:40]:
            print('   ' + e)
        if len(errs) > 40:
            print(f'   ... 其余 {len(errs)-40} 个略')
        total_err += len(errs)
    print('== 全部通过 ==' if total_err == 0 else f'== 共 {total_err} 个错误 ==')
    sys.exit(0 if total_err == 0 else 1)
