# Karlsruhe 399, f. 229r (Bischoff 1954 no. 16c, "ungelesen"): read

Night of 27-28 Oct 2026, from Bischoff's printed ciphertext only; no image seen.

## Source

Bischoff 1954 (MIÖG 62) p. 6, under 16 (substitution by other keys), after the Sloane 1754 key "statt abcde usw.
zadec usw.": "c Ein solches System scheint in dem Eintrag saec. XV in Karlsruhe, Karlsr. 399, fol. 229r vorzuliegen:
'Ne(?)figgii nie tiof fiqomthm nhrmhn nifigiqugtehm dohn' (so nach der Hs. berichtigt); ungelesen."

## Reading

**Miserere mei deus secundum magnam misericordiam tuam** (Psalm 50:3 Vulgate, the opening of the Miserere).

Key: reciprocal letter pairs (Bischoff's section 12 family, *pro a b, pro b a*):

| a-h | c-q | d-t | e-i | f-s | g-r | m-n | o-u |
|---|---|---|---|---|---|---|---|

Several pairs join letters of like sound or shape (d/t, m/n, o/u, e/i, long s/f).

## Check (`karlsruhe399_check.py`)

| Plaintext | Key gives | MS (Bischoff) | |
|---|---|---|---|
| miserere | nefigigi | nefiggii | ..... ^^ . (the 6th and 7th letters transposed; Bischoff marks the opening as uncertain) |
| mei | nie | nie | all agree |
| deus | tiof | tiof | all agree |
| secundum | fiqomton | fiqomthm | the last two letters differ (h = a, final m kept) |
| magnam | nhrmhn | nhrmhn | all agree |
| misericordiam | nefigequgtehn | nifigiqugtehm | two i's left as i, final m kept |
| tuam | dohn | dohn | all agree |

39 of 46 letters agree. The misses are of three kinds: a transposition at the start, plaintext *i* not swapped in
*misericordiam* (but swapped in *mei*), and a word-final *m* sometimes kept. Four of seven words agree exactly, and
the rest fit only this verse. The letter-pair key is fixed from those four words alone (*mei, deus, magnam, tuam*
give a-h, d-t, e-i, f-s, g-r, m-n, o-u), and it then produces *miser-re*, *secund--* and *m-sericordia-* unprompted:
a fixed key reproducing a known verse is not a fit by chance.*

## Status and caveats

- A reading is not found in print or online (searches 28 Oct 2026 for the shelfmark with "Geheimschrift" and for the
  cipher strings). Not checked: Bischoff's revised reprint (*Mittelalterliche Studien* III, 1981, pp. 120-148),
  which may carry addenda; the BLB catalogue entry for Karlsruhe 399 (Holder / the "Karlsruher Handschriften"
  volume); the manuscript image, which would settle the transposition and the final *m*.
- What Karlsruhe 399 contains, and its date beyond Bischoff's "saec. XV" entry, not checked.
- For the Voynich question: none. It is a pen-trial-sized pious line in a letter-swap cipher, a typical member of
  the genre table (`../physicians_ciphers.md`), and a reminder that Bischoff's "ungelesen" items are often easy.
