# Do Voynich labels occur in their own page's text? Results, 28 Oct 2026

Script: `label_page_test.py` (seed 2, 2,000 permutations). Data: ZL 3b TSV, labels (locus L) and paragraph text
(locus P), words of 3+ letters without unread glyphs.

## Why

The genre table (`physicians_ciphers.md`) predicts that, if Voynich is an enciphered medical book, labels name
things (plants, roots, drugs). In a labelled herbal or drug book the name of the thing drawn is normally repeated in
the text beside it. Copy-and-modify generation (Timm & Schinner) predicts instead that words echo nearby words with
small changes. Zandbergen (voynich.nu/extra/labels.html) notes qualitatively that label words "rarely" appear near
their label; this puts a number and a null model on that.

## Method

For each label token on a folio with paragraph text (585 of 642): E = the label word occurs in that folio's
paragraphs; N = a word at edit distance 1 occurs but not the word itself. Null: labels shuffled among folios of the
same section and hand (the paragraph text stays put). Baseline with the same machinery: 600 paragraph words (the
middle word of randomly chosen lines) tested against the rest of their own folio, own line removed.

## Results

| Items | Exact match on own page | Near match (edit distance 1, no exact) |
|---|---|---|
| Labels (585) | 52 against 49.6 +- 4.0 expected; ratio 1.05; z 0.6; p 0.32 | 132 against 126.0 +- 6.4; ratio 1.05; z 0.9; p 0.20 |
| Paragraph words (600) | 259 against 211.9 +- 7.5; ratio 1.22; z 6.3; p < 0.001 | 188 against 206.0 +- 9.1; ratio 0.91 (lower because exact hits are counted first) |

Labels by section: pharmaceutical 233, cosmological 156, biological 106, astronomical 64, text-only 21, herbal 5.

## Reading*

- Pages have their own vocabulary (paragraph words recur on their own page 22% more than chance, z 6.3), and the
  test, at the same sample size, detects it. Labels show nothing: a label word is no likelier to appear in its own
  page's text than in the text of another page of the same section and scribe.
- Labels are not echoed with small changes on their page either (near-match ratio 1.05), so this does not support
  copy-and-modify from the labels into the text.
- So the label and the text beside it look independent. For a herbal or drug book in which labels name the thing
  drawn and the text discusses it, that is unexpected; it fits labels as a separate layer (added later, by another
  hand, as a list, or as decoration). It does not separate the cipher and meaningless hypotheses by itself.
- Limits: no positive control from a real labelled 15th-century herbal (a transcribed one, labels and text, would be
  the right comparison: does a plant's name recur in its own chapter?); herbal-section labels are only 5 here
  (most herbal pages carry no label); 52 exact hits is a small count.
