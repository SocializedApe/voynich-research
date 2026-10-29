# Taxonomic-language test on Voynich labels: results, 27 Oct 2026

Script: `label_prefix_test.py` (seed 1, 2,000 permutations). Data: `targets/voynich/data/ZL3b-n.words.tsv`
(ZL 3b; locus type L = labels, P = paragraph text). Labels kept: 642 words of 3+ letters without unread glyphs or
extended codes.

## Question

If Voynichese were an a priori "philosophical" language (Wilkins/Dalgarno type, Friedman's hypothesis), names of
similar things would share their opening parts. Labels in the same section, or on the same page, should then share
prefixes more than labels from other sections written by the same scribe. Hand is held fixed because Currier
language follows the hand.

## Results (D = P(same prefix | same group, same hand) - P(same prefix | other group, same hand))

| Prefix | Labels by section | Labels by page | Paragraph words by section (baseline) |
|---|---|---|---|
| first 2 EVA letters | z 0.3, p 0.39 | z 0.0, p 0.46 | z 1.9, p 0.03 |
| first 3 EVA letters | z 2.1, p 0.017 | z 2.4, p 0.016 | z 8.6, p < 0.001 |
| first 2 glyph units (ch, sh, qo, cth ... as one) | z 0.1, p 0.42 | z 0.1, p 0.45 | z 5.9, p < 0.001 |

Power check: a section-specific two-unit prefix written into a share of the real labels, same test.

| Share of labels given a section prefix | z | p |
|---|---|---|
| 10% | 0.5 | 0.29 |
| 20% | 2.0 | 0.03 |
| 30% | 5.7 | < 0.001 |
| 50% | 14.0 | < 0.001 |

## Reading*

- On the glyph-unit prefix, the measure the power check was run on, labels show **no** section or page clustering
  (z 0.1). The test would have found it at z 5.7 if 30% of labels carried a category prefix. A taxonomic scheme in
  which a third or more of names open with a category mark is therefore not supported.
- The 3-letter prefix gives a weak signal for labels (z about 2, p about 0.02 for section and page). Six label tests
  were run; with a Bonferroni correction (0.05 / 6 = 0.008) neither is significant. Paragraph words cluster by
  section much more strongly (z 8.6), the known section vocabulary, so the labels are, if anything, *less*
  section-specific than the running text.
- Limits. Almost all of the comparison comes from hand 4 (astronomical 79, cosmological 156, zodiac 32 label
  words); hand 1's labels are 233 pharmaceutical against 9 elsewhere, so herbal against pharmaceutical could not be
  tested. Astronomical, cosmological and zodiac labels may all belong to one category ("heavens") in any taxonomy,
  which would hide a real effect. The pharmaceutical section alone (jars and roots on the same pages) is the next
  place to test, with page groups inside it and a finer illustration code (root against leaf against jar) that the
  TSV does not carry.
- Not done: a literature check on label studies (voynich.ninja, Zandbergen's label pages) before this is quoted.
