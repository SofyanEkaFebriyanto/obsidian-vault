#!/usr/bin/env python3
"""Render markdown chapters to a print-quality PDF with reportlab.

Supported markdown
------------------
    #/##/### headings, paragraphs, -/*/+ bullets, N. numbered lists,
    pipe tables, > blockquotes, --- horizontal rules, and inline
    **bold** / *italic* / `code`.

Two reportlab traps this script already handles
-----------------------------------------------
1. Built-in fonts have no mappable bold/italic pair, so fontName='Times-Bold'
   raises "Can't map determine family/bold/italic". We register a real TTF
   family and map the four faces.
2. reportlab requires the innermost tag to be closed first. The emphasis
   parser below uses a stack that stores tags in OPEN order (outermost
   first), so the closing test compares the stack tail against `tags` in
   forward order. Reversing that yields </b></i> and a hard build failure.

Usage
-----
    python3 md_to_pdf_reportlab.py --out book.pdf ch*.md
    python3 md_to_pdf_reportlab.py --out book.pdf --size A4 --title "My Book" ch*.md
"""

import argparse
import glob
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

BAD_SCRIPT = re.compile(
    '[\u2e80-\u303f\u4e00-\u9fff\uff00-\uffef\u0400-\u04ff]')

# Candidate serif families, first existing wins.
SERIF_DIRS = [
    '/usr/share/fonts/liberation-serif-fonts',
    '/usr/share/fonts/dejavu',
    '/usr/share/fonts/truetype/dejavu',
    '/usr/share/fonts/gnu-free',
]
MONO_DIRS = [
    '/usr/share/fonts/liberation-mono-fonts',
    '/usr/share/fonts/dejavu',
    '/usr/share/fonts/truetype/dejavu',
    '/usr/share/fonts/adobe-source-code-pro-fonts',
]
SERIF_FACES = [
    ('BookSerif', 'LiberationSerif-Regular.ttf'),
    ('BookSerif-Bd', 'LiberationSerif-Bold.ttf'),
    ('BookSerif-It', 'LiberationSerif-Italic.ttf'),
    ('BookSerif-BdIt', 'LiberationSerif-BoldItalic.ttf'),
]
MONO_FACES = [
    ('BookMono', 'LiberationMono-Regular.ttf'),
    ('BookMono-Bd', 'LiberationMono-Bold.ttf'),
    ('BookMono-It', 'LiberationMono-Italic.ttf'),
]

INK = colors.HexColor('#2b2622')
ACCENT = colors.HexColor('#8c5a2b')
MUTED = colors.HexColor('#6f655c')
RULE = colors.HexColor('#d8cfc2')
WARN = colors.HexColor('#b00020')

_registered = False


def _first_existing(dirs, filename):
    for d in dirs:
        path = os.path.join(d, filename)
        if os.path.exists(path):
            return path
    return None


def register_fonts():
    """Register a serif family with a mappable bold/italic pair."""
    global _registered
    if _registered:
        return
    for name, filename in SERIF_FACES:
        path = _first_existing(SERIF_DIRS, filename)
        if path:
            pdfmetrics.registerFont(TTFont(name, path))
    for name, filename in MONO_FACES:
        path = _first_existing(MONO_DIRS, filename)
        if path:
            pdfmetrics.registerFont(TTFont(name, path))
    from reportlab.lib.fonts import addMapping
    addMapping('BookSerif', 0, 0, 'BookSerif')
    addMapping('BookSerif', 1, 0, 'BookSerif-Bd')
    addMapping('BookSerif', 0, 1, 'BookSerif-It')
    addMapping('BookSerif', 1, 1, 'BookSerif-BdIt')
    _registered = True


def inline(text):
    """Escape XML, then apply bold/italic/code via a stack parser.

    The stack holds tags in OPEN order (outermost first). reportlab wants the
    innermost tag closed first, which is exactly popping the stack in reverse.
    The closing test therefore compares the stack tail to `tags` in forward
    order -- do not reverse it.
    """
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    stash = []

    def keep_code(m):
        stash.append(m.group(1))
        return '\x01%d\x01' % (len(stash) - 1)

    text = re.sub(r'`([^`]+)`', keep_code, text)

    out, stack, i, n = [], [], 0, len(text)
    while i < n:
        if text[i] != '*':
            out.append(text[i])
            i += 1
            continue

        run = 0
        while i + run < n and text[i + run] == '*':
            run += 1
        tags = ('i',) if run == 1 else (('b',) if run == 2 else ('b', 'i'))

        close_tags = tags[:min(run, len(tags))]
        if len(stack) >= len(close_tags) and tuple(stack[-len(close_tags):]) == close_tags:
            for _ in close_tags:
                out.append('</%s>' % stack.pop())
        elif stack and tags[0] in stack:
            out.append('*' * run)          # unmatched, keep as literal
        else:
            for tag in tags:
                out.append('<%s>' % tag)
                stack.append(tag)
        i += run

    while stack:
        out.append('</%s>' % stack.pop())

    text = ''.join(out)
    for idx, code in enumerate(stash):
        text = text.replace('\x01%d\x01' % idx, '<font face="BookMono">%s</font>' % code)
    return text


def build_styles(base, step):
    register_fonts()
    ss = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('title', parent=ss['Title'], fontName='BookSerif-Bd',
                                fontSize=base * 2.0, leading=base * 2.5,
                                textColor=INK, spaceAfter=6, alignment=TA_LEFT),
        'h2': ParagraphStyle('h2', parent=ss['Heading1'], fontName='BookSerif-Bd',
                             fontSize=base * 1.4, leading=base * 1.8,
                             textColor=ACCENT, spaceBefore=13, spaceAfter=5),
        'h3': ParagraphStyle('h3', parent=ss['Heading2'], fontName='BookSerif-Bd',
                             fontSize=base * 1.14, leading=base * 1.5,
                             textColor=INK, spaceBefore=9, spaceAfter=3),
        'body': ParagraphStyle('body', parent=ss['BodyText'], fontName='BookSerif',
                               fontSize=base, leading=base * 1.5, textColor=INK,
                               alignment=TA_JUSTIFY, spaceAfter=6),
        'bullet': ParagraphStyle('bullet', parent=ss['BodyText'], fontName='BookSerif',
                                 fontSize=base, leading=base * 1.5, textColor=INK,
                                 leftIndent=12, bulletIndent=2, spaceAfter=3,
                                 alignment=TA_LEFT),
        'quote': ParagraphStyle('quote', parent=ss['BodyText'], fontName='BookSerif-It',
                                fontSize=base, leading=base * 1.5, textColor=MUTED,
                                leftIndent=10, spaceBefore=4, spaceAfter=6),
        'ref': ParagraphStyle('ref', parent=ss['BodyText'], fontName='BookSerif-It',
                              fontSize=base * 0.87, leading=base * 1.24,
                              textColor=MUTED, alignment=TA_LEFT, spaceBefore=8),
        'cell': ParagraphStyle('cell', parent=ss['BodyText'], fontName='BookSerif',
                               fontSize=base * 0.87, leading=base * 1.18,
                               textColor=INK, spaceAfter=0, alignment=TA_LEFT),
        'warn': ParagraphStyle('warn', parent=ss['BodyText'], fontName='BookMono',
                               fontSize=base * 0.8, leading=base * 1.2,
                               textColor=WARN, alignment=TA_LEFT, spaceAfter=4),
    }


def make_table(rows, style, width):
    data = [[Paragraph(inline(c.strip()), style['cell']) for c in r] for r in rows]
    ncol = max(len(r) for r in data)
    data = [r + [''] * (ncol - len(r)) for r in data]
    table = Table(data, colWidths=[width / ncol] * ncol, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE', (0, 0), (-1, 0), 0.8, ACCENT),
        ('LINEBELOW', (0, 0), (-1, -2), 0.35, RULE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def md_to_flowables(md, style, width):
    out = []
    lines = md.split('\n')
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue

        # Surface corrupt lines in the PDF itself rather than shipping them.
        if BAD_SCRIPT.search(stripped):
            out.append(Paragraph(
                '[CORRUPT LINE, fix the source] %s' % stripped[:110], style['warn']))
            i += 1
            continue

        if set(stripped) <= set('-*_') and len(stripped) >= 3:
            out.append(Spacer(1, 7))
            i += 1
            continue

        m = re.match(r'^(#{1,3})\s+(.*)', stripped)
        if m:
            level, txt = len(m.group(1)), m.group(2)
            if level == 1:
                out.append(Spacer(1, 3))
                out.append(Paragraph(inline(txt), style['title']))
            elif level == 2:
                out.append(Paragraph(inline(txt), style['h2']))
            else:
                out.append(Paragraph(inline(txt), style['h3']))
            i += 1
            continue

        if '|' in stripped and i + 1 < len(lines) and \
                re.match(r'^\s*\|?[\s:\-|]+\|[\s:\-|]*$', lines[i + 1]):
            rows = [stripped.strip('|').split('|')]
            i += 2
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                rows.append(lines[i].strip().strip('|').split('|'))
                i += 1
            if rows and len(rows[0]) > 1:
                out.append(make_table(rows, style, width))
                out.append(Spacer(1, 6))
            continue

        m = re.match(r'^[-*+]\s+(.*)', stripped)
        if m:
            out.append(Paragraph(inline(m.group(1)), style['bullet'], bulletText='•'))
            i += 1
            continue

        m = re.match(r'^(\d+)[.)]\s+(.*)', stripped)
        if m:
            out.append(Paragraph(inline(m.group(2)), style['bullet'],
                                 bulletText=m.group(1) + '.'))
            i += 1
            continue

        if stripped.startswith('>'):
            out.append(Paragraph(inline(stripped.lstrip('> ')), style['quote']))
            i += 1
            continue

        out.append(Paragraph(inline(stripped), style['body']))
        i += 1
    return out


def make_page_decorators(pagesize, width, footer, margin):
    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont('BookSerif', 7.3)
        canvas.setFillColor(MUTED)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(margin, margin * 0.83, pagesize[0] - margin, margin * 0.83)
        canvas.drawString(margin, margin * 0.6, footer)
        canvas.drawRightString(pagesize[0] - margin, margin * 0.6, str(doc.page))
        canvas.restoreState()

    def on_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#f4efe6'))
        canvas.rect(0, 0, pagesize[0], pagesize[1], stroke=0, fill=1)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, pagesize[1] - 5 * mm, pagesize[0], 5 * mm, stroke=0, fill=1)
        canvas.restoreState()

    return on_page, on_cover


def selftest():
    """Assert the emphasis parser balances. Run this after editing inline()."""
    cases = [
        ('**bold with *italic* inside** end', True),
        ('*italic* only', True),
        ('**bold** only', True),
        ('***all three***', True),
        ('unbalanced ** bold', True),
        ('italic **inside bold** end', True),
        ('a * b * c', True),
        ('**a *b* c *d* e**', True),
        ('**Bab 1 (Cialdini) dan *Aristoteles***', True),
    ]
    failures = 0
    for src, _ in cases:
        out = inline(src)
        opened = re.findall(r'<([bi])>', out)
        closed = re.findall(r'</([bi])>', out)
        balanced = opened == closed[::-1]
        if not balanced:
            failures += 1
        print('[%s] %-44s -> %s' % ('OK ' if balanced else 'BAD', src, out))
    if failures:
        print('%d emphasis case(s) unbalanced' % failures)
        return 1
    print('all emphasis cases balanced')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', nargs='*', help='markdown files (default: ch*.md)')
    parser.add_argument('--out', required=True, help='output PDF path')
    parser.add_argument('--title', default=None, help='cover title')
    parser.add_argument('--subtitle', default=None, help='cover subtitle')
    parser.add_argument('--size', default='A5', choices=['A5', 'A4', 'LETTER'])
    parser.add_argument('--font-size', type=float, default=9.3)
    parser.add_argument('--margin-mm', type=float, default=15.0)
    parser.add_argument('--footer', default='Document')
    parser.add_argument('--no-cover', action='store_true')
    parser.add_argument('--selftest', action='store_true',
                        help='test the emphasis parser and exit')
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    pagesize = {'A5': A5, 'A4': A4, 'LETTER': None}[args.size]
    if pagesize is None:
        from reportlab.lib.pagesizes import LETTER
        pagesize = LETTER

    files = args.inputs or sorted(glob.glob('ch*.md'))
    if not files:
        print('no input files', file=sys.stderr)
        return 1

    style = build_styles(args.font_size, 1.0)
    margin = args.margin_mm * mm
    width = pagesize[0] - 2 * margin
    on_page, on_cover = make_page_decorators(pagesize, width, args.footer, margin)

    doc = BaseDocTemplate(args.out, pagesize=pagesize,
                          leftMargin=margin, rightMargin=margin,
                          topMargin=margin - 2 * mm, bottomMargin=margin,
                          title=args.title or os.path.basename(args.out))
    frame = Frame(margin, margin, width, pagesize[1] - 2 * margin, id='main')
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[frame], onPage=on_cover),
        PageTemplate(id='body', frames=[frame], onPage=on_page),
    ])

    story = []
    if not args.no_cover:
        story += [
            Spacer(1, pagesize[1] * 0.24),
            Paragraph(inline(args.title or os.path.splitext(
                os.path.basename(args.out))[0]), style['title']),
        ]
        if args.subtitle:
            story.append(Paragraph(inline(args.subtitle), style['h2']))
        story += [Spacer(1, 4 * mm), NextPageTemplate('body'), PageBreak()]

    warnings = 0
    for path in files:
        with open(path, encoding='utf-8') as fh:
            md = fh.read()
        for line in md.split('\n'):
            if BAD_SCRIPT.search(line):
                warnings += 1
        story.extend(md_to_flowables(md, style, width))
        story.append(PageBreak())

    while story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)
    size_kb = os.path.getsize(args.out) / 1024.0
    print('wrote %s (%d source files, %.0f KB)' % (args.out, len(files), size_kb))
    if warnings:
        print('WARNING: %d corrupt line(s) marked in the PDF. '
              'Fix the markdown and rebuild.' % warnings)
    return 0


if __name__ == '__main__':
    sys.exit(main())
