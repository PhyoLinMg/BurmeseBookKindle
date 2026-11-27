# Proofreading after OCR

The OCR draft reads like the book, but it is full of small damage. These books are read on a Kindle
by native readers. They notice a clipped word, a stray footer, or a sentence tail sitting in the
wrong paragraph. The goal of this pass is to catch these before they do.

## 1. Blocks

`blocks.json` is a list of blocks:

| type | fields | renders as |
|---|---|---|
| `h` | text | chapter heading (new page, bookmark) |
| `h2` | text | sub-heading |
| `p` | text, indent | paragraph |
| `center` | text | centred line (poems, letters, signatures) |
| `note` | text, sig | boxed author's note (`မှတ်ချက်။ ။ …`, signature right-aligned) |
| `break` | — | scene-break ornament ✻ ✻ ✻ |
| `pic` | src | picture |
| `img` | src, w, indent | a line kept as an image (legacy-font path only) |

## 2. Edit files

An edit file is a JSON list of `[old, new]` pairs, named `eNN.json` where NN is the chapter index
(0-based count of `h` blocks). Extra files for the same chapter add a letter: `e07b.json`,
`e07c.json`. `pipeline.py` applies them all in sorted order on every rebuild; to apply just one
while working:
```
python3 $SK/apply_edits.py work/blocks.json work/e07b.json <first block index of chapter 7>
```
Each pair edits the **first** `p`/`note`/`center` block at or after the chapter start that contains
`old`, and edits it once. So include enough context in `old` to be unique: short strings like
`"ဘူ"` hit the wrong place.

`new` can be:

| `new` | effect |
|---|---|
| any text | replaces `old` inside the block |
| `@DEL@` | deletes the block. Only when `old` equals the block's **whole** text (a substring delete once wiped a long paragraph) |
| `@JOIN@` | merges the next block onto the end of this one (split paragraphs, attribution tails) |
| `@SET@text` | replaces the block's whole text (for heavily garbled paragraphs retyped from the scan) |

Inside the new text, `\n\n` splits the paragraph there, and a piece that starts with a marker
becomes another block type:

| piece starts with | becomes |
|---|---|
| `@H@title` | chapter heading (when the OCR lost one) |
| `@H2@title` | sub-heading |
| `@C@text` | centred line |
| `@NOTE@text` | note box |
| `@BREAK@` | scene break |
| `@PIC@path/to.png` | picture (e.g. a cipher table or diagram cropped from the scan) |

Example (see `examples/e00.json`):
```json
[
  ["ကျေ နပ်", "ကျေနပ်"],
  ["ဟု မေးလေ၏။", "@DEL@"],
  ["သခင်မလို့ ခေါ်တာတော့ သိတယ်”", "@JOIN@"],
  ["…ဟု ပြောလေ၏။ ဤသို့ဖြင့် ညနေ", "…ဟု ပြောလေ၏။\n\n@H@မင်းသမီးဂူ\n\nဤသို့ဖြင့် ညနေ"]
]
```

The script reports `applied X / Y missing: [...]`. A miss usually means an earlier pair already
changed that text, or the text has a different space or quote character than you typed (curly
`“ ”` vs straight `"`; one vs two spaces). Re-print the chapter, copy the exact text, fix the pair.
Don't leave misses.

Block indices shift whenever you split, delete or insert. Re-print the chapter before writing the
next edit file.

## 3. The chapter loop

1. `python3 $SK/show_ch.py work/blocks.json N > /tmp/c.txt` prints chapter N; read it in pieces of
   15–25 KB (`chunk.py blocks.json N from_block [limit]` prints one piece).
2. Write `eNN.json` (or `eNNb.json`…) with every fix for that piece; apply it.
3. Garbled runs (many mangled words per line, sentences that stop and restart) mean the OCR picked
   up the facing page: retype from the scan (section 5).
4. Log in `PROGRESS.md`: "done: N", book-wide decisions (name spellings), and every guess.
5. Next chapter. After the last one, put name spellings in `finalize.json` `replace`, rebuild, and
   re-read any chapter whose edit files had misses.

## 4. What to look for

**Split quote attributions (the most common "wrong sentence order" complaint).** The tail of a
sentence ends up as its own paragraph, or after the next line of dialogue:
```
“… သခင်မလို့ ခေါ်တာတော့ သိတယ်”
ဟု မရေမရာသာ ဖြေဆိုနိုင်၏။          ← belongs on the line above
```
`merge_attributions.py` fixes the plain cases; the rest are found by hand: lone fragments like
`ခင်ဗျ”`, `မတုန်း”`, `တာလဲ”` that end the line before them, or a quote with no closing `”` whose
ending sits two blocks later.

**Leaked page furniture.** Delete or cut out: publisher footers (`အောင်မြင်`, `ဥာဏ်ဝင်း စာပေ`),
author names from the running foot (`မင်း`, `မင်းသ`), running heads inside a paragraph, page numbers
inside text (`အောင်မြင် ၃၀၅ တောင်ငူ…` → `တောင်ငူ…`), and website watermarks (`www.…`, `….com`). Once
a pattern repeats, move it into `cleanup.strip` in config.json instead of fixing it chapter by
chapter.

**Clipped and split words.** The scan edge or the gutter ate a letter, or a space crept in:
`ဆိ ဖွားသည်`→`ဆိတ်ဖွားသည်`, `မဟုတ်ဘူ လူအားလုံး`→`မဟုတ်ဘူး၊ လူအားလုံး`, `ကျေ နပ်`→`ကျေနပ်`,
`ကျွန်း တ္တာကြီး`→`ကျွန်းသေတ္တာကြီး`, `ပြီးနော ပြန်`→`ပြီးနောက် ပြန်`.

**Character confusions.** `၀` (zero) vs `ဝ`; `၎င်း` read as `၄င်း`/`ငှင်း`; ု/ူ; ်/း; ဂ/ဟ; ဓ/ဒ;
တော့ read as ဘော့; Latin letters glued onto Burmese; `"` instead of `“ ”`; `..` instead of `. . .`.

**Missing punctuation at joins.** Two sentences run together where a line or page break used to be:
add the `။`.

**Names and recurring terms.** One spelling per character across the book, the one that appears
most in clean text. Record it in PROGRESS.md and fix variants in `finalize.json` `replace`.
**But check before "fixing" an unusual word:** if it appears consistently in clean text, it is the
author's own usage (e.g. `အိုင်ဆေး` throughout one book), not an OCR error. Normalising it is
introducing an error.

**Lost headings.** A title OCR'd as a plain paragraph, or dropped entirely, merges two chapters.
Compare the chapter list with the contents page and insert with `@H@`. Chapter indices after it
shift by one, so later edit files need renumbering; inserting it through `headings.json` or the
first edit file of the chapter keeps that contained.

**Things the OCR silently drops.** English lines (poems, quotations), text drawn inside
illustrations (a sign, a wall inscription), letter signatures, tables or ciphers, the book's
closing line. Look at every page with unusual layout in the scan, not only at garbled text.

## 5. Pages the OCR cannot save: retype from the scan

When a scan shows a strip of the facing page, Google OCR interleaves both pages and word-level
fixes stop making sense. You recognise these blocks by many short broken words per line, sentences
that restart mid-paragraph, a heading buried in a paragraph, or lines from a different scene.

1. `python3 $SK/find_page.py "work/text/*.txt" "a phrase from the block"` → page number. Phrases in
   the OCR text are the reliable anchor; block indices are not.
2. `python3 $SK/scan_strip.py work/s /tmp/x.png 311 312 313` and read the image. Three or four
   pages per image are readable; zoom into one page (`--scale 1`) when a word is unclear.
3. Retype. For a few paragraphs, use `@SET@` pairs in the chapter's edit file. For a long stretch,
   write the paragraphs to a JSON list (`@H@`, `@BREAK@` allowed) and run
   `replace_range.py blocks.json "first block prefix" "last block prefix" new.json`.
   **Both ends are inclusive** — read the printed list of removed blocks every time. Note that
   replace_range edits blocks.json directly; record the retyped list in the work folder and
   re-run it after `pipeline.py` if you rebuild.

## 6. Problems in the printed book itself

Old printings have their own errors. They are not OCR errors; don't silently "fix" them by
inventing text.
- **A page that repeats another page** (e.g. pp.127–128 reprinting pp.27–28): the real text is
  missing from the source. Remove the duplicate, add a note block in Burmese saying the original is
  missing that text, and tell the user.
- **A name spelled two ways within a few lines**, an obviously wrong number, a garbled English line:
  keep as printed and list it for the user.

## 7. Guesses and honesty

When a word is unreadable in the scan and you fill it from context, it is a guess. Keep a running
list in PROGRESS.md with page numbers. On delivery, tell the user plainly which pages were retyped,
which words are guesses, what was restored, and which defects are in the printed book. A native
reader will check; the list is worth more than reassurance.
