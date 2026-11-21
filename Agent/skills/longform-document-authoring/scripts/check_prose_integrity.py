#!/usr/bin/env python3
"""Gate long-form prose against self-inflicted generation corruption.

Why this exists
---------------
Long-form generation injects foreign characters into its own output in ways the
author cannot see. Observed damage classes (all seen in one authoring session):

  1. CJK / Kana / Hangul inserted mid-word, splitting an Indonesian or English word
  2. Cyrillic (or Greek) glyphs posing as Latin letters
  3. Fullwidth punctuation (U+FF00 block) in running prose
  4. Words glued together with no space
  5. stranded camelCase tokens in the middle of a sentence
  6. character loops -- decode collapse, thousands of repeated glyphs

Classes 1-3 and 6 are objectively detectable. Class 4-5 are heuristically
detected. What this script CANNOT catch, and what you must read for yourself:
valid-English fragments spliced into prose, and sentences that are grammatical
but wrong. The checker is a floor, not a ceiling.

Usage
-----
    python3 check_prose_integrity.py ch01.md ch02.md
    python3 check_prose_integrity.py            # defaults to ch*.md in cwd

Exit code is 0 when every file is clean, 1 when any file has findings, so it
drops straight into a build script.
"""

import re
import sys
import glob

# CJK radicals+blocks, Kana, Hangul, fullwidth forms, Cyrillic, Greek,
# Arabic, Hebrew, Thai, Devanagari.
BAD_SCRIPT = re.compile(
    '[\u1100-\u11ff\u2e80-\u303f\u3040-\u30ff\u3130-\u318f'
    '\u3400-\u4dbf\u4e00-\u9fff\ua960-\ua97f\uac00-\ud7af'
    '\uf900-\ufaff\ufb00-\ufdff\ufe30-\ufe4f\uff00-\uffef'
    '\u0400-\u04ff\u0370-\u03ff\u0590-\u05ff\u0600-\u06ff'
    '\u0e00-\u0e7f]'
)

# Decode collapse: one character repeated absurdly.
LOOP = re.compile(r'(.)\1{12,}', re.S)

# stranded camelCase inside prose. Allowlist real-world names and acronyms.
ALLOW = {
    'BondDePaulo', 'McGwire', 'IBM', 'TV', 'PDF', 'NLP', 'FACS',
    'AU1', 'AU2', 'AU4', 'AU6', 'AU12', 'AU24', 'AU43',
}
CAMEL = re.compile(r'\b[a-z]{2,}[A-Z][a-z]{2,}\b')

# Two of the same letter glued without a space that is not a known word.
# Heuristic only -- printed as a warning, never a hard failure.
GLUED = re.compile(r'\b([a-z]{3,})\1\b')

CTX = 40


def _context(text, i, j):
    return text[max(0, i - CTX):j + CTX].replace('\n', ' ')


def check(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()

    hard, soft = [], []

    for m in BAD_SCRIPT.finditer(text):
        hard.append('foreign script U+%04X: ...%s...'
                    % (ord(m.group()), _context(text, m.start(), m.end())))

    for m in LOOP.finditer(text):
        hard.append('character loop %r x%d at %d: ...%s...'
                    % (m.group(1), m.end() - m.start(), m.start(),
                       _context(text, m.start(), m.start() + 20)))

    for m in CAMEL.finditer(text):
        if m.group(0) not in ALLOW:
            soft.append('stranded camelCase %r: ...%s...'
                        % (m.group(0), _context(text, m.start(), m.end())))

    for m in GLUED.finditer(text):
        soft.append('doubled fragment %r: ...%s...'
                    % (m.group(0), _context(text, m.start(), m.end())))

    return len(text), len(text.split()), hard, soft


def main(argv):
    files = argv[1:] or sorted(glob.glob('ch*.md'))
    if not files:
        print('no files given and no ch*.md in cwd', file=sys.stderr)
        return 1

    bad = 0
    total_words = 0
    for path in files:
        try:
            size, words, hard, soft = check(path)
        except OSError as exc:
            print('[ERR ] %s: %s' % (path, exc), file=sys.stderr)
            bad += 1
            continue

        total_words += words
        clean = not hard and not soft
        print('[%s] %-34s %6d char  %5d words'
              % ('OK  ' if clean else 'RUSAK', path, size, words))
        for item in hard:
            print('         HARD  %s' % item)
        for item in soft:
            print('         soft  %s' % item)
        extra = max(0, len(hard) + len(soft) - 12)
        if extra:
            print('         ... %d more' % extra)
        bad += bool(hard or soft)

    print('\n%d file(s), %d words total, %d with findings'
          % (len(files), total_words, bad))
    if bad:
        print('HARD findings must be fixed by rewriting the whole sentence.')
        print('soft findings are heuristic -- read each one and decide.')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
