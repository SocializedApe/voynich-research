# controls2: more languages, Arabic-manual ciphers, syllable ciphers (29 Oct 2026)

Status: done (research note, not a decipherment). Scripts: `build_corpora.py` (word lists from eBible.org texts,
downloaded into `data/`, git-ignored), `run_controls.py` (checks 1-3, design fixed in its docstring before any
score), `followup.py` (exploratory, written after seeing the results). Output: `results/controls2.{json,md}`,
`results/followup.json`. Battery and match rule: b3 unchanged (37 items, tolerance max(10%, autocopist spread)), on
the fixed parse (34,834 tokens), so counts compare with `../results/fixed_parse/b3.json` and `c1.json`.

Reference counts (fixed parse): Latin 11, Italian 14, Vulgate 16, Swahili 17, Esperanto 18, Naibbe 21-23, Markov
order 3 trained on Voynich 27 (a fit, not a hypothesis).

## Check 1: languages (Bible text)

| text | /37 | h2 with space | mean len | TTR | token predictability |
|---|---|---|---|---|---|
| Voynich ZL (fixed) | 37 | 2.109 | 4.99 | 0.202 | 0.024 |
| Turkish | 14 | 3.376 | 5.56 | 0.212 | |
| Hungarian (NT) | 15 | 3.504 | 5.32 | 0.201 | |
| Vietnamese, as written / diacritics folded | 11 / 10 | 2.894 / 2.589 | 3.11 | 0.048 / 0.023 | |
| Mandarin, toneless pinyin per syllable | 10 | 2.309 | 2.76 | 0.010 | 0.172 |
| Mandarin, toneless pinyin per jieba word | **19** | 2.741 | 4.24 | 0.110 | 0.139 |
| Arabic transliterated, vocalised / consonantal | 10 / 12 | 3.180 / 3.733 | 7.36 / 4.42 | 0.29 / 0.25 | |

Lindemann & Bowern's Wikipedia h2 (with space, `../data/lb2021_wikipedia_h2.tsv`) covers the rest: Mongolian 3.56,
Uzbek 3.44, Kazakh 3.50, Tatar 3.67, Tibetan 3.14, romanised Hakka / Min Dong 2.84-2.86, Arabic 3.70.

Reading: Turkic and Uralic (suffix chains, vowel harmony) score like the European languages, as Finnish did. Mandarin
by word is the best natural language run through the battery so far (vocabulary, Zipf, Heaps, length and the
near-copy items), but its h2 is 0.63 bit too high and its words are six times too predictable from the previous one.
Written one token per syllable, Mandarin reaches Voynich's h2 (2.31) with a vocabulary 20 times too small.

## Check 2: ciphers from the Arabic manuals (Latin and Italian plaintext)

| cipher | Latin / Italian /37 | h2 with space | reading |
|---|---|---|---|
| homophonic, 40 signs by letter frequency | 5 / 7 | 4.5 / 4.4 | homophones raise h2 and explode vocabulary: the opposite of Voynich |
| same plus nulls | 3 / 9 | 4.8 / 4.6 | worse |
| each letter written as a code word (3 per letter) | 10 / 12 | 3.0 | vocabulary of 60 words |
| two-sign groups (5x5 square, row and column alphabets) | 11 / 13 | 2.1 | right h2, words twice too long, every word locked |

No cipher a 1420s writer could have read about in the Arabic manuals comes near the Naibbe score; most do worse than
the plain language.

## Check 3: syllable ciphers (slot syllabary: onset / nucleus / coda codes)

| variant | Latin / Italian / Turkish /37 |
|---|---|
| one token per syllable | 10 / 8 / 8 |
| one token per plaintext word | 7 / 15 / 10 |
| one token per syllable, 3 codes per slot value | 9 / 8 / 8 |
| follow-up (not pre-registered): one token per word, 3 codes per slot value | 4 / 4 / 4 |
| follow-up: the syllabary on Mandarin words, plain / homophonic | 18 / 6 |

A syllable per token gives Voynich-like h2 (2.3-2.45) with too small a vocabulary; a word per token gives a
language-sized vocabulary with h2 near 3; homophony lowers word-to-word predictability to Voynich's level but
multiplies the vocabulary 2-4 times.

## The corner no new text reaches

Across every text the project has run (b3, c1, controls2, follow-up), the only ones within 0.25-0.33 (log distance)
of Voynich on token predictability and type-token ratio together, with h2 within 0.05 bit, are the Naibbe
ciphertexts (Pliny, Divina Commedia) and Markov chains trained on Voynich (fits). The nearest new text,
homophonic Turkish syllables, matches predictability (0.016) and TTR (0.218) but has h2 2.82. Latin plaintext itself
has predictability 0.034, so low token predictability is not by itself a sign of a cipher.

## Limits

Bible text only (one genre); jieba segmentation is modern; toneless pinyin drops tones (tone letters would raise h2);
the syllabifier is a rule of thumb; the slot syllabary's glyph sets (6/4/5) are one choice, not a search; nothing
here tests a syllabic script of an Asian language with a homophonic layer tuned to Voynich (that would borrow targets
from Voynich, as #36 did).
