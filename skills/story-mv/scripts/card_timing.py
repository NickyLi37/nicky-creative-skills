#!/usr/bin/env python3
"""Check that every credit card stays fully lit long enough to be read.

usage: card_timing.py CARDS.txt|CARDS.json [--wps 4] [--max-lines 6]

CARDS.txt: one card per block, blocks separated by a blank line. A block's first line may be "@hold 6.5"
(seconds at full light). CARDS.json: [{"name": "card 1", "hold": 6.5, "lines": ["...", "..."]}, ...].

Counting follows the HONG KONG reviewer: each English word, number, URL or "&" counts 1; a Chinese name, shop
or album counts 1; separators such as "·" or a lone "/" count 0. Reading speed is 4 words a second for normal
silent reading, with 5 as the fast check. The film lost two rebuild rounds to cards that looked fine and could
not be read in time, so size full-light time from the count before the first render.
Standard library only.
"""
import argparse
import json
import math
import re
import sys

CJK = r'[㐀-䶿一-鿿豈-﫿]'
SEP = re.compile(r'^[\W_]+$')


def words(line):
    n, long_cjk = 0, []
    for tok in re.split(r'[\s·•|]+', line.strip()):
        if not tok:
            continue
        runs = re.findall(CJK + '+', tok)
        latin = re.sub(CJK + '+', ' ', tok)
        for r in runs:
            n += 1
            if len(r) > 6:
                long_cjk.append(r)
        for t in latin.split():
            if not SEP.match(t) or t == '&':
                n += 1
    return n, long_cjk


def load(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    if path.lower().endswith('.json'):
        cards = json.loads(text)
        return [dict(name=c.get('name', f'card {i + 1}'), hold=c.get('hold'), lines=c['lines']) for i, c in enumerate(cards)]
    cards = []
    for i, block in enumerate(re.split(r'\n\s*\n', text.strip())):
        lines, hold = [], None
        for ln in block.splitlines():
            m = re.match(r'\s*@hold\s+([0-9.]+)', ln)
            if m:
                hold = float(m.group(1))
            elif ln.strip():
                lines.append(ln.strip())
        if lines:
            cards.append(dict(name=f'card {len(cards) + 1}', hold=hold, lines=lines))
    return cards


def check(cards, wps=4.0, max_lines=6):
    rows, bad = [], 0
    for c in cards:
        counts = [words(l) for l in c['lines']]
        n = sum(k for k, _ in counts)
        need = n / wps
        fast = n / (wps * 1.25)
        hold = c.get('hold')
        notes = []
        if len(c['lines']) > max_lines:
            notes.append(f'{len(c["lines"])} lines, keep it to {max_lines}')
        if hold is None:
            verdict = 'no hold given'
        elif hold >= need:
            verdict = 'OK'
        elif hold >= fast:
            verdict = 'TIGHT'
        else:
            verdict = 'SHORT'
        if verdict in ('TIGHT', 'SHORT') or len(c['lines']) > max_lines:
            bad += 1
        long_ = [r for _, rs in counts for r in rs]
        if long_:
            notes.append('long Chinese text: time it by reading it aloud')
        suggest = math.ceil(need * 2) / 2
        rows.append(dict(name=c['name'], lines=len(c['lines']), words=n, hold=hold, need=round(need, 2),
                         need_fast=round(fast, 2), verdict=verdict, suggest=suggest, notes=notes))
    return rows, bad


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cards')
    p.add_argument('--wps', type=float, default=4.0, help='words a second at normal reading speed')
    p.add_argument('--max-lines', type=int, default=6)
    a = p.parse_args(argv)
    rows, bad = check(load(a.cards), a.wps, a.max_lines)
    print(f'{"card":10} {"lines":>5} {"words":>5} {"hold":>6} {"need":>6} {"fast":>6}  verdict')
    for r in rows:
        hold = '-' if r['hold'] is None else f'{r["hold"]:.2f}'
        extra = f'  hold at least {r["suggest"]:.1f} s' if r['verdict'] in ('TIGHT', 'SHORT', 'no hold given') else ''
        note = ('  ' + '; '.join(r['notes'])) if r['notes'] else ''
        print(f'{r["name"]:10} {r["lines"]:5d} {r["words"]:5d} {hold:>6} {r["need"]:6.2f} {r["need_fast"]:6.2f}  {r["verdict"]}{extra}{note}')
    print(f'{len(rows)} cards, {bad} to fix. Leave about 1 s of black after the last card.')
    return 1 if bad else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as err:
        print('card_timing:', err, file=sys.stderr)
        sys.exit(2)
