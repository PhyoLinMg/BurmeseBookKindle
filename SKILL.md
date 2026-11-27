---
name: burmese-novel-kindle
description: Turn a scanned, legacy-font (ZTR) or WinInnwa Burmese book PDF into a proofread, retyped Unicode Kindle PDF (12 pt Padauk, chapter bookmarks) plus a plain-text copy - OCR, chapter-by-chapter proofreading, retyping from scans, typesetting, checks.
---

# Burmese book → retyped Kindle PDF

The deliverable is a 4.25 × 5.667 in PDF (the size of a 6" Kindle screen), set in Padauk Book 12 pt
with line height 1.9. It has a cover, a title page and one bookmark per chapter, and comes with a
`_text.txt` plain-text copy. Every book in a series must print at the **same measured size**:
the reader can't resize text in a PDF, so a mismatch between books is the first thing they notice.

All scripts are in this skill's `scripts/` folder; `SK` below means that folder's absolute path.
Run them as `python3 $SK/<name>.py` (`bash` for build.sh). Each script's docstring gives its usage.
`examples/` has a filled-in config, headings, finalize and edit file to copy from.

Keep one work folder per book (`work/<book>/`). Put a `PROGRESS.md` in it from the start: these jobs
span several sessions, and that file is how the next session knows where you stopped.

## Which path?

Check the font names first:
`python3 -c "import fitz;print({f[3] for p in fitz.open('x.pdf') for f in p.get_fonts()})"`

- **No fonts / pages are images** → scanned book, the [main path](#main-path-scanned-book).
- **Fonts named `ZTR…`** (cherrythitsar.org downloads; text selects as garbage) →
  [Legacy-font path](#legacy-font-path). No OCR, but still proofread.
- **Fonts named `WinInnwa`** (typed Word document, letter-size, text selects as ASCII like
  `qm;ykvif;ESif;armif`) → [WinInnwa path](#wininnwa-path). No OCR, but a full proofreading pass
  is still needed for the typist's own typos.

Then render a few pages (`pdftoppm -r 60 -f N -l N -png`) and note: whether pages are two-up, where
the story starts, which pages are full-page illustrations, which pages have an illustration sharing
the page with text, and what the running head, footer and any watermark say.

## Main path: scanned book

### 1. Page images
```
python3 $SK/prepare_scans.py book.pdf work/s [--twoup]
```
Writes `work/s/0001.png …`, one image per book page. Check that the cover is 0001 and that the
numbering follows the printed page numbers. Every later step refers to pages by these numbers.

**Check the two-up split before OCR.** The gutter detector sometimes cuts into the right-hand page:
the left page then carries a strip of the next one, and the next page loses the first 1–3 letters of
every line. List suspects (pages much wider than the median):
`python3 -c "from PIL import Image;import glob,statistics as s;w={f:Image.open(f).width for f in glob.glob('work/s/*.png')};m=s.median(w.values());print(sorted(f[-8:-4] for f,x in w.items() if x>1.08*m))"`
Look at each and re-crop those sheets by hand at the real gutter before making OCR batches. It is
far cheaper than repairing ~50 clipped pages afterwards.

### 2. OCR through Google Drive
Google Docs OCR reads Burmese far better than tesseract. Feed it small batches with a page marker
stamped on each page:
```
python3 $SK/make_ocr_batches.py work/s work/batches --per 10 --skip 1,2
```
Each page gets a `#P0042#` stamp; the marker survives OCR and is how text is matched back to pages.
`work/batches/hashes.txt` lists `<path> <sha256>` for each batch.

For each batch:
1. `mcp__Google_Drive__create_file` with `title: "bNN"`, `contentMimeType: "application/pdf"` and
   `base64Content: "sha256:<hash>:<absolute path>"`. Leave conversion on: converting to a Google Doc
   is what runs the OCR.
2. `mcp__Google_Drive__download_file_content` with the returned id exports plain text. Large exports
   come back as saved blob files: `python3 $SK/collect_ocr.py work/text` copies every blob to
   `work/text/pNNNN.txt`, named by its first marker, so download order doesn't matter.
3. When every batch is saved, trash the Drive docs with `mcp__Google_Drive__trash_file`.

**Size limit.** The connector refuses requests over ~4.2 MB (a batch PDF over ~3.1 MB). Check
`ls -l work/batches` first and rebuild big batches with `--per 5`. If a batch is refused, tell the
user; don't silently skip pages.

Without the Drive connector, the user can do the same by hand: upload each batch to Google Drive,
*Open with → Google Docs*, *File → Download → Plain text*, and save as `work/text/bNN.txt`.
Tesseract (`mya`) is a poor fallback; warn that the text will need far more fixing.

### 3. Configure and assemble
Copy `examples/config.json` into the work folder and fill it in (paths are relative to it):
- `titles`: page → chapter title, typed by hand from the contents page and chapter openings
  (`find_headings.py work/s` lists candidate heading lines). `""` = untitled scene break.
- `image_pages`: full-page illustrations; `skip`: blank, duplicated or misprinted pages.
- `running_heads`: regexes for page headers; `cleanup.strip`: regexes for footers, publisher
  marks and watermark text that leak into paragraphs.
- `headings`: `headings.json`, `[OCR text, correct title]` pairs for headings that sit mid-page and
  get glued into paragraphs.

Then build the draft:
```
python3 $SK/pipeline.py work/config.json
```
It runs assemble → re-attach quote attributions → insert headings → OCR cleanup → every edit file →
finalize. **Never edit blocks.json by hand.** All proofreading lives in edit files, so the whole
book can be regenerated any time (a re-OCR'd page, a new heading, a better cleanup rule) without
losing work. Read the `missing markers` line: a missing page usually means the OCR misread the
stamp; find that page's text by phrase and check it wasn't merged into the page before it.

Check the chapter count against the contents page now. Every missing heading means two chapters
are merged, and all later chapter indices are off by one.

### 4. Proofread chapter by chapter
This is most of the work, and it is what the book is judged on. **Read
`reference/proofreading.md` before starting.** It covers the edit-file format and markers, the
chapter loop, what OCR damage looks like (with real examples), retyping garbled pages from the
scans, misprints in the original book, and how to report guesses.

Work through every chapter; don't sample a few and call the book proofread. When the user reports
one error ("page 28 sentence order is wrong"), treat it as a pattern: fix it, then search the whole
book for the same thing.

### 5. Finalize
`finalize.json` (copy from `examples/`) holds book-wide finishing that isn't a text edit:
illustrations that share a page with text (`pictures`: page, crop band, anchor paragraph),
watermark trimming for full-page pictures (`full_page_trim`), sub-headings (`h2`), centred lines,
and book-wide name spellings (`replace`). `pipeline.py` runs it last.

### 6. Build
```
BOOK_AUTHOR="မင်းသိင်္ခ" bash $SK/build.sh work/blocks.json book.pdf out <FileStem> "<title line 1>" "<title line 2>" ["part label"] ["note"]
```
Produces `out/<Stem>_Kindle.pdf` (with bookmarks) and `out/<Stem>_text.txt`, then prints the body
font size the PDF actually rendered. The cover is page 1 of the source PDF (or a typographic cover
if it has no picture).

### 7. Check, then deliver
- `check_fontsize.py` (build.sh runs it) must report **12.0 pt** for every book in the series. If
  not, see "Shrunken text" below.
- Render 3–4 pages with PyMuPDF (`page.get_pixmap(dpi=80)`) and look at them: a chapter opening, a
  dense dialogue page, a picture page, and any page the user complained about. Confirm each fix is
  visible on the rendered page, not just present in the JSON.
- Bookmarks = chapters + 1 (the cover).
- Deliver the PDF and the text file, and list plainly:
  - pages retyped from the scans
  - words that are guesses
  - headings or lines restored that the OCR had dropped
  - defects in the printed book (missing or duplicated pages)
  - anything not yet done

## Shrunken text: always measure, never trust the CSS

Headless Chrome sometimes refuses to break a Burmese line at a plain space; that one line overflows
and Chrome scales **every page** down to fit it (books came out at 8, 8.5, 10.5 and 11 pt from the
same CSS). `kindle_typeset.py` prevents this by putting a zero-width space (U+200B) after every
space. If a book still measures under 12 pt, run `find_overflow.py out/<Stem>.html` to list the
overflowing elements and fix the cause; don't change the font size to compensate. More pages is the
expected cost of real 12 pt.

## WinInnwa path
```
python3 $SK/extract_wininnwa.py source.pdf work/blocks.json
```
`win_map.py` maps Win glyph codes to Unicode and reorders them (pre-base ေ/ြ after the consonant,
kinzi before it, canonical mark order; `]]`/`}}` → “ ”). The extractor prints the headings it found
and any unknown glyph codes; an unknown code is usually a rare stacked letter: find it in the PDF and
add it to `M`. Latin words typed in the Win font decode to Burmese nonsense (`(Kabala)` → `(ုဘေူ)`);
search for and retype them. Typical typist habits: `ဒေါ် ` + space + name, `လှု` for `လှူ`, `ဥ်` for
`ဉ်`. Then proofread (step 4) and finish with `typo_candidates.py blocks.json 4` and
`global_replace.py` for confirmed pairs. Here the edits apply straight to blocks.json with
`apply_edits.py` (there is no OCR draft to regenerate), so keep a copy of the extracted original.

## Legacy-font path
```
python3 $SK/extract_book.py source.pdf <first_story_page> work/blocks.json work/lineimg
```
Decodes ZTR glyph codes (`ztr_map.py`) and rebuilds headings, centred lines, paragraphs and
pictures from the PDF's layout. Lines it can't decode are kept as images (`img` blocks), so no text
is lost. Tuned on cherrythitsar PDFs: the `TOP`/`BOT` crop band and the `LATIN` font set may need
adjusting for a new source. Compare a few chapters with the PDF, then proofread (lighter, but quote
attributions and page furniture still need checking).

## Requirements
- `pdftoppm`/`pdftotext` (poppler-utils) and `google-chrome` (headless printing).
- Python: `pymupdf pypdf pillow numpy` (`playwright` only for `find_overflow.py`).
- Font: Padauk (`fonts-sil-padauk`). Check `fc-list | grep -i padauk`; Chrome silently falls back
  to another font if it's missing.
