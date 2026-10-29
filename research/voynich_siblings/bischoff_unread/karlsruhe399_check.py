"""Karlsruhe 399 f. 229r (Bischoff 1954 no. 16c, 'ungelesen'): check the reading
'miserere mei deus secundum magnam misericordiam tuam' (Ps. 50:3 Vulgate) letter by letter against the reciprocal
pair key a-h, c-q, d-t, e-i, f-s, g-r, m-n, o-u. Ciphertext as printed by Bischoff ('nach der Hs. berichtigt')."""
pairs = ['ah', 'cq', 'dt', 'ei', 'fs', 'gr', 'mn', 'ou']
key = {}
for a, b in pairs:
    key[a], key[b] = b, a
ct = 'nefiggii nie tiof fiqomthm nhrmhn nifigiqugtehm dohn'.split()
pt = 'miserere mei deus secundum magnam misericordiam tuam'.split()
ok = bad = 0
for c, p in zip(ct, pt):
    expect = ''.join(key.get(x, x) for x in p)
    marks = ''.join('.' if a == b else '^' for a, b in zip(c, expect))
    ok += marks.count('.'); bad += marks.count('^')
    print(f'{p:14s} key gives {expect:14s} MS {c:14s} {marks}')
print(f'{ok} of {ok + bad} letters agree with the key')
