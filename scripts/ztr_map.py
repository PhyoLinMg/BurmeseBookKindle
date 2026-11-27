"""ZTR legacy Burmese font (cherrythitsar PDFs) -> Unicode.
Glyph codes are in visual order (pre-base ေ / ြ come first)."""
import re

M = {
    0x20: ' ',
    # consonants
    0xAB: 'က', 0xBD: 'ခ', 0xF6: 'ဂ', 0xBE: 'ဘ', 0xB7: 'င', 0xB0: 'စ', 0xAF: 'ဆ', 0xC6: 'ဇ',
    0xB2: 'ည', 0x2F: 'ည', 0xA9: 'တ', 0xA8: 'ထ', 0xF9: 'ဒ', 0x6C: '္ဒ', 0x7D: 'ဣ', 0xFE: 'ဓ', 0xA5: 'ဧ',
    0xDB: 'န', 0xBB: 'န', 0xA7: 'ပ', 0xA6: 'ဖ', 0xDF: 'ဗ', 0xAE: 'မ', 0xF4: 'ယ', 0xDD: 'ဃ',
    0xFA: 'ရ', 0x63: 'ရ', 0xAA: 'လ', 0xF0: 'ဝ', 0xB1: 'သ', 0xC5: 'ဟ', 0xAC: 'အ', 0xD1: 'ဥ',
    0xD0: 'ဏ', 0x4D: 'ဉာ', 0xA4: 'ဋ္ဌ', 0xE0: 'ဏ္ဍ', 0x22: 'ဤ', 0x24: '၌', 0x7C: '၎', 0xC8: 'ဌ', 0xCA: 'ဠ', 0xFD: 'ဋ', 0x67: 'ဍ္ဎ', 0x53: 'ဉ',
    # dependent vowels & marks
    0xB3: 'ာ', 0xB9: 'ါ', 0xBC: 'ိ', 0xDC: 'ီ', 0xB5: 'ု', 0xD5: 'ု', 0xB4: 'ူ', 0xD4: 'ူ', 0xD7: 'ှု',
    0xBF: 'ေ', 0xD6: 'ဲ', 0xD8: 'ံ', 0xBA: '်', 0xE5: 'း',
    0xB8: '့', 0xC7: '့', 0xF2: '.', 0xCB: '့',
    0xAD: 'ျ', 0xB6: 'ြ', 0xC0: 'ြ', 0xD2: 'ြ', 0xD3: 'ြ', 0xDE: 'ြ',
    0xD9: 'ွ', 0xCD: 'ှ', 0xCE: 'ျွ', 0xCF: 'ျှ', 0xCC: 'ွှ',
    0xC4: '၏', 0xE6: 'ါ်', 0x48: 'င်္ိ', 0x50: 'င်္ီ', 0x79: 'ှ', 0xE2: '', 0xE4: '', 0x2D: 'ျ', 0x33: '၍', 0xDA: 'င်္',
    # stacked (subscript) consonants
    0x26: '္က', 0x77: '္ခ', 0x62: '္ဂ', 0x2A: '္စ', 0x3C: '္ဆ', 0x5A: '္ဇ', 0x3B: '္တ', 0x74: '္ထ',
    0x6E: '္ဌ', 0x5B: '္တ', 0x78: '္ဓ', 0x37: '္န', 0x44: '္ပ', 0x5F: '္ဗ', 0x59: '္ဘ', 0x72: '္မ', 0x8E: '္လ',
    # punctuation / digits
    0xF1: '။', 0xE1: '၊', 0xC3: '‘', 0xA3: '’', 0x39: '’', 0xC1: '?', 0xF3: '-', 0xF7: ')', 0xF8: '(',
    0xC2: '/', 0x5C: '*',
    0xEF: '၁', 0xEE: '၂', 0xED: '၃', 0xEC: '၄', 0xEB: '၅', 0xEA: '၆', 0xE9: '၇', 0xE8: '၈', 0xE7: '၉',
}
DIGITS = '၀၁၂၃၄၅၆၇၈၉'
UNKNOWN = set()

def decode_raw(s):
    out = []
    for ch in s:
        c = ord(ch)
        if c >= 0xF000: c -= 0xF000
        elif c > 255: c = ch.encode('cp1252')[0]
        if c in M: out.append(M[c])
        else:
            UNKNOWN.add(c); out.append(f'⟨{c:02X}⟩')
    return ''.join(out)

CONS = 'က-အဿ'
def reorder(t):
    # ဝ vs ၀ (digit zero)
    for _ in range(4):
        t = re.sub(r'(?<=[၀-၉/\-])ဝ|ဝ(?=[၀-၉/])', '၀', t)
    # visual pre-base: ေ? ြ? C  ->  C ြ ... ေ
    t = re.sub(r'(ေ)?(ြ|)?((?:င်္)?[' + CONS + r'](?:္[' + CONS + r'])?)', lambda m: (m.group(3) + (m.group(2) or '').replace('', 'ြွ') + (m.group(1) or '')) if (m.group(1) or m.group(2)) else m.group(0), t)
    t = t.replace('', 'ြွ')
    # kinzi drawn above following consonant: C + င်္  -> င်္ + C
    t = re.sub(r'([' + CONS + r'](?:္[' + CONS + r'])?)([ျြွှေ]*)(င်္)', r'\3\1\2', t)
    # canonical order of marks after base: medials ျ ြ ွ ှ, then ေ, then vowels
    def canon(m):
        base, marks = m.group(1), m.group(2)
        order = 'ျြွှေိီုူဲံ့်း'
        # keep asat/dot relative order sensible: ့ before ် per Unicode
        ms = sorted(marks, key=lambda c: order.index(c) if c in order else 99)
        s = ''.join(ms)
        s = s.replace('့်', '့်')
        s = s.replace('့်', '့်')
        return base + s
    t = re.sub(r'([' + CONS + r'](?:္[' + CONS + r'])?)([ျြွှေိီုူဲံ့်း]+)', canon, t)
    # Unicode wants ့ after ် ? no: standard is  ် before ့? Unicode storage: ့ (1037) precedes ် (103A)
    t = t.replace('ါ့်', 'ါ့်')
    # ေ + ါ/ာ + ် ordering ok. collapse doubles
    t = re.sub(r'([ါာိီုူဲံ့်း])\1+', r'\1', t)
    t = t.replace('နု်ပ်', 'န်ုပ်')
    t = t.replace('‘‘', '“').replace('’’', '”')
    t = re.sub(r'“+', '“', t); t = re.sub(r'”+', '”', t)
    # ဥ + ် often stands for ဉ်
    t = t.replace('ဥ်', 'ဉ်')
    # ဦ
    t = t.replace('ဦ', 'ဦ')
    return t

def decode(s):
    return reorder(decode_raw(s))
