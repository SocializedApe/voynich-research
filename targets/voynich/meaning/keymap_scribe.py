"""Within one scribe: are his two styles one system under two keys? (keymap.py at the scribe level)

scribes.py found that Davis's hand 1 writes two styles (herbal A vs pharmaceutical) and hand 2 two (herbal B vs
biological). If one style is the other with a changed glyph-for-glyph key, keymap.compare finds a mapping that closes
most of the gap to the noise floor; if not, the two styles are different systems within one hand.
Size 3,000 words a side (the pharmaceutical section is short); controls at the same size: herbal A of hand 1 half
against half (identity should be best) and Pliny against itself under a random letter key (mapping must close it).
Cross-scribe pair at the same size for reference: hand 1 herbal against hand 2 herbal.

Run from the repository root: python targets/voynich/meaning/keymap_scribe.py
"""
import csv, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import keymap, pliny

keymap.NW = 3000


def main():
    rng = random.Random(23)
    W = {}
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'ZL3b-n.fixed.words.tsv'), encoding='utf-8'), delimiter='\t'):
        if r['locus_type'] == 'P':
            W.setdefault((r['hand'], r['illus']), []).extend(w for w in r['line_words'].split() if re.fullmatch(r'[a-z]+', w))
    print('words:', {k: len(v) for k, v in W.items() if len(v) >= 2000})
    h1H, h1P, h2H, h2B = W[('1', 'H')], W[('1', 'P')], W[('2', 'H')], W[('2', 'B')]
    keymap.compare('hand 1: herbal A vs pharmaceutical', h1H, h1P, keymap.units_voy, rng)
    keymap.compare('hand 2: herbal B vs biological', h2H, h2B, keymap.units_voy, rng)
    keymap.compare('hand 1 herbal vs hand 2 herbal (other scribe)', h1H, h2H, keymap.units_voy, rng)
    keymap.compare('control: hand 1 herbal, half vs half', h1H[:len(h1H) // 2], h1H[len(h1H) // 2:], keymap.units_voy, rng)
    lat = [w for b in pliny.STREAM for c in pliny.chapters(b) for w in pliny.latin_words(c)]
    alpha = sorted(set(''.join(lat))); key = dict(zip(alpha, random.Random(3).sample(alpha, len(alpha))))
    keymap.compare('control: Pliny vs Pliny under a random key', lat[:20000], [''.join(key[c] for c in w) for w in lat[20000:40000]], keymap.units_let, rng)


if __name__ == '__main__':
    main()
