# Bischoff 1954's unread 15th-century book ciphers: attempts, 27-28 Oct 2026

Items Bischoff (MIÖG 62, 1954) prints and marks "ungelesen" / "ungedeutet", attacked from his printed text with the
key families of his own sections 11-19 and lang/ character models (Latin `la`, English `en-modern`, German
`de-1500s`). `solve_sub.py` = key families + one-to-one substitution hill-climb.

| Item | Status | File |
|---|---|---|
| **Karlsruhe 399 f. 229r** (no. 16c) | **read**: *Miserere mei deus secundum magnam misericordiam tuam* (Ps. 50:3), reciprocal letter pairs a-h c-q d-t e-i f-s g-r m-n o-u; 39 of 46 letters agree, misses systematic | `karlsruhe399.md`, `karlsruhe399_check.py` |
| **CCCC 96 f. 240** (no. 137; Jervaulx, c. 1425) | not read. Bischoff's and James's transcriptions differ (*p³p³lap³edff.p⁴.g.gggharazy p³ar* / *ipolapedff. o.g.gg gharazy p ar*). Tried: all 120 assignments of the vowels to p1-p5 x identity, alphabet and consonant shifts +-1..3, Atbash, reciprocal swaps, both models: best scores about -4.9 per character (real text -1.2 to -1.8), i.e. nothing. The pastedown is not among the Parker on the Web images (the viewer ends at 239v). Needs the leaf | `ccc96_search.py`, `../ccc96_bruteforce.py` |
| **Lambeth Palace 477 ff. 120v, 142v** (no. 19b) | blocked: Bischoff prints fragments only (*Cmapmabmd mafmb madmafx ⊛⊛⊛ mafx ... ymbns farte xmbfmd* "usw."); the fuller text is in James & Jenkins's Lambeth catalogue (1930-32) p. 659, not online. The host MS is a 14th-c. biblical concordance with sermons and Remigius's *Interpretationes* (Todd 1812). Bischoff files it with the Sloane 351 system (consonant replaced, "ex" inserted at double consonants, dummy letters); the frequent *m* looks like such fillers | none |

Not attempted: Göttingen Morbio 15 (1484 note; Bischoff gives only "(1484 .... i(n) ..... / barbare (?) eid (= die ?)
/ 22 (?)"), Vatican Borghese 239 f. 16r (an alphabet, no text), the early-medieval unread items (nos. 57-59).
