"""Phase 2 corpora: a typologically wide set of natural-language texts. (11 Nov 2026)

Source: the multilingual Bible corpus of Christodouloupoulos & Steedman (2015), github.com/christos-c/bible-corpus
(CC0), one XML file per language, verses in <seg> elements. For each language in LANGS the first WORDS words are
kept as plain text, one verse a line, in data/external/bible/<Language>.txt (git-ignored). Languages written without
spaces use the corpus's tokenised versions. One genre for every language is deliberate (it holds content constant
across languages); other genres come from the texts already in the repository (see build.py).

Run from targets/voynich: python phase2/corpora2.py
"""
import os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'data', 'external', 'bible')
WORDS = 40000
LANGS = ['Latin', 'Italian', 'Spanish', 'French', 'Portuguese', 'Romanian', 'German', 'Dutch', 'English', 'Danish', 'Swedish', 'Icelandic', 'Greek',
         'Russian', 'Czech', 'Polish', 'Croatian', 'Bulgarian', 'Lithuanian', 'Albanian', 'Hungarian', 'Finnish', 'Turkish', 'Hebrew', 'Arabic',
         'Syriac-NT', 'Amharic', 'Coptic-NT', 'Farsi', 'Hindi', 'Telugu', 'Malayalam', 'Korean', 'Vietnamese-tok', 'Chinese-tok', 'Thai-tok',
         'Indonesian', 'Tagalog', 'Cebuano', 'Maori', 'Malagasy', 'Swahili-NT', 'Xhosa', 'Somali', 'Shona', 'Nahuatl-NT', 'Quichua-NT', 'Basque-NT',
         'Esperanto', 'Afrikaans']
WORD = re.compile(r'[^\W\d_]+', re.UNICODE)


def main():
    os.makedirs(OUT, exist_ok=True)
    for lang in LANGS:
        dest = os.path.join(OUT, lang + '.txt')
        if os.path.exists(dest):
            continue
        url = 'https://raw.githubusercontent.com/christos-c/bible-corpus/master/bibles/' + urllib.request.quote(lang) + '.xml'
        for i in range(4):
            try:
                xml = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'voynich-research'}), timeout=120).read(); break
            except Exception as e:
                xml = None; time.sleep(5)
        if xml is None:
            print('FAILED', lang, flush=True); continue
        n = 0; lines = []
        for seg in ET.fromstring(xml).iter('seg'):
            ws = WORD.findall((seg.text or '').lower())
            if ws:
                lines.append(' '.join(ws)); n += len(ws)
            if n >= WORDS:
                break
        open(dest, 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); print(lang, n, 'words', flush=True)


if __name__ == '__main__':
    main()
