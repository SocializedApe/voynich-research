# Credits and sources

## People

- **dbourdeau** (github.com/dbourdeau): co-author of the cyphersolver project this work grew out of. The September
  2026 Voynich baseline (`targets/voynich/a1`-`a6`, `b1`-`b4`, `c1`-`c3`, `NOTES.md`), the cipher and copying-scribe
  models in `research/voynich_siblings/`, the `lang/` language-model code and the period cipher transcriptions in
  `targets/voynich/data/period/` were built in that shared project.
- The author of this repository: the October 2026 work (`targets/voynich/meaning/`, `verbose/`, `controls2/`, `tfm/`,
  `glyphs/`, the homophone tests and the write-up).
- Written with an LLM coding agent (Claude, Anthropic); see the caveat in `targets/voynich/README.md`.

<!-- Add or change names here as you agree with your collaborator(s). -->

## Data

| data | where | source and terms |
|---|---|---|
| ZL3b transliteration (Zandbergen-Landini) and IVTFF files | `targets/voynich/data/` | René Zandbergen, voynich.nu; the transliterations are offered under CC0, with a request to acknowledge voynich.nu |
| Gibberish transcriptions | `targets/voynich/meaning/data/gaskell_bowern/` | Gaskell, D. E. and C. L. Bowern (2022), "Gibberish after all? Voynichese is statistically similar to human-produced samples of meaningless text", CEUR Workshop Proceedings 3313, International Conference on the Voynich Manuscript 2022, University of Malta. github.com/danielgaskell/voynich (data/gibberish_transcriptions.zip). Copyright (c) 2022 Daniel E. Gaskell and Claire L. Bowern, provided under the modified MIT licence of that repository, which requires this notice and citation of the paper |
| Pliny, Naturalis Historia (Latin) | `targets/voynich/meaning/data/pliny_raw/` | Latin Wikisource (la.wikisource.org); the text is public domain, Wikisource markup CC BY-SA |
| Enochian Calls (Dee 1584, Casaubon 1659) | `targets/voynich/meaning/data/enochian/` | sacred-texts.com/pag/pr_calls.txt; public-domain text |
| Auchinleck manuscript item list | `targets/voynich/meaning/data/auchinleck_raw/` | item-to-scribe list from the National Library of Scotland's online Auchinleck edition (auchinleck.nls.uk); page texts are not included |
| Herbal / pharmaceutical plant pairs | `targets/voynich/meaning/data/voynich_nu/` | voynich.nu |
| Naibbe cipher: ciphertext of Pliny (`targets/voynich/tfm/data/naibbe.txt`, included); cipher tables (not included) | `targets/voynich/tfm/data/` | Greshko, github.com/greshko/naibbe-cipher (`references/naibbe_tables.csv` and the enciphered Natural History output); MIT licence, copyright Michael A. Greshko |
| Line-by-line transcriptions of medieval manuscripts (not included; fetched by `targets/voynich/lines/fetch_mss.py`, text only) | `targets/voynich/data/external/cremma/` | Cremma Medieval (Pinche et al., CremmaLab; Old French) and CREMMA Medii Aevi (Clérice et al.; Latin), HTR-United, github.com/HTR-United/cremma-medieval and /cremma-medieval-lat; CC BY 4.0; authors and citation in each repository's `htr-united.yml` and citation file |
| Language corpora (not included) | | Project Gutenberg and other public-domain texts; see `lang/README.md` |

## Prior work this builds on or agrees with

- Zhang, X. and V. S. Sheng (2026), "Does the Voynich Manuscript Mean Anything? Calibrated Tests Find Little Trace of
  Language", arXiv 2610.34499.
- "Fingerprinting Gibberish: A Quantitative Comparison of the Voynich and Sloane MS 3188", International Conference
  on the Voynich Manuscript 2022 (abstract book, University of Malta).
- Montemurro, M. A. and D. H. Zanette (2013), "Keywords and co-occurrence patterns in the Voynich manuscript: an
  information-theoretic analysis", PLOS ONE 8(6).
- Davis, L. F. (2020), the five scribal hands; Currier, P. (1976), languages A and B.
- Timm, T. and A. Schinner (2020), the self-citation (copying) hypothesis, basis of the autocopist control.
- Teh, Y. W. (2006), "A hierarchical Bayesian language model based on Pitman-Yor processes", ACL: the hierarchical
  Pitman-Yor process and its Gibbs sampler, used in `targets/voynich/reinforce/` (10 Nov 2026).
