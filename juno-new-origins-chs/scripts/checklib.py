# -*- coding: utf-8 -*-
"""
共用校验核心 —— 保证译文不会破坏游戏的文本格式系统
校验维度:
  1. {0} {1} {0:n1} 等 string.Format 占位符  (必须完全一致)
  2. @Token / @Token:format / @Token:plural(a|b) 游戏自定义记号
     - 记号名与格式名必须一致
     - plural(...) 的分支数(| 分隔)必须一致; 括号内的词是可译文本
  3. %Token% 另一种记号
  4. 结构字符: 尖括号(富文本标记 <color> <br> <size>)、真换行(@&#10;)、字面 \\n
  5. 非法裸 & (会让 XML 非法)
"""
import re
from html import unescape

PLACEHOLDER_RE = re.compile(r'\{[^{}]*\}')
AT_TOKEN_RE = re.compile(r'@[A-Za-z][A-Za-z0-9]*(?::[A-Za-z]+(?:\([^()]*\))?)?')
PCT_TOKEN_RE = re.compile(r'%[A-Za-z][A-Za-z0-9]*%')
# |键位绑定/引用| 记号: 教程里显示为按键提示(如 |Brake;+|), 或 Vizzy 变量引用(|Vizzy.EventVariable.Part|)
# 内容必须整体原样保留 —— 译错会导致教程按键提示失效
PIPE_TOKEN_RE = re.compile(r'\|[^|\[\]\n]{1,60}\|')
# Vizzy 参数类型标注 (0:Number) (1:OneOrMore) 等 —— 插槽序号与类型名必须原样
PAREN_TOKEN_RE = re.compile(r'\(\d+:[A-Za-z][A-Za-z0-9]*\)')
ILLEGAL_AMP_RE = re.compile(r'&(?!#\d+;|#x[0-9a-fA-F]+;|[a-zA-Z]+;)')


def struct(s):
    """结构字符计数。方括号计入: [highlight] / [b] / [i] 等富文本标记漏掉会导致显示异常。"""
    return {
        'lt': s.count('<'),
        'gt': s.count('>'),
        'lb': s.count('['),
        'rb': s.count(']'),
        'nl': s.count('\n'),
        'esc_nl': s.count('\\n'),
    }


# 方括号组: [highlight] / [/highlight] / [b] 等是富文本标记(必须原样);
# [clicking|tapping] 是"鼠标端|触屏端"双端文本记号(内含 |, 内容可译, 只需分支数一致)
BRACKET_RE = re.compile(r'\[[^\[\]\n]{0,80}\]')


def bracket_sig(s):
    out = []
    for m in BRACKET_RE.findall(s):
        inner = m[1:-1]
        if '|' in inner:
            out.append('SPLIT%d' % (inner.count('|') + 1))
        else:
            out.append('TAG:' + inner)
    return sorted(out)


def token_sig(s):
    """@记号(剥离 plural 括号内容) + plural 分支数 + %记号% + |绑定记号| + 方括号标记/双端记号"""
    at, branches = [], []
    for m in AT_TOKEN_RE.finditer(s):
        t = m.group(0)
        if '(' in t:
            inner = t[t.index('(') + 1:t.rindex(')')]
            branches.append(inner.count('|') + 1)
            t = t[:t.index('(')]
        at.append(t)
    return {
        'at': sorted(at),
        'pct': sorted(PCT_TOKEN_RE.findall(s)),
        'plural': sorted(branches),
        'pipe': PIPE_TOKEN_RE.findall(s),
        'bracket': bracket_sig(s),
        'paren': sorted(PAREN_TOKEN_RE.findall(s)),
    }


def check_pair(en_raw, zh_raw):
    """
    en_raw: 英文原文(经 XML 解析, 实体已解码)
    zh_raw: 中文译文(原样, 可能含实体)
    返回错误字符串列表, 空列表=通过
    """
    errs = []
    e = unescape(en_raw)
    zd = unescape(zh_raw)
    if not isinstance(zh_raw, str) or not zh_raw.strip():
        return ['空译文']
    if ILLEGAL_AMP_RE.search(zd):
        errs.append('非法裸 & (需写成 &amp; / &lt; / &gt;)')
    ep, zp = sorted(PLACEHOLDER_RE.findall(e)), sorted(PLACEHOLDER_RE.findall(zd))
    if ep != zp:
        errs.append(f'占位符不符: 英文{ep} 中文{zp}')
    se, sz = token_sig(e), token_sig(zd)
    if se != sz:
        errs.append(f'@记号/%记号% 不符: 英文{se} 中文{sz}')
    ste, stz = struct(e), struct(zd)
    if ste != stz:
        d = {k: (ste[k], stz[k]) for k in ste if ste[k] != stz[k]}
        errs.append('结构字符不符: ' + ', '.join(f'{k} 英文{a}->中文{b}' for k, (a, b) in d.items()))
    return errs
