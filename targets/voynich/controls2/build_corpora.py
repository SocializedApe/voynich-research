"""build_corpora.py -- word lists for the check-1 language controls (Turkic, Uralic, Austroasiatic, Sinitic, Semitic).

Sources: eBible.org "readaloud" zips (one plain-text file per chapter), downloaded by hand into data/_<id>.zip on
29 Oct 2026 (only redistributable or public-domain texts):
  turytc     Turkish WEB (2023-2025, Serinken / eBible.org), OT+NT
  hun        Hungarian Bible (Biblica 2021), NT only
  vie1934    Vietnamese Bible 1923/1934, public domain, OT+NT
  cmn-cu89s  Chinese Union Version (simplified), public domain, OT+NT
  arb-vd     Arabic Van Dyck Bible, public domain, fully vocalised, OT+NT

Writes data/<name>.txt, one token per space, one verse per line:
  turkish, hungarian        letters as written (lower case)
  vietnamese                syllables as written, with tone and vowel diacritics (Vietnamese spaces syllables)
  vietnamese_fold           same, diacritics removed (a-z plus d for d-stroke): a small-alphabet syllable script
  chinese_pinyin_syl        one toneless pinyin syllable per Han character (pypinyin, v -> u-umlaut written 'v')
  chinese_pinyin_word       jieba word segmentation, the word's toneless syllables written together
  arabic_voc                Van Dyck, letter-for-letter Latin transliteration with the short vowels written
  arabic_cons               same, consonantal skeleton only (as Arabic is normally written)
"""
import os, re, sys, zipfile, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data')


def chapters(tid):
    z = zipfile.ZipFile(os.path.join(D, f'_{tid}.zip'))
    names = sorted(n for n in z.namelist() if n.endswith('_read.txt') and '_000_000_000_' not in n)
    for n in names:
        yield z.read(n).decode('utf-8-sig', 'replace')


def verses(tid):
    for ch in chapters(tid):
        lines = [l.strip() for l in ch.split('\n') if l.strip()]
        for l in lines[2:]:          # line 1 book title, line 2 chapter number
            yield l


def write(name, lines):
    lines = [l for l in lines if l]
    with open(os.path.join(D, name + '.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(name, len(lines), 'lines', sum(len(l.split()) for l in lines), 'tokens')


WORD = re.compile(r"[^\W\d_]+")


def plain(tid, fold=False):
    for v in verses(tid):
        v = v.lower()
        if fold:
            v = v.replace('đ', 'd')
            v = ''.join(c for c in unicodedata.normalize('NFD', v) if unicodedata.category(c) != 'Mn')
        yield ' '.join(WORD.findall(v))


def chinese(by_word):
    import pypinyin, jieba
    jieba.setLogLevel(60)
    han = re.compile(r'[一-鿿]+')
    for v in verses('cmn-cu89s'):
        out = []
        for run in han.findall(v):
            units = jieba.lcut(run) if by_word else list(run)
            for u in units:
                syl = pypinyin.lazy_pinyin(u, style=pypinyin.Style.NORMAL, v_to_u=False)
                out.append(''.join(s for s in syl if s.isalpha()))
        yield ' '.join(w for w in out if w)


# Arabic: one Latin symbol per Arabic letter (several are accented letters, so no letter is a digraph)
AR = {'ا': 'â', 'ٱ': 'â', 'آ': 'eâ', 'أ': 'e', 'إ': 'e', 'ء': 'e', 'ؤ': 'e', 'ئ': 'e', 'ب': 'b', 'ت': 't', 'ث': 'þ',
      'ج': 'j', 'ح': 'ḥ', 'خ': 'x', 'د': 'd', 'ذ': 'ð', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'š', 'ص': 'ṣ', 'ض': 'ḍ',
      'ط': 'ṭ', 'ظ': 'ẓ', 'ع': 'c', 'غ': 'g', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h',
      'و': 'w', 'ي': 'y', 'ى': 'à', 'ة': 'ŧ'}
VOW = {'َ': 'a', 'ِ': 'i', 'ُ': 'u', 'ً': 'an', 'ٍ': 'in', 'ٌ': 'un', 'ٰ': 'â'}
SUKUN, SHADDA = 'ْ', 'ّ'


def arabic_word(w, vowels):
    out = []
    for c in w:
        if c in AR:
            out.append(AR[c])
        elif c == SHADDA:
            if out:
                out.append(out[-1][-1])   # doubled consonant (written in both forms: it is a letter sign)
        elif c in VOW:
            if vowels:
                out.append(VOW[c])
        # sukun, tatweel and other marks dropped
    return ''.join(out)


def arabic(vowels):
    tok = re.compile(r'[ء-ْٰٱ]+')
    for v in verses('arb-vd'):
        yield ' '.join(x for x in (arabic_word(w, vowels) for w in tok.findall(v)) if x)


def main():
    write('turkish', plain('turytc'))
    write('hungarian', plain('hun'))
    write('vietnamese', plain('vie1934'))
    write('vietnamese_fold', plain('vie1934', fold=True))
    write('chinese_pinyin_syl', chinese(False))
    write('chinese_pinyin_word', chinese(True))
    write('arabic_voc', arabic(True))
    write('arabic_cons', arabic(False))


if __name__ == '__main__':
    main()
