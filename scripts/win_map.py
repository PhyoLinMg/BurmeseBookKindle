"""WinInnwa (and the other "Win" family fonts: Win Researcher, Win Kalaw ...) -> Unicode.
These are typed-Word-document PDFs (fonts named WinInnwa) where the text selects as ASCII
garbage like "qm;ykvif;ESif;armif". Glyph codes are in visual order: pre-base ေ (a) and
ြ (j M N B) come before the consonant, kinzi (F) after it.
usage (as a module): from win_map import decode; decode(raw)
usage (CLI):         win_map.py "raw text"   -> prints Unicode"""
import re, sys

M = {
    # consonants
    'u': 'က', 'c': 'ခ', '*': 'ဂ', 'C': 'ဃ', 'i': 'င', 'p': 'စ', 'q': 'ဆ', 'Z': 'ဇ', 'n': 'ည',
    '#': 'ဋ', 'X': 'ဌ', '!': 'ဍ', 'P': 'ဏ', 'w': 'တ', 'x': 'ထ', "'": 'ဒ', '"': 'ဓ',
    'e': 'န', 'E': 'န', 'y': 'ပ', 'z': 'ဖ', 'A': 'ဗ', 'b': 'ဘ', 'r': 'မ', ',': 'ယ',
    '&': 'ရ', '½': 'ရ', 'v': 'လ', '0': 'ဝ', 'o': 'သ', '[': 'ဟ', 'V': 'ဠ', 't': 'အ',
    'O': 'ဥ', '{': 'ဧ', 'þ': 'ဤ', 'ó': 'ဿ', '@': 'ဏ္ဍ',
    # dependent vowels and marks
    'm': 'ာ', 'g': 'ါ', ':': 'ါ်', 'd': 'ိ', 'D': 'ီ', 'k': 'ု', 'K': 'ု', 'l': 'ူ', 'L': 'ူ',
    'a': 'ေ', 'J': 'ဲ', 'H': 'ံ', 'f': '်', ';': 'း', 'h': '့', 'Y': '့', 'U': '့',
    # medials
    's': 'ျ', 'j': 'ြ', 'M': 'ြ', 'N': 'ြ', 'B': 'ြ', 'G': 'ွ', 'S': 'ှ',
    'R': 'ျွ', 'Q': 'ျှ', 'T': 'ွှ', 'I': 'ှု', 'W': 'ွှ',
    'F': 'င်္',   # kinzi, drawn after the consonant it belongs before
    # stacked (subscript) consonants
    'ú': '္က', '©': '္ခ', '¾': '္ဂ', '¢': '္ဃ', 'ö': '္စ', 'ä': '္ဆ', 'Æ': '္ဇ',
    'å': '္တ', 'Å': '္တ', '¦': '္ထ', '´': '္ဒ', '¨': '္ဓ', 'é': '္န', 'Ö': '္ဏ',
    'Ü': '္ပ', 'Á': '္ဗ', 'Ç': '္ဘ', '®': '္မ',
    # punctuation and digits
    '/': '။', '?': '၊', '\\': '၏', 'í': '၍', 'ü': '၌', '4': '၄',
    '1': '၁', '2': '၂', '3': '၃', '5': '၅', '6': '၆', '7': '၇', '8': '၈', '9': '၉',
}
UNKNOWN = {}

def decode_raw(s):
    s = s.replace('‘', '')   # stray Windows quote typed next to ]] in some files
    s = s.replace(']]', '“').replace('}}', '”').replace(']', '‘').replace('}', '’')
    out = []
    for ch in s:
        if ch in M: out.append(M[ch])
        elif ch in ' ().-“”‘’' or ch.isspace(): out.append(ch)
        else: UNKNOWN[ch] = UNKNOWN.get(ch, 0) + 1; out.append(ch)
    return ''.join(out)

CONS = 'က-အဿဣ-ဧ'
C1 = '(?:[' + CONS + '](?:္[' + CONS + '])?|ဏ္ဍ)'
ORDER = 'ျြွှေိီဲုူါာံ့်း'

def reorder(t):
    # digit zero vs letter wa
    for _ in range(3):
        t = re.sub(r'(?<=[၀-၉])ဝ|ဝ(?=[၀-၉])', '၀', t)
    # pre-base ေ / ြ in front of the consonant -> after it
    t = re.sub(r'([ေြ]+)(' + C1 + ')', lambda m: m.group(2) + m.group(1), t)
    # subscript typed after the vowel signs (e.g. န ီ ္ဒ) -> right after its consonant
    t = re.sub(r'([' + CONS + r'])([ိီုူဲံ့]+)(္[' + CONS + r'])', r'\1\3\2', t)
    # kinzi after its consonant -> before it
    t = re.sub(r'(' + C1 + r')([' + ORDER + r']*)(င်္)', r'\3\1\2', t)
    # canonical order of the marks that follow a consonant
    def canon(m):
        ms = sorted(m.group(2), key=lambda c: ORDER.index(c))
        s = re.sub(r'(.)\1+', r'\1', ''.join(ms))
        return m.group(1) + s
    t = re.sub(r'(' + C1 + ')([' + ORDER + ']+)', canon, t)
    t = t.replace('ဥ်', 'ဉ်').replace('ဥ္', 'ဉ္').replace('ဦ', 'ဦ').replace('ဦ', 'ဦ')
    t = t.replace('နု်ပ်', 'န်ုပ်')
    t = re.sub(r'(^|[\s(“‘])၄င်း', r'\1၎င်း', t)
    t = re.sub(r'“\s+', '“', t); t = re.sub(r'\s+”', '”', t)
    return t

def decode(s):
    return reorder(decode_raw(s))

if __name__ == '__main__':
    print(decode(' '.join(sys.argv[1:])))
