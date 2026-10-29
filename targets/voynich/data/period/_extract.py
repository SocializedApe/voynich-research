"""Build the 14th-15th-century "period cipher" control set for the Voynich work.

Reads the transcriptions kept in this repository's own target folders (targets/<target>/...) and writes one
JSON per cipher system into this folder (targets/voynich/data/period/), plus nothing else. Deterministic: no
randomness, no network, no writes outside this folder. Run from anywhere:

    PYTHONUTF8=1 python targets/voynich/data/period/_extract.py

Token conventions (all files):
  * one token per cipher sign, in reading order, using the target's own sign ids;
  * "|"      a separator the scribe wrote (word points, dot groups, // strokes ...); never a cipher letter;
  * "N:x"    sign x is a nomenclator/code sign (a name or a whole word: also the word signs for et/che), as the
             target's key, gloss or reading says;
  * "0:x"    sign x is a null, as the target's key says;
  * clear (non-cipher) text is left out; a cipher run between clear words is its own line;
  * an illegible or lost sign ends the line there (the rest becomes a new line, id suffixed a, b, ...), so that
    no false sign pair is created across a gap; a sign the transcriber marked doubtful ("X?") is kept as X.
Plaintext: lowercase a-z and spaces only; editorial insertions/expansions in ( ) or [ ], unread signs, code
expansions and clear words are left out.
"""
import collections
import csv
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]          # repository root (…/targets/voynich/data/period -> …)
T = ROOT / 'targets'
GAP = object()                  # line break caused by clear text, an illegible sign or a struck passage


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def read(p):
    return Path(p).read_text(encoding='utf-8')


# ----------------------------------------------------------------------------------------------- helpers
class Stats(collections.Counter):
    pass


def segments(line_id, toks):
    """Split a token list at GAP markers; trim/collapse separators; drop empty segments."""
    segs, cur = [], []
    for t in toks + [GAP]:
        if t is GAP:
            while cur and cur[0] == '|':
                cur.pop(0)
            while cur and cur[-1] == '|':
                cur.pop()
            out = []
            for x in cur:
                if x == '|' and out and out[-1] == '|':
                    continue
                out.append(x)
            if any(x != '|' for x in out):
                segs.append(out)
            cur = []
        else:
            cur.append(t)
    if len(segs) <= 1:
        return [(line_id, s) for s in segs]
    return [(f'{line_id}{chr(97 + i)}', s) for i, s in enumerate(segs)]


def strip_q(tok, st, keep=()):
    """Remove a trailing doubt mark '?' (counted), unless the sign id itself ends in '?'."""
    if tok in keep:
        return tok
    if tok.endswith('?') and tok.rstrip('?'):
        st['doubtful_signs_kept'] += 1
        return tok.rstrip('?')
    return tok


def deaccent(s):
    s = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in s if not unicodedata.combining(c))


def join_lines(lines):
    """Join reading lines, closing words split as 'respon-' / '-dit'."""
    out = ''
    for l in lines:
        l = l.strip()
        if not l:
            continue
        if out.endswith('-'):
            out = out[:-1] + l.lstrip('-')
        else:
            out = (out + ' ' + l.lstrip('-')) if out else l.lstrip('-')
    return out


def norm_plain(s):
    s = re.sub(r'\{[^}]*\}', ' ', s)            # tags / glosses
    s = re.sub(r'<[^>]*>', ' ', s)              # code expansions
    s = re.sub(r'\[[^\]]*\]', '', s)            # unread or editorially supplied letters, clear notes
    s = re.sub(r'\([^)]*\)', '', s)             # expansions of abbreviations, doubt marks, comments
    s = deaccent(s).lower()
    s = re.sub(r'[^a-z\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def load_key(path):
    key = {}
    for l in read(path).splitlines():
        l = l.strip()
        if not l or l.startswith('//') or l.startswith('#') and '=' not in l[1:]:
            continue
        if '=' in l:
            k, v = l.rsplit('=', 1)
            if k.strip():
                key[k.strip()] = v.strip()
    return key


def counts(lines):
    toks = [t for l in lines for t in l]
    signs = [t for t in toks if t != '|']
    base = lambda t: t[2:] if t[:2] in ('N:', '0:') else t
    letters = [t for t in signs if t[:2] not in ('N:', '0:')]
    codes = [t for t in signs if t[:2] == 'N:']
    nulls = [t for t in signs if t[:2] == '0:']
    return {
        'lines': len(lines),
        'sign_tokens': len(signs),
        'distinct_signs': len(set(map(base, signs))),
        'letter_sign_tokens': len(letters),
        'distinct_letter_signs': len(set(letters)),
        'code_sign_tokens': len(codes),
        'distinct_code_signs': len(set(codes)),
        'null_tokens': len(nulls),
        'distinct_nulls': len(set(nulls)),
        'dividers': toks.count('|'),
    }


# ----------------------------------------------------------------------------------------------- targets
def benedict1399():
    """Reconstructed from Puig's text + the key rebuilt from the p. 475 plate (word-by-word check file)."""
    src = T / 'benedict1399/src/plate475_check.tsv'
    key_md = T / 'benedict1399/key.md'
    reveal = ROOT / 'docs/reveal/benedict1399.json'
    # Sign names as in key.md's table and docs/reveal/benedict1399.json (c and i share 'o'; u and v share 'cb').
    KEY = {'a': 'ɣ', 'b': 'Ƭ', 'c': 'o', 'd': '‡', 'e': 'δ', 'f': 'Ϭ', 'g': 'ɕ', 'h': 'ʓ', 'i': 'o', 'l': 'ϑ',
           'm': 'ɛ', 'n': 'n', 'o': 'ꝏ', 'p': '⊥', 'q': '⊧', 'r': 'ı', 's': 'T', 't': 'c′', 'u': 'cb', 'v': 'cb',
           'x': 'ɑ'}
    for t in json.loads(read(reveal))['tokens']:            # cross-check against the sign-by-sign line 24
        if t.get('g') and t['p'] != '?':
            assert KEY[t['p']] == t['g'], (t, KEY[t['p']])
    st = Stats()
    runs = collections.OrderedDict()
    for l in read(src).splitlines():
        if not l.strip() or l.startswith('#'):
            continue
        f = l.split('\t')
        line, run, word, status = f[0], f[1], f[2], f[3]
        runs.setdefault(run, []).append((word, status))
    lines, ids, plain = [], [], []
    for run, words in runs.items():
        toks = []
        for word, status in words:
            if status == 'n':                                 # not legible on the plate: gap
                toks.append(GAP)
                st['words_dropped_illegible'] += 1
                continue
            if status == 'p':
                st['words_partly_seen'] += 1
            if word == 'K':
                toks.append('N:V̇')
            elif word == 'SEP':
                toks.append('0:SEP')
            else:
                toks += [KEY[c] for c in word.lower()]
                plain.append(word.lower())
        for lid, seg in segments(run, toks):
            ids.append(lid)
            lines.append(seg)
    return dict(
        target='benedict1399', dataset='benedict1399',
        piece="Benedict XIII to Francesc Climent, Avignon 22 June 1400 (Puig 1920 app. XXXV), last page",
        date='22 June 1400', year=1400, date_basis='dated in the letter',
        shelfmark="Arxiu Capitular de Barcelona, Cisma d'Occident, Çapera doc. 1068; the only image is the "
                  "photogravure in S. Puig y Puig, Pedro de Luna (1920), p. 475",
        system="Simple substitution, one invented sign per letter (c and i share one sign, u/v one), no word "
               "division, cipher runs inside clear Latin; one name sign (dotted V = King of Aragon) and groups of "
               "null separator signs. Puig broke it in 1920; key rebuilt here from the plate.",
        language='Latin', outcome='read (Puig 1920; plate checked sign by sign, 91.4% of letters confirmed)',
        sign_inventory_note=(
            "RECONSTRUCTED, not transcribed: every cipher word on the plate whose status in plate475_check.tsv "
            "is y (every sign seen and fits the key) or p (partly seen) was re-enciphered from Puig's printed "
            "word with the key of key.md; sign ids are the glyph names used in key.md and "
            "docs/reveal/benedict1399.json (checked against the sign-by-sign line 24 there). N:V̇ = the dotted-V "
            "King-of-Aragon sign (Puig 'K'); 0:SEP = one group of lambda/ʒ/ɑ-like separator signs (count of "
            "signs inside each group not recorded). Runs R1-R5 are the cipher runs between clear Latin; R2 is "
            "split where line 4's overwritten stretch is not legible."),
        lines=lines, line_ids=ids,
        plaintext=norm_plain(' '.join(plain)),
        plaintext_source="Puig y Puig 1920 italics as checked word by word in plate475_check.tsv (three "
                         "corrections there: tenendum, absque congedio, necessaria)",
        source_files=[rel(src), rel(key_md), rel(reveal), rel(T / 'benedict1399/NOTES.md')],
        caveats=[
            "Ciphertext is reconstructed from plaintext + key, so it has no scribal slips, and the c/i and u/v "
            "mergers are the key's; the one unexplained extra stroke in 'istorum' (line 24) is not included.",
            f"{st['words_partly_seen']} words were only partly visible on the 1920 halftone (status p) and "
            f"{st['words_dropped_illegible']} words of line 4 (overwritten) are left out.",
            "Separator groups are single 0:SEP tokens; their internal signs are not transcribed.",
            "Only the last page of one letter is imaged anywhere; the other ten letters' ciphertext is not."],
        _stats=st)


def siena_no14():
    f = T / 'siena14/transcripts/no14_reading2.txt'
    rows = read(f).splitlines()
    st = Stats()
    DROP = {'BAR', 'DASH', 'SLASH', 'ITICK', 'TILDE'}       # marks, not signs (as the target's prep14.py)
    lines, ids, plain_lines, misaligned = [], [], [], []
    for i, l in enumerate(rows):
        m = re.match(r'^(L\d+) SIGNS: (.*)$', l)
        if not m:
            continue
        lid, sig = m.group(1), m.group(2)
        tm = re.match(r'^\s+TEXT:\s+(.*)$', rows[i + 1]) if i + 1 < len(rows) else None
        sig = re.sub(r'\{[^}]*\}', ' ', sig)
        words, cur = [], []
        for t in sig.split():
            if t == '/':                       # word point; the TEXT line has one entry per '/'-word
                words.append(cur)
                cur = []
            else:
                cur.append(t)                  # ':' and '::' stay inside the entry, become '|' below
        words.append(cur)
        words = [w for w in words if w]
        text = [e.strip() for e in tm.group(1).split(' | ')] if tm else []
        aligned = len(text) == len(words)
        if not aligned:
            misaligned.append(lid)
        toks, ptoks = [], []
        for k, w in enumerate(words):
            entry = text[k] if aligned else ''
            is_code = '{code}' in entry
            out = []
            for t in w:
                if t in (':', '::'):
                    out.append('|')
                    continue
                if t.startswith('??'):
                    out.append(GAP)
                    st['illegible_signs'] += 1
                    continue
                if t == 'BLOT':
                    st['struck_signs_dropped'] += 1
                    continue
                t = t.lstrip('^')
                if t.startswith('PLUS^dot'):
                    base = 'PD'
                    if t.endswith('?'):
                        st['doubtful_signs_kept'] += 1
                else:
                    base = t.split('^')[0]
                    base = strip_q(base, st, keep=('N?',))
                if base in DROP:
                    st['marks_dropped'] += 1
                    continue
                # CIRC (circled figure) is the reading's code <13> inside 'dispac(c)iati da <13>' (L21)
                out.append('N:' + base if is_code or base == 'CIRC' else base)
            if toks:
                toks.append('|')
            toks += out
            if aligned and '{x}' not in entry and not is_code:
                ptoks.append(entry.replace('{?}', ''))
        for sid, seg in segments(lid, toks):
            ids.append(sid)
            lines.append(seg)
        plain_lines.append(' '.join(ptoks))
    assert not misaligned, misaligned
    return dict(
        target='siena1421', dataset='siena1421_no14',
        piece="Sienese envoys (subscribed 'Marco'?) to the Priori and Capitano del Popolo of Siena, no. 14",
        date='undated, c. 1409-1429 (Carlo Malatesta alive)', year=1420, date_basis='content (NOTES); 1420 is a placeholder',
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", no. 14 (DECODE R4802)',
        system="Italian; substitution with a few homophones (e, o, i, a), a point after every cipher word, two or "
               "three code signs for persons (7H, Z7, CIRC) and numbers in cipher digits; key recovered "
               "ciphertext-only here (homsolve2).",
        language='Italian', outcome='read in part (58.6% of tokens in words read as sense, 29.2% doubtful)',
        sign_inventory_note=(
            "Sign names of transcripts/no14_reading2.txt (second reading pass, corrected SIGNS lines: TH, DL, PHI, "
            "F, M, X added; former D/OSTEM split). Normalised as the target's prep14.py: PLUS^dot -> PD, other "
            "^tick/^arch/^curl/^tilde/^m/^bar marks stripped (arcs are abbreviation marks), BAR/DASH/SLASH/ITICK/"
            "TILDE dropped as marks, BLOT (struck sign) dropped. 'N?' is a sign name (n with a loop = u/v), not "
            "doubt. '|' = the scribe's word points (and the ':' / '::' marks). N: = every sign of a cipher word "
            "the reading tags {code} (<7H>, <Z7>, and the numerals (420) = LP Q4 2 O PAREN and 10 = L O), plus "
            "the circled figure CIRC, read as the code <13> inside a longer word on L21."),
        lines=lines, line_ids=ids,
        plaintext=norm_plain(join_lines(plain_lines)),
        plaintext_source="TEXT lines of no14_reading2.txt: words read as sense and doubtful words ({?}); unread "
                         "({x}) and code words left out",
        source_files=[rel(f), rel(T / 'siena14/prep14.py'), rel(T / 'siena14/NOTES.md'),
                      rel(T / 'siena14/profile.json')],
        caveats=[
            "Date not fixed: placed c. 1409-29 from content only (Carlo Malatesta alive).",
            "Only 58.6% of tokens are in words read as sense; 29% sit in words with a doubtful letter.",
            f"{st['illegible_signs']} illegible signs (paper damage, blots) end lines; "
            f"{st['doubtful_signs_kept']} signs the transcriber marked doubtful are kept.",
            "Look-alike glyph splits (8 vs TH, B vs DL, Q/Q4/PHI) were settled only in the second pass; "
            "Q and Q4 may not be kept apart by the scribe."],
        _stats=st)


def siena_no25():
    f = T / 'siena25/transcripts/no25_reading.txt'
    body = read(f).split('PER LINE (corrected signs -> Italian)')[1].split('RUNNING TEXT')[0]
    rows = body.splitlines()
    st = Stats()
    lines, ids, plain = [], [], []
    for i, l in enumerate(rows):
        m = re.match(r'^(L\d+) (.*)$', l)
        if not m:
            continue
        lid, sig = m.group(1), m.group(2)
        st['struck_groups_dropped'] += len(re.findall(r'\[struck[^\]]*\]', sig))
        sig = re.sub(r'\[struck[^\]]*\]', ' ', sig)
        toks = []
        for t in sig.split():
            if t == '/':
                toks.append('|')
            elif t == 'TH':
                toks.append('N:TH')
            else:
                toks.append(strip_q(t, st))
        for sid, seg in segments(lid, toks):
            ids.append(sid)
            lines.append(seg)
        plain.append(rows[i + 1].replace(' / ', ' ').replace('[TH]', ' '))
    return dict(
        target='siena1421', dataset='siena1421_no25',
        piece="Sienese envoys to the Signoria of Siena (a lord's route by Laiatico, Radicondoli, Casole), no. 25",
        date='undated', year=None, date_basis="none: no date, name or hand estimate recorded; the fascicle's dated pieces run 1421-1547",
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", no. 25 (DECODE R4813)',
        system="Italian (Sienese spelling); simple monoalphabetic substitution, one sign per letter, 21 signs built "
               "on a running horizontal stroke, a point after each cipher word, one code sign (TH); key "
               "recovered ciphertext-only here.",
        language='Italian', outcome='read (96.2% of signs in words read as sense)',
        sign_inventory_note=(
            "Sign names of transcripts/no25_reading.txt, 'PER LINE' section (rev. 2: Y = m and X = r split, G "
            "withdrawn). '|' = the scribe's word points. N:TH = the single code/abbreviation sign standing alone "
            "between points. The struck group on L06 (X3 R PI 9 S, 'quelo') is left out."),
        lines=lines, line_ids=ids,
        plaintext=norm_plain(join_lines(plain)),
        plaintext_source="per-line Italian of no25_reading.txt (rev. 2)",
        source_files=[rel(f), rel(T / 'siena25/transcripts/no25.txt'), rel(T / 'siena25/keys/no25_key.txt'),
                      rel(T / 'siena25/NOTES.md')],
        caveats=[
            "UNDATED: nothing fixes it to the 15th century (the fascicle runs 1421-1547); use as a period sample only "
            "with that caveat.",
            "Short (about 500 signs).",
            "Two words (18 signs) read but not understood: s'hadra, o chon grediamo."],
        _stats=st)


def siena_no04():
    f = T / 'borghesi1456/transcripts/no04_reading.txt'
    rows = read(f).splitlines()
    st = Stats()
    # gather R-lines with their continuation lines, up to the '->' reading line
    runs, cur = [], None
    for l in rows:
        m = re.match(r'^(R\d+)\s+(L\d+)\s+(.*)$', l)
        if m:
            cur = [m.group(1), m.group(3), None]
            runs.append(cur)
            continue
        if l.startswith('#'):
            cur = None
            continue
        s = l.strip()
        if cur is None or not s:
            continue
        if s.startswith('->'):
            cur[2] = s[2:]
        elif cur[2] is None:
            cur[1] += ' ' + s                     # continuation of the sign line (R10)
        # lines after the reading are comments on it: ignored
    CLEAR = {'che'}                                  # clear Italian word inside R10 (no04.txt has it as [che])
    lines, ids, plain = [], [], []
    for rid, sig, reading in runs:
        sig = re.sub(r'\{[^}]*\}', ' ', sig)                        # recipient's glosses
        sig = re.sub(r'\([^)]*\)', ' ', sig)                        # transcriber's comments
        sig = re.sub(r'\[[^\]]*\]', ' ; ', sig)                     # clear text -> run break
        sig = sig.replace('...', ' ; ')                             # omitted clear text (R11)
        sig = re.sub(r'<([^>/?]*)[^>]*>', lambda m: ' N:' + m.group(1).strip() + ' ', sig)  # Latin code words
        toks = []
        for t in sig.split():
            if t == ';' or t in CLEAR:
                toks.append(GAP)
            elif t in ('·', ':'):
                toks.append('|')
            elif t == '|':
                continue                                            # transcriber's grouping, not on the page
            elif t.startswith('N:'):
                toks.append(t)
            else:
                toks.append(strip_q(t, st))
        for sid, seg in segments(rid, toks):
            ids.append(sid)
            lines.append(seg)
        if reading:
            r = re.split(r'\s{2,}[(\']', reading)[0]
            r = re.sub(r'<[^>]*>', ' ', r)
            r = re.sub(r'\(\+[^)]*\)', ' ', r)
            rt = r.split()
            words = []
            for k, w in enumerate(rt):
                if w == '?' or w.endswith('?') or (w.startswith('(') and w.endswith('?)')):
                    continue                                        # unread sign, doubtful letter or guess
                w2 = re.sub(r'\[[^\]]*\]', '', w)
                w2 = w2.replace('(', '').replace(')', '').replace('?', '')
                if len(w2) == 1 and '?' in rt[max(0, k - 1):k] + rt[k + 1:k + 2]:
                    continue                                        # single letter between unread signs
                if w2 and w2.isupper() and w2.isalpha():
                    words.append(w2)
            plain.append(' '.join(words))
    return dict(
        target='siena1421', dataset='siena1421_no04',
        piece="Galgano Borghesi, orator at Naples, to Leonardo Benvoglienti, no. 4",
        date='12 May 1456', year=1456, date_basis='dated in the letter; Senatore 2009',
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", no. 4 (DECODE R4793)',
        system="Substitution of capitals, digits and drawn signs in 15 short runs inside a clear Italian letter, "
               "plus Latin code words (Calor = duca, storps = Lucca, cras = parte, vapor = cardinali ...); key "
               "rebuilt from an alphabet fragment below the text and the recipient's glosses.",
        language='Italian (one Latin phrase)', outcome='read in part (79% of sign tokens, 87% with doubtful)',
        sign_inventory_note=(
            "Sign names of transcripts/no04_reading.txt (agent G: digits and Latin letters as themselves, drawn "
            "signs as words with '_', e.g. q_foot, g_ring, L_slant, longs). '//' is a sign there (two slanting "
            "strokes). N:<word> = a Latin code word written in clear letters (one token each). '|' = a point the "
            "scribe wrote between groups ('·' and ':'); the transcriber's own '|' groupings are dropped. Clear "
            "text and the clear 'che' split runs into separate lines; glosses dropped."),
        lines=lines, line_ids=ids,
        plaintext=norm_plain(' '.join(plain)),
        plaintext_source="the '->' readings of each run in no04_reading.txt, upper-case (deciphered) words only",
        source_files=[rel(f), rel(T / 'borghesi1456/transcripts/no04.txt'), rel(T / 'borghesi1456/keys/no04_key.txt'),
                      rel(T / 'borghesi1456/NOTES.md')],
        caveats=[
            "Very short (about 140 signs in 15 runs): too short for character statistics on its own.",
            "19 signs unread and 11 doubtful; several sign shapes occur once.",
            "Code words are clear Latin words; they are single N: tokens, not spelled out."],
        _stats=st)


def siena_tok(dataset, parts, meta, folder, sub='transcripts'):
    """Siena pieces kept as the target's prepared .tok files (one manuscript line or run per line)."""
    st = Stats()
    lines, ids = [], []
    for label, fn in parts:
        for n, l in enumerate(read(T / folder / sub / fn).splitlines(), 1):
            if not l.strip():
                continue
            toks = []
            for t in l.split():
                if t.startswith('??') or t == '[x]':
                    toks.append(GAP)
                    st['illegible_signs'] += 1
                else:
                    toks.append(t)
            for sid, seg in segments(f'{label}.t{n:02d}', toks):
                ids.append(sid)
                lines.append(seg)
    d = dict(target=folder, dataset=dataset, lines=lines, line_ids=ids, plaintext=None,
             plaintext_source=None, _stats=st,
             source_files=[rel(T / folder / sub / fn) for _, fn in parts] +
                          [rel(T / folder / sub / x) for x in meta.pop('txt')] +
                          [rel(T / folder / 'NOTES.md'), rel(T / folder / 'profile.json')])
    d.update(meta)
    return d


def r1854_part(dataset, files, keyfile, codes, separators, gap_signs, meta, plaintext, psource):
    st = Stats()
    key = load_key(T / 'r1854' / keyfile) if keyfile else {}
    lines, ids = [], []
    for label, fn in files:
        for l in read(T / 'r1854' / fn).splitlines():
            m = re.match(r'^(L\d+):\s?(.*)$', l)
            if not m:
                continue
            lid, body = m.group(1), m.group(2)
            toks = []
            for t in re.findall(r'\{[^}]*\}|\S+', body):
                if t.startswith('{'):
                    if t == '{struck}':
                        st['struck_runs_dropped'] += 1
                    toks.append(GAP)
                    continue
                s = t.split('/')[0] if '/' in t and t not in ('//', '/') else t   # p3: sign/gloss
                if s in separators:
                    toks.append('|')
                elif s in gap_signs:
                    toks.append(GAP)
                    st['illegible_signs'] += 1
                elif s in codes:
                    toks.append('N:' + s)
                elif key.get(s) == '_':
                    toks.append('0:' + s)
                else:
                    toks.append(s)
            for sid, seg in segments(f'{label}.{lid}' if label else lid, toks):
                ids.append(sid)
                lines.append(seg)
    d = dict(target='r1854', dataset=dataset, lines=lines, line_ids=ids, plaintext=plaintext,
             plaintext_source=psource, _stats=st,
             source_files=[rel(T / 'r1854' / fn) for _, fn in files] +
                          ([rel(T / 'r1854' / keyfile)] if keyfile else []) +
                          [rel(T / 'r1854/NOTES.md'), rel(T / 'r1854/profile.json')])
    d.update(meta)
    return d


def r1854_all():
    rp2 = read(T / 'r1854/reading_p2.md')
    p2_plain = norm_plain(join_lines(rp2.split('## Latin')[1].split('## English')[0].splitlines()))
    rp3 = read(T / 'r1854/reading_p3.md').split('## Italian')[1].split('## Summary')[0]
    p3_plain = norm_plain(' '.join(re.findall(r'\*([^*]+)\*', rp3, flags=re.S)))
    rp4 = read(T / 'r1854/reading_p4.md')
    im4 = rp4.split('## Image 4')[1].split('## Image 5')[0]
    im5 = rp4.split('## Image 5')[1].split('## Measure')[0]
    num = lambda s: [re.sub(r'\s{2,}\(.*$', '', re.sub(r'^\d+\.\s*', '', l))     # drop "(revised ...)" notes
                     for l in s.splitlines() if re.match(r'^\d+\.\s', l)]
    p45_plain = norm_plain(join_lines(num(im4)) + ' ' + join_lines(num(im5)))
    out = []
    out.append(r1854_part(
        'r1854_p1', [('', 'p1v2.txt')], None, codes=set(), separators={'//', '/', '|', ':', '...', '.'},
        gap_signs={'&'}, plaintext=None, psource=None,
        meta=dict(piece="Pandolfo Malatesta, archbishop of Patras, to Gianfrancesco Gonzaga (R1854 image 1)",
                  date='22 Apr 1428', year=1428, date_basis="archivist's date on the letter; signed",
                  shelfmark='Archivio di Stato di Mantova (Archivio Gonzaga); DECODE R1854 image 1 (I8411)',
                  system="Unknown. Three cipher runs of letter-like invented signs inside clear Latin, with "
                         "separator marks (// : ... . |) between groups; none of the Gonzaga register's Malatesta "
                         "keys fits; not monoalphabetic or homophonic in Latin/Italian under every test run.",
                  language='Latin context (cipher language unknown)', outcome='not read',
                  sign_inventory_note=(
                      "Sign names of p1v2.txt (second pass): ss, n (eta), A, H, H#, I, cc, Z, Z3, bz, K, Xb, x, y, "
                      "9, q, oo, v, vb, 8, 4, +, t+, *, O, P, F, g. All separator marks (// / | : ... .) are '|'. "
                      "'&' (a grey blot, smudged or corrected sign) is treated as illegible."),
                  caveats=["Short (262 signs).", "The separators may themselves be cipher signs (tested in NOTES "
                           "without result); here they are all mapped to '|', which merges five mark types.",
                           "Scan resolution about 15 px per sign; fine marks at the limit of the image."])))
    out.append(r1854_part(
        'r1854_p2', [('', 'p2v3.txt')], 'key7.txt', codes={'ARW', 'ARO', 'S'}, separators={'_'},
        gap_signs={'?'}, plaintext=p2_plain, psource="reading_p2.md, '## Latin' (editorial brackets removed)",
        meta=dict(piece="Unnamed Gonzaga agent (lozenge mark) to Gianfrancesco Gonzaga (R1854 image 2)",
                  date='9 Aug 1428', year=1428, date_basis="dated in clear at the foot; archivist's note",
                  shelfmark='Archivio di Stato di Mantova (Archivio Gonzaga); DECODE R1854 image 2 (I8412)',
                  system="Latin; homophonic substitution of graphic signs and numerals, 13 null signs, "
                         "syllable signs (3 = con, 8t = rum), a word sign (S = et), two code signs (ARW = "
                         "cardinalis, ARO), occasional dot-group separators; whole letter in cipher; key "
                         "recovered ciphertext-only here.",
                  language='Latin', outcome='read (about 97% of signs)',
                  sign_inventory_note=(
                      "Sign names of p2v3.txt (o plain circle, q tailed circle, f = phi, F crossed phi, b, g, j, "
                      "numerals 1-20 as written ...). 0: = signs the key key7.txt sets to null (#, &q, 19, 20, D, "
                      "K, M, O, W, Y, wq, F, v); N: = ARW, ARO and the et-sign S. '|' = the dot-group separator "
                      "'_'. The syllable signs 3 (con) and 8t (rum) are left as letter signs."),
                  caveats=["About 45 signs sit in doubtful spans; code ARO unread.",
                           "Look-alike splits (bold vs dotted triangle, tailed vs plain circle) were made on the "
                           "image in a second pass."])))
    out.append(r1854_part(
        'r1854_p3', [('', 'p3_signs.txt')], 'key3_p3.txt', codes={'MALx', 'FIOL', 'PAPA'}, separators={'_'},
        gap_signs={'?'}, plaintext=p3_plain, psource="reading_p3.md, italic (deciphered) passages only",
        meta=dict(piece="Ricc(ardo?) de Mutiliana to Gianfrancesco Gonzaga (R1854 image 3)",
                  date='6 Nov 1428', year=1428, date_basis='dated in the clear subscription (Forlì)',
                  shelfmark='Archivio di Stato di Mantova (Archivio Gonzaga); DECODE R1854 image 3 (I8413)',
                  system="Italian; homophonic substitution of graphic signs with about ten null signs and three "
                         "name codes (MALx = signor Malatesta, FIOL = fioli del signor marchese, PAPA); runs "
                         "inside clear Italian; contemporary interlinear decipherment.",
                  language='Italian', outcome='read at the time (gloss); re-deciphered here, about 97%',
                  sign_inventory_note=(
                      "Sign names of p3_signs.txt (the '/x' gloss letters are dropped, only the sign kept). 0: = "
                      "signs key3_p3.txt sets to null (+, hk, st, T, Lh, tc, I, lc, Q4, Lp); N: = MALx, FIOL, PAPA. "
                      "'|' = separator points ('_') inside a run; points at the clear/cipher boundary fall at line "
                      "ends and are dropped. Clear words ({...}) and struck runs ({struck}) end lines."),
                  caveats=["Signs Z and fk unread; about 25 signs in doubtful spans.",
                           "Runs are short (often 10-40 signs) and interleaved with clear text."])))
    out.append(r1854_part(
        'r1854_p4p5', [('P4', 'p4v2.txt'), ('P5', 'p5v2.txt')], 'key4_v2.txt', codes={'E', 'C', 'J'},
        separators=set(), gap_signs={'?'}, plaintext=p45_plain,
        psource="reading_p4.md, numbered lines of images 4 and 5",
        meta=dict(piece="Francesco de' Cattanei to Gianfrancesco Gonzaga, two letters (R1854 images 4-5)",
                  date='13 and 21 Feb 1430', year=1430, date_basis='dated in clear (Rome); signed on the verso',
                  shelfmark='Archivio di Stato di Mantova (Archivio Gonzaga); DECODE R1854 images 4-5 (I8414, I8415)',
                  system="Latin; homophonic substitution of graphic signs (up to four signs per letter), three "
                         "signs for the word et (E, C, J), syllable signs m = rum and 3c = com; no word division, "
                         "no nulls found; key recovered ciphertext-only here.",
                  language='Latin', outcome='read (96.7% of signs on image 4; image 5 in full)',
                  sign_inventory_note=(
                      "Sign names of p4v2.txt / p5v2.txt (second pass: OTO, OO, O, OXO, I, bo, Dv, q, R, # ...). "
                      "'=' is a cipher sign (t), not a separator. N: = the et-signs E, C, J. No separators or "
                      "nulls are marked. '?' (one unresolved composite sign) ends a line."),
                  caveats=["About 32 signs in illegible spots (786-px scan), sign 'd' without value.",
                           "Image 5 is only three lines (about 200 signs) of the second letter."])))
    return out


def florence1429():
    f = T / 'florence1429/cipher171.tsv'
    st = Stats()
    runs = collections.OrderedDict()
    for r in csv.reader(read(f).splitlines(), delimiter='\t'):
        if not r or r[0].startswith('#') or r[0] == 'run':
            continue
        runs.setdefault(r[0], []).append(r)
    lines, ids, plain = [], [], []
    for run, rows in runs.items():
        toks, words, cur = [], [], ''
        for r in rows:
            sign, value = r[1], r[2]
            if value == 'null':
                toks.append('0:' + sign)
            elif value != '?' and len(value) > 1:
                toks.append('N:' + sign)
                if cur:
                    words.append(cur)
                    cur = ''
                words.append(value)
            else:
                toks.append(sign)
                if value != '?':
                    cur += value
                else:
                    st['unvalued_signs'] += 1
        if cur:
            words.append(cur)
        ids.append(run)
        lines.append(toks)
        plain.append(' '.join(words))
    return dict(
        target='florence1429', dataset='florence1429',
        piece="Galeotto Fibindacci da Ricasoli to the Signoria of Florence, Urbino, no. 171",
        date='early 1425 (1424 Florentine style)', year=1425, date_basis='content and sibling letters (NOTES)',
        shelfmark='ASF, Dieci di Balìa, Responsive 2 no. 171 (old 168) (DECODE R3754)',
        system="Homophonic substitution of graphic signs (two or three per letter) with about 17 nulls and a "
               "nomenclator of about 30 signs (persons, places, 'che', 'per', 'con'); about twenty short runs "
               "inside clear Italian. Key: Gabbrielli 1863 (Meister 1902) extended here from sibling glosses.",
        language='Italian', outcome='read (98.0% of cipher tokens given a value)',
        sign_inventory_note=(
            "Sign names of cipher171.tsv (as in key_extended.md: Unicode look-alikes such as ∵, ᴗ, ⊐, ∂, ℘, +o). "
            "0: = value 'null' in the TSV; N: = a sign whose value is a word or name (il Conte, Dieci, fanti, il "
            "Papa, ella ...). Each TSV run (L2a, L3b ...) is one line. The cipher writes no word separators."),
        lines=lines, line_ids=ids,
        plaintext=norm_plain(' '.join(plain)),
        plaintext_source="value column of cipher171.tsv (letters joined per run; word/name values as words)",
        source_files=[rel(f), rel(T / 'florence1429/READING.md'), rel(T / 'florence1429/key_extended.md'),
                      rel(T / 'florence1429/NOTES.md')],
        caveats=["Very short (99 cipher tokens in 20 runs): too short for statistics on its own.",
                 "About 270 more signs of the same cipher (sibling letters R3755-R3757, glossed runs) are in "
                 "TRANSCRIPTION.md as a markdown table; not included here."],
        _stats=st)


def maria1435():
    f = T / 'maria1435/cipher.txt'
    lines, ids = [], []
    for l in read(f).splitlines():
        if l.strip() and not l.startswith('#'):
            ids.append(f'run{len(ids) + 1}')
            lines.append(l.split())
    return dict(
        target='maria1435', dataset='maria1435',
        piece="Queen María of Castile to Alfonso V, register copy",
        date='5 Aug 1435', year=1435, date_basis='dated in the register',
        shelfmark='ACA, Cancillería, reg. 3225 f. 59r (DECODE R10171)',
        system="Unknown. Three short cipher runs of digit-like, letter-like and figure signs inside a Catalan "
               "letter; dotted figures (sq, bp, O) may be nomenclator signs (hypothesis from the 1429 key).",
        language='Catalan context (cipher unread)', outcome='not read',
        sign_inventory_note=(
            "Sign names of cipher.txt: ff, 6, 8 (plain), 8R (8 with top-right stroke), 8L (8 with left tail, only "
            "after 6), tri, sq (square hook, dotted), bp (b with bracket, dotted), O (circle with dot, dotted), t, "
            "z, a d n v M, 2 3 9, E, E2. No sign is marked N: or 0: because no key exists; the dots flanking sq, "
            "bp and O are not tokens."),
        lines=lines, line_ids=ids, plaintext=None, plaintext_source=None,
        source_files=[rel(f), rel(T / 'maria1435/NOTES.md')],
        caveats=["About 40 signs in all: far too short for statistics."],
        _stats=Stats())


def it1583(which):
    if which == 'f68':
        f = T / 'it1583/transcription.txt'
    else:
        f = T / 'it1583/transcription_f70.txt'
    st = Stats()
    lines, ids = [], []
    n = 0
    for l in read(f).splitlines():
        if not l.strip() or l.startswith('#'):
            continue
        n += 1
        toks = []
        for t in re.findall(r'\{[^}]*\}|\S+', l):
            if t.startswith('{'):
                toks.append(GAP)
            elif t == '|':
                continue                                   # paragraph-start marker of the transcription
            elif t == '.':
                toks.append('|')
            elif t == '?':
                toks.append(GAP)
                st['illegible_signs'] += 1
            else:
                toks.append(strip_q(t, st))
        for sid, seg in segments(f'{which}.p{n}', toks):
            ids.append(sid)
            lines.append(seg)
    common = dict(
        target='it1583', language='Italian (Lombard) context; cipher unread', outcome='not read',
        lines=lines, line_ids=ids, plaintext=None, plaintext_source=None, _stats=st,
        source_files=[rel(f), rel(T / 'it1583/NOTES.md'), rel(T / 'it1583/profile.json')])
    if which == 'f68':
        common.update(
            dataset='it1583_f68',
            piece="Sforza side to Giorgio (Zorzo) del Maino, reply, f. 68",
            date='4 May 1446', year=1446, date_basis='dated at the head in clear; Mazzatinti 1883',
            shelfmark='BnF italien 1583 f. 68 (DECODE R7898)',
            system="Graphic-sign cipher of the Sforza family (homophonic letters with syllable and word signs, "
                   "cf. ASMi Sforzesco cart. 1597 no. 14), dot separators, stretches inside clear Lombard Italian.",
            sign_inventory_note=(
                "Sign codes of transcription.txt (draft 1): 8 p c k n r z x > as written; B barred b, H looped h, "
                "E barred epsilon, F double-barred stroke, + cross/stroke, D divide sign, S long s, J barred yogh, g "
                "barred g, Q phi, d d with apostrophe, 7 hooked 7, V cross-circle, M barred m-like sign, - dash-hook. "
                "'|' = the written dot separators ('.', for :: or .:.). Rows are the transcription's paragraphs, "
                "split at clear text."),
            caveats=["Short (about 400 signs).", "Draft transcription from a binarized scan: diacritics that may "
                     "separate signs are unreliable.", "Probably syllabic/word signs over homophonic letters."])
    else:
        common.update(
            dataset='it1583_f70',
            piece="Vincenzo Amidani (Milan) to Francesco Sforza, f. 70",
            date='4 May 1446', year=1446, date_basis="pencil '1446 4 Mai' on the slip; Mazzatinti 1883",
            shelfmark='BnF italien 1583 f. 70 (seen on DECODE R7899 image 1)',
            system="Same sign family as f. 68, a different hand; almost all cipher.",
            sign_inventory_note=(
                "Sign codes of transcription_f70.txt: as f. 68 EXCEPT that E here is a b with double bar (not the "
                "barred epsilon of f. 68); W ab-ligature, K hatched sign, Y slashed v, O reversed c, e plain "
                "epsilon, P barred p, 3 4 6 s b. Sign ids are therefore not comparable with it1583_f68. '|' = "
                "written dot separators."),
            caveats=["Short (about 390 signs).", "Draft transcription from a binarized scan.",
                     "Kept separate from f. 68: different hand and a partly different sign set."])
    return common


def buda1489():
    key = json.loads(read(T / 'buda1489/key.json'))
    st = Stats()

    def tag(t):
        v = key.get(t)
        if t == '.' or v == '{null}':
            return '0:' + t
        if isinstance(v, str) and v.startswith('['):
            return 'N:' + t
        return t

    lines, ids = [], []
    # R1098 line 10, boxes 44-61: "faded tail, boxes 44-61 illegible" (trans/r1098p1_v.txt)
    r1098_tail = lambda r: r['line'] == '10' and int(re.match(r'\d+', r['idx']).group()) >= 44
    for label, fn, illegible in (('R1098', 'r1098p1.csv', r1098_tail),
                                 ('V267', 'v267.csv', lambda r: False)):
        bylines = collections.OrderedDict()
        for r in csv.DictReader(read(T / 'buda1489/trans' / fn).splitlines()):
            bylines.setdefault(r['line'], []).append(r)
        for ln, rows in bylines.items():
            toks = []
            for r in rows:
                t = r['token'].strip()
                if t.startswith('[clear'):
                    toks.append(GAP)
                elif illegible(r):
                    st['illegible_signs'] += 1
                    toks.append(GAP)
                else:
                    toks.append(tag(strip_q(t, st)))
            for sid, seg in segments(f'{label}.L{int(ln):02d}', toks):
                ids.append(sid)
                lines.append(seg)
    rr = read(T / 'buda1489/r1098_reading.md').split('**Cipher, page 1')[1].split('**English')[0]
    r1098 = [re.sub(r'^\d+\.\s*', '', l) for l in rr.splitlines() if re.match(r'^\d+\.\s', l)]
    r1098 = [l.replace('Ser.mo Re', ' ') for l in r1098]          # nomenclator sign M., left out like other codes
    plain = norm_plain(join_lines(r1098).replace('…', ' ')) + ' ' + norm_plain(read(T / 'buda1489/plain267.txt'))
    return dict(
        target='buda1489', dataset='buda1489',
        piece="Maffeo da Treviglio to Ludovico Sforza: Buda 12 Jan 1490 (DECODE R1098, p. 1) and Vienna 2 Apr 1490 "
              "(Vestigia 267)",
        date='12 Jan 1490 and 2 Apr 1490', year=1490, date_basis='dated in clear in both letters',
        shelfmark='ASMi, Sforzesco, Potenze estere, Ungheria cart. 642 (DECODE R1098; Vestigia 267, clear extract 268)',
        system="Italian; homophonic substitution of cursive letters, numerals and marks with syllable signs "
               "(letter + superscript: q^e = re, b^o = no, m^o = si ...), nulls (w, ÷, -, lone dots) and a small "
               "nomenclator (M. = Ser.mo Re, S. = S.V.); no word division (Somogyi 2016 key, extended here).",
        language='Italian', outcome='V267 read at the time (clear extract 268); R1098 read in gist here',
        sign_inventory_note=(
            "Token alphabet of AGENT_BRIEF.md (trans/*.csv): base letters, capitals, numerals and marks (// two "
            "slashes, ) crescent, ÷ ...) with modifiers appended (^a/^e/^o superscript, ~ macron, | stroke, . dot, "
            "- attached bar). 0: = nulls by key.json (w, ÷, -, and lone dots '.'); N: = nomenclator signs by "
            "key.json (M., M:, S.). Lines R1098.Lnn and V267.Lnn are manuscript lines; clear words split them."),
        lines=lines, line_ids=ids,
        plaintext=plain,
        plaintext_source="R1098: r1098_reading.md lines 1-10 (bracketed and unread parts left out); V267: "
                         "plain267.txt (the contemporary clear extract, Vestigia 268)",
        source_files=[rel(T / 'buda1489/trans/r1098p1.csv'), rel(T / 'buda1489/trans/v267.csv'),
                      rel(T / 'buda1489/trans/r1098p1_v.txt'), rel(T / 'buda1489/key.json'),
                      rel(T / 'buda1489/AGENT_BRIEF.md'), rel(T / 'buda1489/r1098_reading.md'),
                      rel(T / 'buda1489/plain267.txt'), rel(T / 'buda1489/NOTES.md')],
        caveats=[
            "R1098's token file is a first agent pass that NOTES says conflates z/3, d/ð, s/ſ and u/v, with many "
            "doubtful signs; the faded tail of its line 10 (boxes 44-61, illegible per r1098p1_v.txt) is left out.",
            "Short (about 650 signs in the two letters).",
            "The 22 Nov 1489 letter (Vestigia 2831, about 2,000 signs, the oldest of the set) has sign-by-sign notes "
            "only in prose reading files (trans/v2831*_read*.md), not a token file; not included."],
        _stats=st)


def main():
    data = [benedict1399(), siena_no14(), florence1429()]
    data += r1854_all()
    data += [maria1435(), it1583('f68'), it1583('f70'), siena_no04()]
    data.append(siena_tok('siena1421_no07', [('no07', 'no07.tok')], dict(
        txt=['no07.txt', 'no07_reading.txt'],
        piece="Sienese orator at Milan to the Officiales Balie (Lionardo Benvoglienti named), no. 7",
        date='c. 1454 (undated)', year=1454, date_basis='context: the 1454 Milan embassy (NOTES); not in the letter',
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", no. 7 (DECODE R4796)',
        system="Mixed digits, letters and drawn signs, homophonic-looking (faint glosses give o for several signs), "
               "runs inside a clear Italian despatch; key R4750 (Milan 1454) does not fit.",
        language='Italian context; cipher unread', outcome='not read',
        sign_inventory_note=("Tokens of transcripts/no07.tok (one cipher run per line, as the target prepared it "
                             "from no07.txt; the scribe's sporadic points are not kept)."),
        caveats=["Short (363 signs).", "Some short cursive items inside runs may be clear words (no07.txt notes).",
                 "Date from context, not from the letter."]), folder='siena7'))
    data.append(siena_tok('siena1421_no11', [('no11', 'no11.tok')], dict(
        txt=['no11.txt'],
        piece="Donato Acciaiuoli to Lorenzo de' Medici, intercepted Florentine letter held in Siena, no. 11",
        date='13 June 1478', year=1478, date_basis="dated 'ex Urbe die 13 junii 1478'",
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", no. 11 (DECODE R4800)',
        system="Florentine cipher of graphic signs (44 types), no word division, two cipher blocks inside a clear "
               "letter; homophonic anneal fails; no key known.",
        language='Italian context; cipher unread', outcome='not read',
        sign_inventory_note="Tokens of transcripts/no11.tok (sign names of no11.txt; 'PLUS O' merged as one sign).",
        caveats=["Short (409 signs)."]), folder='siena11'))
    data.append(siena_tok('siena1421_no06_24', [('no06', 'no06.tok'), ('no24', 'no24p2.tok')], dict(
        txt=['no06.txt', 'no24.txt', 'no24_p2a.txt', 'no24_p2b.txt'],
        piece="Two letters to the Signori of Siena in one system: no. 6 (sender unknown, 'di Firenze'?) and no. 24 "
              "(text side)",
        date='undated; 15th-century hand (no. 6)', year=None,
        date_basis="hand only ('15th-century mercantesca-like hand', no06.txt); the profile's 1450 is a placeholder",
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", nos. 6 and 24 (DECODE R4795, R4812 P2)',
        system="About 65 sign types (letters, digits, drawn signs, signs with a cross above), no word division, "
               "frequent 'p p' pairs and point-framed single signs; not plain homophonic substitution "
               "(validated solvers fail): probably syllabic or nomenclator elements. No key.",
        language='Italian context; cipher unread', outcome='not read',
        sign_inventory_note=("Tokens of transcripts/no06.tok and no24p2.tok, one manuscript line per line, sign "
                             "names of the no. 6 legend (a, b, B, c, c^, d, d+, m+, W, A, BOX, THETA, SS ...; X+ = "
                             "sign with a cross above). No. 24's dorse run-over (P1, about 640 signs) is not "
                             "included."),
        caveats=["Date only from the hand of no. 6.",
                 "Two transcribers (agent A for no. 6, agents H and I for no. 24) with one legend; look-alike "
                 "signs may be merged or split differently.",
                 "System unidentified: tokens may be syllables or code signs, not letters."]), folder='siena1431', sub='project_attempt'))
    data.append(siena_tok('siena1421_no20_23', [('no20', 'no20.tok'), ('no23', 'no23.tok')], dict(
        txt=['no20.txt', 'no23a.txt', 'no23b.txt'],
        piece="Two letters in one system: no. 20 to a king ('Sacra Regia Maiestas'), [Perugia?], penultimate day "
              "of March; no. 23 unsigned",
        date='undated', year=None,
        date_basis="none: no year in either letter; the profile's 1455 is a placeholder; the fascicle runs 1421-1547",
        shelfmark='ASSi, Concistoro 2308, fasc. 2 "Lettere in cifra", nos. 20 and 23 (DECODE R4808, R4811)',
        system="About 50-67 sign types, mostly letter-shaped, with superscripts (o^n, q^o ...); no word division; "
               "'f' + o^n / a / o groups behave as units (syllabic or nomenclator element); not plain homophonic "
               "substitution. No key.",
        language='Italian context; cipher unread', outcome='not read',
        sign_inventory_note=("Tokens of transcripts/no20.tok and no23.tok, one manuscript line per line; a sign "
                             "with a superscript (q^o, f o^n's o^n) is one token, as transcribed."),
        caveats=["UNDATED: may be 16th century; do not use as a dated 15th-century sample.",
                 "Two transcribers (agents C and D); one illegible sign ('??^o') ends a line.",
                 "System unidentified."]), folder='siena2023', sub='project_attempt'))
    data.append(siena_no25())
    data.append(buda1489())

    written = []
    for d in data:
        st = d.pop('_stats')
        d['counts'] = counts(d['lines'])
        d['counts']['plaintext_letters'] = len((d['plaintext'] or '').replace(' ', ''))
        d['counts'].update({k: v for k, v in sorted(st.items())})
        order = ['dataset', 'target', 'piece', 'date', 'year', 'date_basis', 'shelfmark', 'system', 'language',
                 'outcome', 'sign_inventory_note', 'counts', 'plaintext', 'plaintext_source', 'source_files',
                 'caveats', 'line_ids', 'lines']
        d = {k: d[k] for k in order}
        head = json.dumps({k: v for k, v in d.items() if k not in ('line_ids', 'lines')}, ensure_ascii=False,
                          indent=1)
        body = (',\n "line_ids": ' + json.dumps(d['line_ids'], ensure_ascii=False) + ',\n "lines": [\n  ' +
                ',\n  '.join(json.dumps(l, ensure_ascii=False) for l in d['lines']) + '\n ]\n}\n')
        text = head[:-2] + body                     # head ends with '\n}'
        assert json.loads(text) == d
        (HERE / f"{d['dataset']}.json").write_text(text, encoding='utf-8')
        written.append(d)
        c = d['counts']
        print(f"{d['dataset']:20s} {str(d['year']):5s} tokens {c['sign_tokens']:5d} distinct {c['distinct_signs']:3d}"
              f" letters {c['distinct_letter_signs']:3d} codes {c['code_sign_tokens']:3d} nulls {c['null_tokens']:4d}"
              f" div {c['dividers']:4d} lines {c['lines']:3d} plain {c['plaintext_letters']}")
    write_readme(written)


# ----------------------------------------------------------------------------------------------- README
SHORT = {   # dataset: (system in a few words, main caveat)
    'benedict1399': ("simple substitution, one sign per letter (c=i, u=v); name sign; null separator groups; Latin",
                     "RECONSTRUCTED from Puig's text + rebuilt key (only image is a 1920 halftone), not transcribed"),
    'siena1421_no14': ("substitution with a few homophones; word points; person codes; Italian",
                       "date c. 1409-29 from content only; 59% of tokens read as sense"),
    'florence1429': ("homophonic + 17 nulls + nomenclator; short runs in clear Italian",
                     "99 signs: too short alone"),
    'r1854_p1': ("unknown; letter-like signs in 3 runs with separator marks; in clear Latin",
                 "262 signs; unread"),
    'r1854_p2': ("homophonic + 13 null signs + syllable signs (con, rum) + et-sign + 2 codes; Latin", "-"),
    'r1854_p3': ("homophonic + 10 null signs + 3 name codes; runs in clear Italian", "runs short, glossed at the time"),
    'r1854_p4p5': ("homophonic (up to 4 signs per letter) + 3 et-signs + syllable signs; Latin", "-"),
    'maria1435': ("unknown; 3 short runs in a Catalan register copy", "42 signs: far too short"),
    'it1583_f68': ("Sforza family: homophonic with syllable/word signs (probable); dot separators",
                   "unread; draft from a binarized scan"),
    'it1583_f70': ("same family as f. 68, other hand", "unread; sign ids not comparable with f. 68"),
    'siena1421_no04': ("letter substitution in 15 runs + Latin code words", "153 signs: too short"),
    'siena1421_no07': ("mixed digits/letters/signs, homophonic-looking; runs in clear", "unread; date from context"),
    'siena1421_no11': ("Florentine cipher, 44 sign types, no word division", "unread"),
    'siena1421_no06_24': ("unidentified, ~70 types incl. crossed variants; not plain homophonic",
                          "date from hand only; unread; two transcribers"),
    'siena1421_no20_23': ("unidentified, superscripted signs, 'f o^n' units; not plain homophonic",
                          "UNDATED (fascicle 1421-1547); unread"),
    'siena1421_no25': ("simple substitution, one sign per letter; word points; Italian",
                       "UNDATED (fascicle 1421-1547)"),
    'buda1489': ("homophonic + syllable signs (letter+superscript) + nulls + nomenclator; Italian",
                 "R1098 is a noisy first-pass transcription"),
}

SKIPPED = [
    ("florence1414", "1414", "No ciphertext reachable: the letters are not online (ASF Signori, Responsive); only "
     "Gabbrielli's partial key (KEY.md)."),
    ("medici1425", "1425", "Ciphertext not online (ASF Dieci di Balìa, Responsive, Oct 1425); nothing transcribed."),
    ("heidelberg597", "1426", "Read by Wattenbach 1869; only the alphabets were recovered here, the running cipher of "
     "the recipes has never been transcribed."),
    ("matthias1482", "1482", "About 330 signs of homophonic cipher, read against Fraknói's print, but no "
     "sign-by-sign transcription is kept (only the reading and a key table); homophones rule out rebuilding the "
     "signs from the text."),
    ("sadoleto1482", "1482", "Readings, alignments and a working key only; no sign-level token file (seg/ holds "
     "unlabelled glyph boxes); homophonic, so not rebuildable from the text."),
    ("beatrice1482", "1482-86", "Deciphered in print 1877-78 (MDE III-IV); no transcription in the folder."),
    ("esp318", "1497-1504", "No. 5 (1497) was printed by Parisi 2020 but not transcribed here; no. 95 (1497) exists "
     "only as machine-clustered letter decodes without sign ids; no. 92 (Aug 1500) and nos. 93-94 (1503-04) are the "
     "Catholic Monarchs' CVC-code family of 1500 and later."),
    ("research/oldest (ACA Reserva 12)", "1413-16", "A columnar transposition of clear Catalan (Salas 1931), not a "
     "sign cipher; no transcription under targets/."),
    ("siena1421, other pieces", "1421-1547", "No. 1 (1421) and nos. 2, 26-28 not photographed; nos. 9, 19, 21 and "
     "R4794 too short (46-170 signs) and undated; nos. 8, 10, 12 read at the time or marked decrypted on DECODE, no "
     "transcription here; nos. 13/16, 15, 17, 18 are 16th century; no. 22 clear drafts with number codes; no. 29 a "
     "scrap; the no. 24 dorse run-over (about 640 signs) is not in a token file."),
    ("buda1489, other pieces", "1489-92", "Vestigia 2831 (22 Nov 1489, about 2,000 signs) has sign notes only in prose "
     "reading files, no token file; R1146, R1147, R1158 (1491-92) are other systems and not transcribed."),
    ("florence1429 siblings", "1424-25", "R3755-R3757: about 270 signs of glossed runs, only as a markdown table "
     "(TRANSCRIPTION.md); left out."),
]


def write_readme(data):
    rows = sorted(data, key=lambda d: (d['year'] is None, d['year'] or 0, d['dataset']))
    out = []
    w = out.append
    w('# Period ciphers, 14th-15th century: a control set for the Voynich statistics\n')
    w('Genuine ciphertexts of c. 1400-1490 taken from this repository\'s own targets, to test whether any real '
      'cipher system of the period gives Voynich-like character statistics (in particular a very low conditional '
      'entropy h2). One JSON per cipher system. Built by `_extract.py` (deterministic; reads only the target '
      'folders; rerun with `PYTHONUTF8=1 python targets/voynich/data/period/_extract.py`, which also rewrites this '
      'file).\n')
    w('## Format\n')
    w('Each JSON has `dataset`, `target`, `piece`, `date`, `year` (null if undated), `date_basis`, `shelfmark`, '
      '`system`, `language`, `outcome`, `sign_inventory_note`, `counts`, `plaintext`, `plaintext_source`, '
      '`source_files`, `caveats`, `line_ids` and `lines`.\n')
    w('- `lines`: list of lines, each a list of sign tokens in reading order, in the target\'s own sign ids.')
    w('- `|` = a separator the scribe wrote (word points, dot groups, //); `N:x` = nomenclator/code sign (a name or '
      'a whole word, including et-signs); `0:x` = null by the key. Strip the prefixes to get the raw sign stream.')
    w('- Clear text is left out; a cipher run between clear words is its own line. An illegible, lost or struck '
      'sign ends the line (the rest is a new line with a suffixed id), so no false sign pair crosses a gap. A sign '
      'the transcriber marked doubtful is kept.')
    w('- `plaintext`: the reading of those passages, lowercase a-z and spaces; unread signs, editorial insertions, '
      'code expansions and clear words left out; null if there is no reading.')
    w('- `counts`: computed by the script: `sign_tokens` (all tokens except `|`), `distinct_signs` (prefixes '
      'stripped), letter/code/null tokens and distinct types, `dividers`, `lines`, `plaintext_letters`, and the '
      'number of doubtful signs kept and illegible signs dropped.\n')
    w('## Extracted\n')
    w('| dataset | date | system | sign tokens | distinct signs (letter / code / null) | dividers | plaintext | '
      'main caveat |')
    w('|---|---|---|---:|---|---:|---|---|')
    for d in rows:
        c = d['counts']
        sysd, cav = SHORT[d['dataset']]
        pt = 'yes' if d['plaintext'] else 'no'
        if d['plaintext'] and d['outcome'].startswith('read in part'):
            pt = 'partial'
        w(f"| {d['dataset']} | {d['date']} | {sysd} | {c['sign_tokens']} | {c['distinct_signs']} "
          f"({c['distinct_letter_signs']} / {c['distinct_code_signs']} / {c['distinct_nulls']}) | {c['dividers']} | "
          f"{pt} | {cav} |")
    total = sum(d['counts']['sign_tokens'] for d in rows)
    w(f'\nTotal: {len(rows)} datasets, {total} sign tokens.\n')
    big = [d for d in rows if d['counts']['sign_tokens'] >= 700]
    w('## Which to use\n')
    w('- Long enough for h2 on their own (700+ signs): ' + ', '.join(
        f"{d['dataset']} ({d['counts']['sign_tokens']})" for d in big) + '.')
    w('- Securely dated 1400-1490 among those: r1854_p2 (1428), r1854_p4p5 (1430), r1854_p3 (1428), '
      'siena1421_no14 (c. 1409-29, by content), benedict1399 (1400, reconstructed, so its h2 is that of Latin with '
      'c=i and u=v merged).')
    w('- The two largest, siena1421_no06_24 (15th-century hand) and siena1421_no20_23 (undated), are unread systems '
      'that are not plain homophonic substitution; they are the most interesting controls and the least certain in '
      'date and sign inventory.')
    w('- Everything under 500 signs (florence1429, maria1435, siena1421_no04, r1854_p1, siena1421_no07, '
      'siena1421_no11, it1583_f68, it1583_f70, siena1421_no25) is too short for a stable h2 on its own; use it '
      'pooled or as a sanity check only.\n')
    w('## Looked at and skipped\n')
    w('| target | date | reason |')
    w('|---|---|---|')
    for t, dt, why in SKIPPED:
        w(f'| {t} | {dt} | {why} |')
    w('')
    (HERE / 'README.md').write_text('\n'.join(out) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
