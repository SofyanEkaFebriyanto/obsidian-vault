---
name: longform-document-authoring
description: "Author multi-chapter long-form files, gate, render PDF."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [longform, ebook, document, markdown, pdf, prose, verification, reportlab]
    category: productivity
    related_skills: [pdf, humanizer, docx, grounded-citations]
---

# Long-form document authoring

Build a multi-chapter document as real files on disk, verify every chapter, and render the whole thing to PDF. The hard part is not the writing. It is that long-form generation **corrupts itself**, and a corrupted chapter that looks fine to the author will ship silently.

**Core principle: the file is not trustworthy because you wrote it. It is trustworthy because a checker ran on it.**

## When to use

- "bikin ebook", "buku personal", "split jadi beberapa bab"
- A report, handbook, course, or playbook delivered as a document artifact
- Any deliverable that must end up as a real file the user opens, not a chat reply
- Existing prose that needs an integrity pass before delivery

Not for: a short memo (just answer in chat), or a single-page spec (write the file).

## Workflow

### Phase 1: agree the shape before writing

Ask, or infer and state, four things: chapter count, chapter order, target length per chapter, and output format (`.md` only, or `.md` plus PDF). If the user has not answered after one `clarify` call, **proceed with the recommended defaults and say which ones you assumed**. Do not stall on a second round of questions; a deliverable in the assumed shape is worth more than a perfect shape nobody is waiting for.

### Phase 2: one file per chapter

Write `ch00-intro.md`, `ch01-*.md`, and so on, rather than one giant file. This gives you three things: a corrupt chapter can be rewritten without touching the others, a PDF build can glob them in order, and the user can edit one chapter without a merge conflict.

Give every chapter the same skeleton so the document reads as one work:

```markdown
# BAB N — TITLE

**Source: Author, *Book Title* (year)**

## Why this chapter sits here
## The argument
## The part everyone gets wrong
## Practical application
## Latihan Bab N   <- one concrete exercise, always
```

That last section is what separates a document the user can use from one they can only reread.

### Phase 3: gate every chapter

Run `scripts/check_prose_integrity.py` after **every** chapter, before moving on. Do not batch the check at the end. See "The corruption problem" below for why.

```bash
python3 scripts/check_prose_integrity.py ch01-*.md ch02-*.md
```

Exit code is non-zero when any file is damaged, so it drops straight into a build script.

### Phase 4: render and verify

```bash
python3 scripts/md_to_pdf_reportlab.py --out book.pdf ch*.md
pdftotext book.pdf - | head -40      # confirm text actually renders
```

Verify the rendered text, not just the file size. See "Pitfalls" for the extraction trap.

## The corruption problem

Long-form generation degrades in ways that are invisible to the author and obvious to a reader. Observed rates in a 13-chapter Indonesian document ranged from 0 defects in a 7,800-character chapter to 20 in a 5,900-character one, so **length is not the predictor, and you cannot eyeball your way out of this**. Only a checker catches it.

Damage types, all observed in one session:

| Type | Example |
|---|---|
| CJK injected mid-word | `mela对其做.` where `melakukan.` was intended |
| Cyrillic posing as Latin | `tidak akanets` where `memperbaiki` was intended |
| Fullwidth punctuation | `。` `，` `、` in running prose |
| Words glued, no space | `Aristotelesdivide`, `punyaPesona` |
| camelCase stranded mid-sentence | `caraXivAssembly`, `duanyaReading` |
| Valid English spliced into prose | `stop Guillotine melihat`, `MayoritasnyaIteration mengarang` |
| Character loop (decode collapse) | thousands of repeated glyphs, output unusable |

The last type is the catastrophic one: it eats a whole response, including the tool call that was supposed to write the file. Recovery is to write shorter, and never lose the rest of the work in one shot.

`scripts/check_prose_integrity.py` catches the first five. It cannot catch the sixth (an English fragment is valid text) or sentences that are grammatical but wrong. **Read the output too.** The checker is a floor, not a ceiling.

## Repair discipline

Getting this wrong costs more turns than the corruption did.

**Never blanket-strip the bad characters.** `re.sub(CJK, '', text)` deletes the glyphs and leaves the word broken around the hole: `melakukan` becomes `mel.`. You have silently destroyed the sentence while satisfying your own regex. Strip-then-check will report clean and ship garbage.

**Rewrite the whole sentence.** Locate the damage with a context-printing pass, then replace the entire clause with clean text:

```python
for m in BAD.finditer(text):
    print(repr(text[max(0, m.start()-45):m.end()+45]))   # see the damage in place
```

Then replace by sentence, not by token. A 20-character context window is enough to see what the sentence was trying to say.

**String replace can silently miss.** When two damaged characters are adjacent, `text.replace("foo", "bar")` can fail to match depending on surrounding context. When a replace does nothing, verify the target exists and fall back to index splicing:

```python
idx = [m.start() for m in BAD.finditer(text)]
if len(idx) == 2:
    text = text[:idx[0]] + "replacement" + text[idx[1] + 1:]
```

**Your repair text can be corrupt too.** The same generation defect that damaged the file can damage the replacement string you are typing. Verify after every single patch, not once at the end. A patch pass that does not re-verify is a guess.

**Short appends beat long writes.** When corruption rate is high, write the first third, check, append the middle, check, append the end, check. Slower per chapter, far fewer damaged characters overall, and a failure costs one section instead of the chapter.

## Delegation pitfalls

Fan-out looks like the obvious way to parallelize chapter writing. It is a trap when the model is degrading.

- **Your own prompts get corrupted.** Prompts that looked fine when composed arrived at the subagent containing stray Cyrillic and Chinese. The child then worked from garbled instructions. If your generation is unstable, do not delegate prose.
- **A "completed" report does not mean a file exists.** In one session 5 of 10 subagents reported completion, and one reported full success while having written nothing. List the directory and check on disk (`search_files` with `target='files'`, or `ls` in `terminal`). Never take the report as evidence of a side effect.
- **Rate limits kill the batch silently.** Failures surface only in the consolidated result, minutes later, after you have moved on.
- **Fallback rule:** if more than a third of a batch fails, stop delegating and write the remainder yourself, sequentially, with a checker after each file.

## PDF rendering

`scripts/md_to_pdf_reportlab.py` handles headings, paragraphs, bullets, numbered lists, pipe tables, blockquotes, rules, and inline emphasis, and flags any line containing non-Latin characters in the output so a corrupt chapter is visible in the PDF itself.

Two reportlab specifics that cost real time:

**Register real TTFs.** The built-in fonts have no mappable bold/italic pair, so `fontName='Times-Bold'` raises `Can't map determine family/bold/italic`. Register a family and map it:

```python
pdfmetrics.registerFont(TTFont('BookSerif', '.../LiberationSerif-Regular.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('BookSerif', 1, 0, 'BookSerif-Bd')
```

**Inline emphasis needs a stack parser, and the stack holds open order.** For `**bold and *italic* end**`, reportlab requires the innermost tag closed first. The stack stores tags outermost-first, so the closing check compares the tail against `tags` in forward order. Getting this backwards yields `</b></i>` and a build failure. `***both***` needs care: one run opens two tags, so the close must pop two.

**Test the parser on its own** before building a document. The render script ships a self-test for exactly this:

```bash
python3 scripts/md_to_pdf_reportlab.py --selftest --out /dev/null
```

Nine inline cases; it asserts open/close tags balance and prints each result. Takes a second, and it is the fastest way to confirm an edit to `inline()` did not break the stack.

## Pitfalls

- **Naive PDF text extraction returns nothing.** With subset-embedded fonts, `Tj` operators are not plain text and a hand-rolled extractor reports zero characters for a perfectly good 51-page file. Use `pdftotext` (poppler) or `pypdf`. Do not conclude the PDF is empty because your regex found nothing.
- **Do not check the PDF, check the source.** A corrupt chapter renders corrupt. The integrity gate belongs on the markdown, before the build.
- **Rewriting a function can duplicate it.** Slicing with `text[:start] + new + text[end:]` when `end` is the index of a marker appearing *earlier* than `start` silently duplicates the function instead of replacing it. After any such edit, assert the definition count.
- **Chapter order comes from the filename glob.** Prefix with zero-padded numbers or the order is alphabetical, not deliberate.
- **Do not fabricate citations.** If a source cannot be verified, either drop the claim or mark it as unverified. Inventing a plausible author, date, or quotation is the one failure mode that makes the whole document untrustworthy, and it is invisible to every checker above.
- **Read the first chapter yourself after building.** A document that is 90 percent clean still fails if the opening is the corrupted one.

## User preference

For Sofyan: direct, no preamble, no restating the request, no hedging. Match reply length to the weight of the ask. When something is genuinely blocked, name the specific blocker in one sentence and stop. For documents he prefers real files over chat prose, and he accepts machine-checked verification as long as you also say plainly which parts are weakest so he knows where to look first. See the `humanizer` skill for the prose-quality pass, and `pdf` for PDF operations beyond this build script.
