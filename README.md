# burmese-novel-kindle

**မြန်မာစာအုပ် PDF များကို Kindle တွင် ဖတ်ရလွယ်အောင် ပြန်လည်စီစဉ်ပေးသော Claude skill**

This is a [Claude](https://claude.ai) skill and a set of Python scripts. It turns a Burmese book PDF
into a retyped, proofread Unicode PDF sized for a 6" Kindle. The source can be a phone or scanner
scan, a cherrythitsar-style legacy-font PDF, or a typed WinInnwa document.

A scanned Burmese PDF reads badly on a Kindle. The pages are tiny images, you can't zoom per line,
and the text can't be searched. This pipeline produces:

- **A 4.25 × 5.667 in PDF.** One page is one Kindle screen, set in Padauk at a real, measured
  12 pt with line height 1.9.
- **Navigation.** A cover, a title page, and a bookmark for each chapter in the Kindle "Go to" menu.
- **Pictures.** Illustrations, cipher tables and diagrams are kept as images.
- **A plain-text copy** (`_text.txt`) of the whole book.

The real work is not the OCR. It is the **proofreading pass after OCR**, done chapter by chapter.
That pass re-attaches split dialogue, removes leaked page headers and footers, repairs clipped
words, restores headings and lines that the OCR dropped, and retypes garbled pages from the scans.
It also records every guess, so a native reader can check it. That workflow is written down in
[`SKILL.md`](SKILL.md) and [`reference/proofreading.md`](reference/proofreading.md).

## What it handles

| Source PDF | How it's read |
|---|---|
| Scanned pages (single or two-up) | Split, deskew, Google Docs OCR in small batches with page markers, then proofreading |
| Legacy font `ZTR…` (cherrythitsar.org) | Glyph codes decoded straight to Unicode; lines that can't be decoded are kept as images |
| `WinInnwa` / Win-family fonts (typed Word documents) | Glyph codes decoded and reordered to Unicode |

## Using it with Claude (recommended)

The skill is written for Claude. Claude runs the scripts, reads the scans, and does the
chapter-by-chapter proofreading.

**Claude Code**
```bash
git clone https://github.com/PhyoLinMg/BurmeseBookKindle ~/.claude/skills/burmese-novel-kindle
```
Then ask: *"Retype this Burmese novel PDF for Kindle and proofread it"* and attach the PDF.

**Claude apps (claude.ai / desktop)**: zip this folder and upload it as a custom skill in Claude's
settings. Connect the **Google Drive** connector too: OCR of scanned books runs through Google
Docs, which reads Burmese far better than tesseract.

A 400-page scanned book takes several sessions. The skill keeps a `PROGRESS.md` in the work folder,
so a new session can pick up where the last one stopped.

## Using the scripts by hand

```bash
sudo apt install poppler-utils fonts-sil-padauk   # plus google-chrome
pip install -r requirements.txt
SK=$PWD/scripts

# 1. page images (one PNG per book page)
python3 $SK/prepare_scans.py book.pdf work/s --twoup

# 2. OCR batches with #P0042# page markers
python3 $SK/make_ocr_batches.py work/s work/batches --per 10
#    upload each bNN.pdf to Google Drive → Open with Google Docs → Download as .txt → work/text/

# 3. configure (copy and edit the examples), then build the draft
cp examples/{config,headings,finalize}.json work/
python3 $SK/pipeline.py work/config.json

# 4. proofread: print a chapter, write work/e00.json fixes, rebuild
python3 $SK/show_ch.py work/blocks.json 0
python3 $SK/pipeline.py work/config.json

# 5. typeset and check the measured font size
BOOK_AUTHOR="မင်းသိင်္ခ" bash $SK/build.sh work/blocks.json book.pdf out MyBook "Title line 1" "Title line 2"
```

`pipeline.py` regenerates the book from the OCR text and then applies every edit file in order.
Proofreading is never lost when you re-OCR a page or add a cleanup rule. The edit-file format
(`@DEL@`, `@JOIN@`, `@SET@`, `@H@`, `@C@`, `@PIC@` …) is documented in
[`reference/proofreading.md`](reference/proofreading.md).

## Repository layout

```
SKILL.md                    the skill: which path, OCR, assembly, build, checks
reference/proofreading.md   proofreading after OCR: edit format, the chapter loop, what to fix
scripts/                    all pipeline scripts (usage in each docstring)
examples/                   config, headings, finalize, edit file and PROGRESS.md templates
```

## Lessons baked in

- **Measure the font size; don't trust the CSS.** Headless Chrome shrinks the whole book when one
  Burmese line won't break, so books came out at 8–11 pt from a 12 pt stylesheet. The typesetter
  adds zero-width spaces, and `check_fontsize.py` measures the size the PDF actually rendered.
- **Small OCR batches with page stamps.** Google OCR is unreliable on large PDFs. The `#PNNNN#`
  stamps map the text back to book pages.
- **Check the two-up gutter before OCR.** One wrong split clips the first letters of every line on
  dozens of pages.
- **Don't "correct" the author.** A spelling that appears consistently in clean text is the
  author's own usage. Misprints in the original book are reported, not invented around.

## Copyright

This repository contains tools only. It contains no book text and no scans. Most Burmese novels
are still under copyright. Use this to make a readable copy of a book you own, for your own
reading. Don't publish the converted books unless you have the rights.

## License

MIT. See [LICENSE](LICENSE).
