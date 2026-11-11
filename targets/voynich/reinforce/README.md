# Reinforcement models: where word re-use lives, and a generator fitted by likelihood (10 Nov 2026)

Every account that fits part of the Voynich profile has words being re-used: from what was written just before
(self-citation), from what the scribe habitually writes (hand conventions), from a shared stock (one template). A
hierarchical Pitman-Yor process (Teh 2006) is the standard Bayesian model of exactly that: a tree of restaurants
(book > hand > section > quire > page > line, and in later versions a Currier-language level and a previous-word
context) in which each node re-uses what was already used there with a rich-get-richer rule and passes the rest up
to its parent; two parameters per level (discount d, concentration theta) say how much re-use happens at that
level, and 'passed up' = the share of a level's draws that it did not re-use. Fitting it gives a 'where does re-use
live' profile; generating from the fitted parameters gives a candidate generator whose only inputs are the fitted
re-use strengths, the page/line skeleton and a base distribution of word parts borrowed from Voynich. Nothing is
tuned on the b3 battery; the fit is by Gibbs sampling of the seating with Teh's auxiliary-variable hyperparameter
updates (`hpy.py`; parameter recovery on synthetic data checked, lower levels recovered well, top levels weakly
identified; a fixed-parameter likelihood check, `check_fit.py`, confirmed the fitted values beat lower discounts).

## 1. Whole words: Voynich's re-use is at the scribe, section and quire levels, not the page (`hpy.py fit`)

Share of each level's draws passed up to its parent (1.00 = the level re-uses nothing), whole-word model, G0 uniform:

| text | hand | section | quire | page | line |
|---|---|---|---|---|---|
| Voynich | 0.82 | 0.84 | 0.87 | 0.95 | 1.00 |
| Pliny laid out leaf by leaf (`pliny_fit.py`) | 0.98 | 0.97 | 0.93 | 0.97 | 1.00 |
| Pliny as a stream | 0.98 | 0.96 | 0.91 | 0.96 | 1.00 |
| Latin poured | 0.99 | 1.00 | 0.99 | 1.00 | 1.00 |
| English poured | 0.96 | 0.99 | 0.92 | 0.96 | 1.00 |
| Naibbe cipher | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| autocopist | 1.00 | 0.99 | 1.00 | 0.73 | 1.00 |
| gibberish volunteers | 1.00 | 1.00 | 0.96 | 0.82 | 1.00 |

Held-out likelihood with level ablations (`ablate.py`, every fifth page predicted token by token): the hierarchy
saves 0.23 bits/token over a flat model for Voynich (hand level alone 0.04), 0.02 for English, nothing for Latin
and Naibbe, 0.57 for the gibberish volunteers (all at the page level: each volunteer's text is a block of pages).

Reading. Voynich's whole-word re-use sits at the hand, section and quire levels (13-18% of draws re-used at each),
five to ten times a real topical text's; at the page level it re-uses 5%, against 3% for Pliny by leaf, 4% for
English, 27% for the autocopist and 18% for the gibberish volunteers. The page-level copying of the self-citation
generator is five times too strong; what Voynich has is convention-level re-use. But the discounts near 1 at every
level below the book say that a whole-word model finds little to re-use at the page or line: Voynich's locality is
in near-copies (0.64 of tokens have an LD<=1 twin on the page), which a whole-word model cannot see. Exact
same-page repeats beyond the hand/section/quire vocabulary are 0.03 of tokens (shuffle decomposition in the
session log). So the unit that is re-used is the word part.

## 2. Word parts: the slot-level reinforcing improviser (`slots.py`, `slots2.py`, `slots3.py`)

Each word is parsed into slots (meaning/slots_ab.py: prefix | gallows | middle | ending); v2 joins prefix and
gallows into an opener and the middle and ending into a tail (opener | tail, the split at which Voynich's start-end
dependence is smallest, slot_independence.md), and adds a Currier-language level above the hands; v3 gives the
opener a context level at the top of its hierarchy (the last glyph unit of the previous word, or '^' at a line start),
so that the line-bound chain found in lines/boundaries.py is learned, not borrowed. Each slot has its own fitted
hierarchy; a word is one draw per slot at the line node; base distributions are the slot's empirical token
distribution (borrowed from Voynich) with 20% of a glyph-unit trigram template over tail types for new tails.

Fitted opener re-use (v2, share passed up): book 0.31, lang 0.48, hand 0.66, section 0.58, quire 0.42, page 0.69,
line 0.97: the opener is re-used at every level, most at the quire and the language. Tail: 1.00, 0.98, 0.95, 0.88,
0.85, 0.91, 1.00: re-used at the section, quire and page, a little.

Scores (b3 battery, 37 items; held-out = the 30 outside hybrid_model.TUNED_B3; scribe ratios as scribe_ratio.py;
drift = JSD of merged-glyph bigrams; edge X = within-line coupling of lines/boundaries.py):

| text | matched/37 | held-out/30 | between scribes / within | same scribe, other doc / within | JSD A vs B | JSD quire halves within hand x section | edge X within line |
|---|---|---|---|---|---|---|---|
| Voynich | 37 | 30 | 2.96 [2.18-3.59] | 2.00 [1.87-2.15] | 0.101 | 0.052 | 0.060 |
| best earlier models (cipher + scribe, code + scribe, improviser + layer; meaning/README.md) | | 24-25 | 1.0-2.3 | 1.0-1.5 | | | |
| v1, four independent slots, seeds 19 / 7 | 28 / 25 | 24 / 20 | 3.79 / 4.58 | 2.51 / 3.00 | 0.086 / 0.084 | 0.097 / 0.121 | 0.003 |
| v2, opener + tail, lang level, seeds 19 / 7 / 3 | 27 / 28 / 22 | 23 / 24 / 19 | 2.92 / 3.20 / 4.09 | 1.78 / 1.93 / 1.89 | 0.072 / 0.091 / 0.121 | 0.080 / 0.070 / 0.130 | 0.003 / 0.004 / 0.025 |
| v3, opener in context of the previous word (line-bound), degenerate levels dropped, five seeds | 21-28 | 18-24 | 1.56-1.87 | 1.32-1.42 | 0.020-0.051 | 0.038-0.054 | 0.026-0.080 |
| v2 three slots (opener, middle, ending), no context, seeds 19 / 7 / 3 | 14 / 15 / 15 | 12 / 15 / 15 | 3.74 / 3.08 / 3.00 | 2.19 / 2.02 / 1.98 | 0.141 / 0.085 / 0.089 | 0.109 / 0.101 / 0.091 | 0.003-0.009 |
| v4, opener in context + middle + ending, degenerate levels dropped, five seeds | 13-21 | 13-19 | 2.49-2.95 | 1.68-1.97 | 0.054-0.097 | 0.059-0.090 | 0.044-0.067 |
| v5, chained slots (opener in context of the previous word, middle of the opener, ending of opener + middle), five seeds | 23-29 | 20-25 | 1.67-2.03 | 1.38-1.48 | 0.037-0.053 | 0.046-0.058 | 0.044-0.062 |

v2 is the first model in this repository that sits inside Voynich's intervals on both scribe ratios while matching
as many held-out battery items as the best hand-tuned cipher and code models, and it produces A/B drift of the
right order (0.07-0.09 of 0.10) from nothing but fitted re-use strengths. Seed 3 of v2 ran away (one tail table
captured a hand's draws: adjacent repeats 5%, word-to-word predictability 0.084): with a fitted discount near 1 and
a small concentration, the generation can lock onto an early table, which the fit never does because the data pin
the seating; v3 drops such levels (d >= 0.99) from the generation.

v3 and v4 add a self-consistency check (the share of draws passed up per level in the generated text against the
fitted share): v4 passes it at every level (e.g. ending at the language level 0.43 against 0.41, opener in context
0.60 against 0.62), so v4 is a faithful sample of its fit, and what it reproduces is reproduced by fitted re-use
alone: both scribe ratios inside or at the edge of Voynich's intervals in five seeds of five, A/B drift 0.05-0.10
of 0.10, the within-line coupling 0.04-0.07 of 0.06 with zero across lines. v3, with the tail as one slot, cannot
carry the tail's A/B convention (3,800 values, 70% hapax: its language and hand levels fit at d = 1 and are
dropped) and loses the scribe ratios; v4, with the ending as its own slot (30 values, re-used 55-65% at the
language, hand and section levels), recovers them. The price of independent slots is the word itself: v4's words
are too long (mean 6.3 against 5.0, 13-21% of nine or more glyphs) and too novel (0.43-0.57 of tokens are Voynich
words), so the character and length items fail and the battery count falls to 13-21.

v5 chains the slots (the word becomes a chunk-level Markov chain whose transition tables are re-used by
location) and is self-consistent at every level. It keeps the words (0.50-0.59 of tokens Voynich words), reaches
25 of 30 held-out items in its best seed (the highest count of any model in the repository; 20-25 over five
seeds), gets the line-bound coupling (0.044-0.062 of 0.060, zero across lines) and the quire drift (0.046-0.058
of 0.052) right, but carries only half the A/B convention (JSD 0.04-0.05 of 0.10, k_jsd_halves 0.02 of 0.06) and
gives scribe ratios of 1.7-2.0 / 1.4-1.5: with the context level above the language level, the ending's
language-level re-use drops from 59% (v4) to 47% and the convention is partly absorbed into the chain. Its
remaining misses, every seed: word-length spread (sd 2.6-2.9 against 1.8, 9-14% of words of nine or more glyphs:
the template's new middles run long), line-initial gallows (0.01-0.09 against 0.22: a convention tied to the '^'
context that each seed's rich-get-richer draw sets at random), adjacent repeats (1-2.6% against 0.8%) and the
within-page near-copy excess (e_ratio 1.00 against 1.14).

So the fitted reinforcement models bracket the same trade-off the hand-tuned duel of #33 found: v4 (slots
independent within the word) carries the scribe conventions and the chain but not the word; v5 (slots chained)
carries the word, the chain and the quire drift but only half the convention. In the data the ending convention is
categorical and context-free (-edy against -ol, -y on the same stems, #35) and the chain is strong at the same time;
a tree hierarchy has to put one above the other. A product of the two (a context tree for the transitions times a
language and hand habit on each ending, the 'convention layer' of #36 fitted rather than tuned) is the next model,
and is not a tree.

What v2 misses, every seed: word length too dispersed (sd 2.36-2.47 against 1.79; words of 9+ glyphs 8-11% against
2.4%) because opener and tail are drawn independently and new tails from the template run long; long-range
clustering too strong (MZ peak 0.49 against 0.31, peak scale 1024 against 512) and quire drift about 1.5 times too
large; adjacent exact repeats 1.2% against 0.84%; and no word-to-word coupling (v3 is the answer to that).

## 3. The volunteers with their own lines and pages (`volunteers.py`, `gibberish_fit.md`)

Every earlier use of the Gaskell-Bowern volunteers here and in `lines/` poured their words into the Voynich skeleton.
Their transcriptions keep the written lines, the page separators and the paragraph blanks (38 writers, 88 pages, 1,617
lines, 10,049 words, 6,840 types), so the same tests and the same fits were run on them as written, with Latin,
English, the autocopist and the Voynich text poured into the volunteers' skeleton as controls, and Voynich refitted
with the same script-neutral word split (first unit | rest | last unit) so that the two corpora get one model.
Hierarchy book > batch > writer > page > line; a writer's whole output (80-480 words) is about one Voynich page.

| measure | volunteers, own lines | Voynich |
|---|---|---|
| word-to-word coupling X inside a line / across a line break, null shuffled within each page | 0.003 / 0.001 | 0.059 / -0.001 |
| writers (Voynich: pages of the same size, median 146 words) with coupling at z >= 3 against their own shuffles | 5 of 35 | 62 of 128 |
| first-unit JSD of the line-first word against the interior (null) | 0.012 (0.006) | 0.205 (0.002) |
| word length, line-first / line-last word against the line mean | +0.27 / +0.27 | +0.43 / -0.36 |
| near-copies one line up, interior words, aligned within one position / column-shuffle null (z) | 1.06 (+2.2) | 0.99 (-0.7) |
| whole-word re-use, share of draws: root (stock shared across writers or hands) / writer or hand / page | 0 / 20% / 7% | 47% / 18% / 5% |
| types per token | 0.68 | 0.20 |
| scribe ratio on last units, 100-word docs: between / within; same scribe, other doc | 3.40 [2.90-3.97]; 1.35 | 2.13 [1.87-2.54]; 1.75 |
| scribe ratio on glyph bigrams, 100-word docs | 2.31 [2.06-2.57]; 1.19 | 2.29 [1.82-2.59]; 1.69 |
| excess MI of the last unit given the unit before it / of the second unit given the first | 0.09 / 0.11 | 0.56 / 0.41 |
| slot model, bits per token gained by the context: opener (previous word's last unit) / middle / ending | -0.18 / +0.76 / +0.81 | +0.27 / +1.12 / +1.39 |
| ending re-used at the writer or hand level, location model -> chain model | 64% -> 49% | hand 40% -> 30%, lang 48% -> 47% |

Controls in the volunteers' skeleton, whole-word re-use at root / writer / page: English 51% / 5% / 3%, Latin 22% /
0 / 0, Voynich poured in reading order 45% / 4% / 2%, autocopist 15% / 1% / 24%.

Reading. What the volunteers share with Voynich is the scribe. Each writer has strong personal habits in openers and
endings (the ending habit more distinctive than a Voynich hand's), re-uses his own words at 20% of draws (a hand
18%), and keeps that habit as a context-free layer on top of a within-word chain, which is the two-source structure
of section 2 (ending re-use at the writer 64%, still 49% once the preceding unit is known). What they do not have is
everything that makes Voynich a line-and-book structure rather than a heap of personal texts: no coupling between
adjacent words (0.003; five of 35 writers show some at z >= 3, against half of Voynich's pages at the same size), so
nothing that could restart at a line; no line-first vocabulary (0.012 against 0.205) and a last word that is longer,
not shorter; a within-word chain four to six times weaker (0.09 against 0.56; 0.8 against 1.4 bits); and no shared
stock between writers at all (the root of the fit is a pass-through at d = 1.00), where Voynich takes 47% of its
root draws from a stock shared across hands. The one thing the volunteers do that Voynich does not is align a
near-copy weakly under its source (1.06, z 2.2, the autocopist's direction), which fits people with the page in
front of them. Casual improvisation by untrained writers therefore gives the scribe-level habits and not the
line-level or book-level structure; whether a practised writer of one taught system would is untested, as no such
sample exists. The remark in `meaning/README.md` that the volunteers offer no page structure to compare was wrong:
the files keep it. Limits: one sitting of 1-3 pages per writer, modern English speakers in Latin letters, the DA
batch two writers; the writer level sits at small nodes (a page's worth) and the root over 38 writers, not 5 hands.

## 4. Second session (10-11 Nov 2026): the length budget, the product model, and generator v6

### 4.1 A length budget between the slots (`lengths.py`, `lengths.md`)

(Qualified in 4.6: the budget is found without the recipe as well, and Latin words have a stronger one against
their own letter chain, so it is a constraint on generators and not a mark of Voynich.)

Among words whose opener ends in the same glyph unit, a longer opener is followed by a shorter middle (r -0.22),
and among words with the same last unit before the ending a longer stem gets a shorter ending (r -0.18); the
variance of the word length is 0.70 of the sum of the slot variances. Resampling the middle and the ending from
book-wide tables (opener kept, no location, no template):

| conditioning | length sd (chars) | 9+ chars | tokens that are Voynich words | variance ratio |
|---|---|---|---|---|
| Voynich | 1.79 | 0.024 | 1.00 | 0.70 |
| independent slots (slots4's assumption) | 2.31 | 0.079 | 0.64 | 1.00 |
| chain on the last unit (slots5's assumption) | 1.97 | 0.043 | 0.85 | 0.83 |
| chain + length class (units written so far, binned) | 1.82 | 0.027 | 0.88 | 0.70 |
| middle given the whole opener, ending given the last unit | 1.92 | 0.037 | 0.86 | 0.79 |
| middle given the whole opener, ending given the whole middle | 1.81 | 0.026 | 0.93 | 0.70 |
| chain on the last two units | 1.85 | 0.032 | 0.89 | 0.74 |

So a chained generator has to know how much of the word is already written; a last-unit chain alone leaves half of
the excess. slots5's own spread (2.6-2.9) is larger than the chain null's 1.97: most of its excess comes from
generating the transition structure (4.3 below), not from the missing budget. Control: the Naibbe cipher, in the
same parse, has the same budget (within-context r -0.24 / -0.11, variance ratio 0.65), so the budget does not
separate a cipher from a generator; the autocopist has almost none within contexts (-0.04 to -0.10 / -0.01 to -0.02).

### 4.2 Is the convention a context-free habit on a shared transition rule? (`product.py`, `product_heldout.md`)

Held-out bits per token (every fifth page predicted token by token; models fitted on three fifths, exponents and
mixture weight chosen on the remaining fifth). product = P(v) x [P(v | context) / P(v)] x [P(v | location) / P(v)].

| text | slot | context only | location only | best tree | product | product, fitted exponents | mixture | product - best tree [95%] |
|---|---|---|---|---|---|---|---|---|
| Voynich | opener | 3.358 | 3.445 | 3.258 | 3.252 | 3.243 | 3.306 | -0.006 [-0.030, +0.019] |
| Voynich | middle | 4.200 | 4.577 | 4.094 | 4.154 | 4.137 | 4.184 | +0.060 [+0.040, +0.084] |
| Voynich | ending | 3.343 | 3.930 | 3.118 | 3.161 | 3.161 | 3.332 | +0.042 [+0.022, +0.064] |
| Voynich | middle, context with length class | 4.194 | 4.577 | 4.100 | 4.147 | 4.131 | 4.179 | +0.047 [+0.019, +0.078] |
| Voynich | ending, context with length class | 3.324 | 3.931 | 3.138 | 3.145 | 3.141 | 3.310 | +0.007 [-0.023, +0.034] |
| slots5 sample (truth: tree, chain above location) | opener / middle / ending | | | 2.565 / 4.100 / 2.456 | 2.768 / 4.250 / 2.687 | | | +0.21 / +0.15 / +0.23 |
| slots4 sample (truth: opener a tree; middle, ending location only) | opener / middle / ending | | 2.659 / 5.482 / 2.699 | 2.320 / 5.482 / 2.699 | 2.475 / 5.563 / 2.701 | | | +0.16 / +0.08 / +0.00 |

By the rule set before the run the product is not the better account: it ties the best tree on the opener and loses
by 0.04 on the ending and 0.06 on the middle. But the calibration gives the scale: on a sample of the fitted tree
the product loses by 0.15-0.23 bits on every slot, in Voynich by 0.00-0.06. Of the bits the location adds once the
context is known, a context-free habit recovers all on the opener (0.106 of 0.100), 81% on the ending (0.182 of
0.225) and 43% on the middle (59% with fitted exponents). The fitted exponent on the location ratio is 0.75-1.0: the
habit is counted nearly in full on top of the chain. A linear mixture is worse than the product everywhere (ending
+0.17). The best tree always has the chain above the location; the convention above the chain is 0.1-0.4 worse.
Reading: Voynich's scribe and language habits are mostly the same whatever precedes in the word; a sample of the
slots5 tree invents a separate habit per context, which Voynich does not have, and that is why slots5 lost half
the convention in the marginal statistics.

### 4.3 Generator v6 (`slots6.py`, `slots6_gen.md`)

Contexts with the length class of 4.1; exponents from 4.2; the template rate for new middles set by Good-Turing
(middle types seen once / tokens = 0.035) instead of the hand-set 20%. Five seeds each.

| variant | matched/37 | held-out/30 | between scribes / within | same scribe, other doc | JSD A vs B | edge X within line | Voynich words | length sd | 9+ chars |
|---|---|---|---|---|---|---|---|---|---|
| Voynich | 37 | 30 | 2.96 | 2.00 | 0.101 | 0.060 | 1.00 | 1.79 | 0.024 |
| slots5 (first session) | 23-29 | 20-25 | 1.67-2.03 | 1.38-1.48 | 0.037-0.053 | 0.044-0.062 | 0.50-0.59 | 2.6-2.9 | 0.09-0.14 |
| len5: slots5 + length-class contexts + Good-Turing rate | 24-28 | 21-24 | 1.41-1.91 | 1.19-1.36 | 0.026-0.059 | 0.031-0.129 | 0.51-0.59 | 2.53-2.97 | 0.09-0.13 |
| prod6: product of two reinforced models, fitted exponents | 3, 8 (third seed collapsed to one value) | | | | | | | | |
| prod6g: the same, exponents rescaled to sum to one | 21-29 | 17-25 | 1.27-1.46 | 1.15-1.29 | 0.013-0.029 | 0.001-0.003 | 0.54-0.72 | 2.52-2.70 | 0.06-0.16 |
| prod6t: transition tables borrowed, location habit generated | 28-30 | 23-25 | 1.43-1.49 | 1.29-1.35 | 0.010-0.020 | 0.037-0.041 | 0.86-0.87 | 1.92-1.95 | 0.033-0.035 |
| prod6e: prod6t + the last word's own tables | 28-31 | 23-26 | 1.42-1.50 | 1.31-1.34 | 0.011-0.015 | 0.040-0.043 | 0.86-0.87 | 1.93-1.96 | 0.035-0.037 |

- The length class does not help a generator that makes its own transition structure (len5): a tree generated from
  re-use strengths gives each context a random re-weighting of the slot frequencies, not Voynich's table, so which
  middles follow which openers is arbitrary and the budget has nothing to act on.
- A product of two reinforced models with exponents summing to more than one is an urn with super-linear feedback
  and collapses (prod6); with the exponents pooled to one it is stable but has no chain (edge X 0.001-0.003) and
  no better words (prod6g).
- With the book-wide tables borrowed (as the slot frequencies and the template always were), the word comes out
  right: length sd 1.93 against 1.79, 86-87% of tokens Voynich words, types per token 0.19-0.20 against 0.20, the
  line-bound coupling at two thirds (0.04 of 0.06, zero across lines), 28-31 of 37 and up to 26 of 30 held out, the
  highest counts in the repository with the smallest spread over seeds. The line-end tables (prod6e) change little.
- The convention is lost: A/B JSD 0.010-0.020 against 0.101, scribe ratios 1.4-1.5 / 1.3. A location habit that has
  to grow by reinforcement out of draws dominated by a fixed table does not grow; in slots4 it grew because the
  location model was the only source of each slot. Every item prod6t misses is locality: adjacent repeats (0.006
  against 0.008), near-copies within ten tokens, the long-range clustering peak (0.11 against 0.31), JSD of halves.

Where this leaves the model: the word needs the book-wide transition tables with the length budget; the convention
is nearly context-free (4.2) but does not emerge from re-use on top of those tables at the fitted strength, so it
has to be a parameter of the language and the hand (a tilt on the ending and opener tables drawn once per
language, hand, section and quire), with page-level re-use on top for the locality items. That model (tables x
drawn tilts x local re-use) is the next one, and is a job for Kaggle rather than the laptop.

### 4.4 Generator v7: the convention as a drawn tilt, plus copying (`slots7.py`, `slots7_gen.md`, 11 Nov 2026)

P(v | context, location) proportional to T(v | context) x exp(b x sum of tilts), T the tables of prod6e, one normal
log-tilt vector per language, hand, section and quire, drawn once per text, the same in every context. The sd per
level is a moment estimate from Voynich (opener 0.39, 0.19, 0.24, 0.13; middle 0.40, 0.21, 0.24, 0.13; ending 0.83,
0.22, 0.25, 0.18 for language, hand, section, quire), b = 0.75 from 4.2. Copying: with probability q a word takes
the opener and middle of one of the previous 10 words on the page and draws only its ending.

| variant (five seeds) | matched/37 | held-out/30 | between scribes / within | same scribe, other doc | JSD A vs B | edge X within line | Voynich words | length sd |
|---|---|---|---|---|---|---|---|---|
| Voynich | 37 | 30 | 2.96 | 2.00 | 0.101 | 0.060 | 1.00 | 1.79 |
| prod6e (4.3) | 28-31 | 23-26 | 1.42-1.50 | 1.31-1.34 | 0.011-0.015 | 0.040-0.043 | 0.86-0.87 | 1.93-1.96 |
| tilt, q 0 | 24-29 | 20-24 | 1.21-1.60 | 1.02-1.10 | 0.023-0.051 | 0.031-0.049 | 0.82-0.86 | 1.95-2.08 |
| tilt, q 0.1 | 25-32 | 20-25 | 1.30-1.65 | 1.10-1.15 | 0.022-0.050 | 0.025-0.037 | 0.81-0.86 | 1.94-2.08 |
| tilt, q 0.2 | 25-32 | 19-26 | 1.43-1.74 | 1.20-1.23 | 0.024-0.054 | 0.020-0.030 | 0.81-0.86 | 1.95-2.08 |
| no tilt, q 0.1 (control) | 26 | 21 | 1.05-1.08 | 1.04-1.08 | 0.003 | 0.030-0.033 | 0.85 | 1.93-1.96 |

- A normal tilt of the measured variance carries a quarter to a half of the A/B difference (0.02-0.05 of 0.10) and
  none of the 'same scribe, other document' ratio (1.0-1.2 against 2.00; prod6e's page-level re-use gave 1.3). The
  variance is right by construction and the effect is too small: Voynich's convention is concentrated in a few
  values that are nearly on or off (-edy 492 against 1), which a normal log-tilt of the same variance spreads over
  all values. The convention is categorical, not a graded preference. (Corrected in 4.5: the tilt here was also
  multiplied by b = 0.75, which accounts for part of the shortfall; the evidence for the categorical shape is the
  fourth moment given there.)
- Copying does what it was added for: at q 0.1 the near-copy and adjacent-repeat items are matched (e_w10, e_ratio,
  d_adj_exact), at q 0.2 they overshoot; the best seeds reach 32 of 37 and 26 of 30 held out. It costs chain (edge X
  0.025-0.037 of 0.060), since a copied opener ignores the previous word.
- Still missed by every seed: the long-range clustering peak (0.09-0.15 against 0.31), JSD of halves (0.014 of
  0.062), length sd (1.94-2.08 against 1.79).

### 4.5 Generator v8: the shape of the convention, a page drift, and where the rest of A/B sits (`slots8.py`, `slots8_gen.md`, 11 Nov 2026)

Correction to 4.4 first. slots7 multiplied the drawn tilt by the location exponent b = 0.75 of `product.py`, although
its sd was estimated for the full log-ratio. That alone weakened the convention: the same normal tilt at b = 1
(`norm8`) carries 0.035-0.086 of the A/B difference of 0.101, not 0.02-0.05. 'A quarter to a half' was partly this
choice, and the battery result of 4.4 did not show that the convention is categorical.

What does show it is the fourth moment. With x = log((n + 0.5) / (e + 0.5)) per value and node (e >= 5) and the
sampling noise taken out of the second and fourth moments, a tilt that is +s or -s with probability pi and zero
otherwise has:

| slot | share of values switched, pi (lang, hand, section, quire, page) | size of a switch s, log units |
|---|---|---|
| opener | 0.04, 0.02, 0.02, 0.01, 0.06 | 1.88, 1.42, 1.55, 1.24, 1.16 |
| middle | 0.02, 0.04, 0.01, 0.01, 0.02 | 2.72, 1.09, 2.13, 1.64, 1.50 |
| ending | 0.05, 0.04, 0.04, 0.02, 0.09 | 3.78, 1.12, 1.21, 1.16, 1.21 |

One value in twenty to fifty is switched per level, and a language switches an ending by a factor of about 40 (e^3.78),
a hand, section or quire by a factor of about 3. A normal tilt would give pi = 1/3 under this estimate. The estimate
treats the noise of x as normal with variance 1/e, which is rough at e near 5. The page tilt has lag-1 correlation
0.33 (opener), 0.18 (middle), 0.37 (ending) between consecutive pages of a quire.

Six variants, five seeds, copying at q = 0.1, b = 1, nothing tuned on the battery (range over seeds):

| variant | matched/37 | held-out/30 | between scribes / within | JSD A vs B | clustering peak (h_peak_R) | adjacent-page Jaccard excess | JSD halves |
|---|---|---|---|---|---|---|---|
| Voynich | 37 | 30 | 2.96 | 0.101 | 0.31 | 0.037 | 0.062 |
| prod6e (4.3) | 28-31 | 23-26 | 1.42-1.50 | 0.011-0.015 | 0.09-0.12 | 0.010-0.021 | 0.008-0.012 |
| tilt7, q 0.1 (4.4, b 0.75) | 25-32 | 20-25 | 1.30-1.65 | 0.022-0.050 | 0.08-0.14 | 0.013-0.022 | 0.010-0.018 |
| norm8: normal tilt | 25-33 | 20-27 | 1.44-2.09 | 0.035-0.086 | 0.13-0.20 | 0.022-0.028 | 0.015-0.028 |
| cat8: switched tilt | 25-32 | 20-27 | 1.30-2.28 | 0.023-0.128 | 0.10-0.21 | 0.017-0.039 | 0.012-0.041 |
| cat8p: cat8 + page drift | 26-31 | 21-25 | 1.59-2.72 | 0.034-0.136 | 0.16-0.25 | 0.021-0.036 | 0.020-0.052 |
| emp8: Voynich's own tilt (control) | 29-31 | 24-25 | 2.06-2.11 | 0.072-0.076 | 0.19-0.21 | 0.027-0.031 | 0.044-0.047 |
| emp8p: emp8 + page drift | 29-31 | 24-25 | 2.11-2.25 | 0.072-0.077 | 0.21-0.22 | 0.024-0.031 | 0.043-0.048 |
| lang8: emp8 with tables per language (control) | 31-33 | 24-26 | 2.23-2.28 | 0.092-0.095 | 0.24-0.25 | 0.032-0.036 | 0.051-0.054 |

- The battery does not separate the two shapes. The switched tilt gives a wide spread between seeds (A/B 0.023 to
  0.128, Voynich's 0.101 inside it), because a few large switches matter only when they land on a frequent value;
  the normal tilt gives a narrower spread below Voynich. The evidence for the categorical shape is the moment table,
  not the scores.
- Voynich's own context-free convention (`emp8`) reaches three quarters of the A/B difference (0.072-0.076), three
  quarters of JSD halves and two thirds of the clustering peak, and no more. A convention that acts on slot
  frequencies alone, however well chosen, leaves a quarter of A/B out.
- Most of that quarter is in the chaining rule. With the transition tables built separately for A and B (`lang8`,
  added after the first five were scored) A/B is 0.092-0.095, every seed scores 31-33, and the clustering peak, the
  Jaccard excess and JSD halves each move a further step towards Voynich. The two languages differ in how parts follow
  one another, not only in which parts they prefer. This qualifies 4.2: the context-free product is close in held-out
  likelihood, and the interaction it leaves out is visible in the A/B statistic.
- The page drift adds a little clustering (peak 0.16-0.25 from 0.10-0.21; matched by two seeds of five in cat8p) and
  nothing else. It also pushes the near-copy items over in some seeds (d_adj_ld1 up to 0.084 against 0.042).
- Still missed by every seed of the best variant (lang8): JSD halves (0.051-0.054 of 0.062), the adjacent
  near-copy share (0.030 of 0.042), the scale of the clustering peak. The clustering peak itself (0.24-0.25 of 0.31)
  and the Jaccard excess are matched by two seeds of five. No variant passes 33 of 37. lang8 and emp8 borrow the
  convention from Voynich and are controls: they say what form the convention has, they are not generators of it.

### 4.6 Robustness checks (`robust.py`, `recipe_free.py`; 11 Nov 2026, third session)

**The ceiling of the battery, and held-out generation (`robust.md`).** One half of Voynich scored against the other
with the b3 rule (the autocopist seeds regenerated on the reference half), both directions; and the two best v8
variants built from one half and generated on the skeleton of the other ('held-out') beside built from and scored
against the same half ('in-sample'); five seeds:

| split, direction | tokens in the reference half | other half of Voynich /37 | /30 held-out items | lang8 in-sample | lang8 held-out | cat8p in-sample | cat8p held-out |
|---|---|---|---|---|---|---|---|
| odd / even pages, 0 | 17570 | 35 | 28 | 26-27 | 27-28 | 17-30 | 19-27 |
| odd / even pages, 1 | 17264 | 36 | 29 | 34-36 | 34-35 | 29-34 | 24-34 |
| alternate quires, 0 | 15950 | 33 | 27 | 34-36 | 28-30 | 28-34 | 24-29 |
| alternate quires, 1 | 18884 | 30 | 25 | 31-33 | 31-33 | 20-32 | 23-31 |
| first / second half, 0 | 9341 | 28 | 21 | 30-31 | 23-26 | 25-33 | 23-29 |
| first / second half, 1 | 25493 | 22 | 16 | 27-28 | 21-24 | 23-31 | 21-30 |

- Voynich does not match itself on all 37. Interleaved pages match on 35-36; alternate quires on 30-33; the two
  halves of the book on 22-28. A generator at 31-33 of 37 against the whole book is where another set of quires of
  the same book is, and three items below interleaved pages. The items the other half misses in the interleaved
  split are the adjacent-page Jaccard excess (an artefact of removing every second page) and the scale of the
  clustering peak.
- The score moves by up to nine items with the half used as reference (lang8 in-sample 26-27 against 34-36 on the two
  halves of the same split), because the tolerances come from two autocopist seeds on that half. Differences of one to
  three items between generator variants, here and in sections 2 to 4.5, are inside this noise. The ranges over five
  seeds were already as wide.
- Held out, lang8 keeps its score when the source pages are interleaved with the target pages (27-28 against 26-27;
  34-35 against 34-36) and loses up to six items when whole quires are held out in one direction (28-30 against
  34-36; 31-33 against 31-33 in the other). The borrowed tables are not a page-level overfit; part of what they carry
  is quire-level.

**Without the word recipe (`recipe_free.md`).** The length budget, the switched convention and the A/B chaining
difference restated on glyph units and whole words:

- Length. Variance of word length over that of a unit Markov chain fitted to the same tokens: Voynich 0.31 / 0.70 /
  0.90 (orders 1, 2, 3), Naibbe 0.23 / 0.62 / 0.87, Latin 0.19 / 0.33 / 0.62. The budget of 4.1 is there without the
  recipe (0.70 at order 2, the same number as the recipe's variance ratio), **and it is not a property of Voynich**:
  Latin words are narrower still against their own letter chain. Any vocabulary of real words has it. 4.1's reading
  ('the word is not a concatenation of independent draws') stands as a constraint on generators and says nothing
  about what kind of text this is.
- Convention. Share of values switched and size of a switch by language: whole words 0.09 and 3.49 (a factor of
  33), first unit 0.08 and 1.31, last unit 0.19 and 0.37. The few large switches of 4.5 are a property of whole
  words and of the recipe's endings; the last glyph alone does not carry them (-edy and -y end in the same glyph).
- Chaining. Next-unit models on held-out pages (odd/even, both directions), bits per unit: per-language chain less
  the book chain with a language tilt of unit frequencies, -0.035 to -0.044 at order 1 (pseudocounts 1, 10, 100; all
  intervals below zero); at order 2, +0.012 with pseudocount 1 and -0.016, -0.029 with 10 and 100 (added after the
  first run: a context-by-language cell is thin at order 2). A and B differ in how units follow one another beyond
  unit frequencies, without the recipe; at order 2 the size depends on the smoothing.

Both hold on the Takahashi and RF transliterations (`lines/README.md` s8.2).

## What this adds, and what is next

- Whole-word re-use in Voynich lives at the hand, section and quire levels (13-18% of draws each), five to ten
  times a real topical text's; page-level re-use is 1.5 times Pliny's and a fifth of the self-citation generator's.
- A likelihood-fitted generator of word parts, with nothing tuned on the battery, matches the best hand-tuned
  models on the held-out battery (25/30 in the best seed) and reproduces, as a faithful sample of its fit, the
  line-bound coupling, the quire drift and (in the independent-slot version) the scribe ratios and A/B drift.
- No single tree hierarchy carries the word structure and the ending convention at once; the convention is a
  context-free habit on top of a shared transition rule, which is the repository's result 2 in model form.
- The volunteers read with their own lines and pages (section 3) have the scribe-level habits (an ending habit per
  writer, own-word re-use, a context-free habit on top of a chain) and none of the line-level or book-level
  structure: no coupling between words, no line-first vocabulary, no shared stock, a chain four to six times weaker.
- (second session) The slots share a length budget; the location habit is close to context-free in held-out
  likelihood (it ties the best tree on the opener, loses 0.04-0.06 bits elsewhere, where a tree sample loses
  0.15-0.23); a generator with borrowed transition tables gets the word (up to 26/30 held out) and loses the
  convention, which does not emerge from re-use on top of fixed tables.
- (11 Nov) With the convention drawn as a normal tilt of Voynich's measured variance, the generator carries a
  quarter to a half of the A/B difference: the convention is categorical (a few endings switched on or off per
  language), not a graded preference. Copying a nearby stem at 10% matches the near-copy items (best seeds 32/37,
  26/30 held out).
- (11 Nov, v8) The convention is a few large switches (one value in twenty to fifty per level; an ending switched
  by a language changes by a factor of about 40), by the fourth moment of the log-ratios; the battery does not
  separate that from a normal tilt, and part of v7's shortfall was its exponent of 0.75. Voynich's own context-free
  convention gives three quarters of the A/B difference; separate transition tables for A and B give 0.092-0.095 of
  0.101 and 31-33 of 37 on every seed. A and B differ in the chaining rule as well as in slot frequencies.
- (11 Nov, robustness) Half of Voynich matches the other half on 35-36 of 37 items with interleaved pages, 30-33
  with alternate quires: the generators (31-33) are at the level of another set of quires, and differences of one to
  three items between variants are inside the noise of the rule. The best variant keeps its score when built from
  interleaved held-out pages. The length budget survives without the recipe but Latin has a stronger one: it is a
  property of any real vocabulary. The A/B chaining difference survives without the recipe and on three
  transliterations.
- Next: a generator that draws the chaining difference itself (switches on context-value pairs, not on values),
  and the remaining clustering beyond the page (JSD halves, the peak).

## Reproduce

All commands are run from `targets/voynich` (Python 3 with numpy; the scripts are seeded, so reruns give the same
numbers). Inputs that are git-ignored and have to be fetched first: `python fetch_corpora.py` (ZL transliteration and
comparison texts into `data/`), `python -m lang.corpora la-gutenberg` from the repository root (Latin), and Greshko's
Naibbe files into `data/external/naibbe/out/` (see `SOURCES.md`, `CREDITS.md`). Every script states its protocol in
its docstring and writes a `*_results.json` beside the `.md` table it prints.
The fits are Gibbs samplers and the slow part (minutes to an hour each on a laptop); `HPY_SWEEPS` sets the number of
sweeps (default 60). Generators need the fits of their own script and the ones named.

| section | command | writes |
|---|---|---|
| 1 | `python reinforce/hpy.py fit`; checks: `python reinforce/check_fit.py`, `python reinforce/pliny_fit.py`, `python reinforce/ablate.py` | `fit_results.json`, `fit.md`, `check_fit.json`, `pliny_fit.json`, `pliny_fit.md`, `ablate_results.json`, `ablate.md` |
| 2 | `python reinforce/slots.py all`; `python reinforce/slots2.py all ot`; `python reinforce/slots2.py all ome`; `python reinforce/slots3.py all`; `python reinforce/slots4.py all`; `python reinforce/slots5.py all` | `slots_fit.json`, `slots_gen.md`, `slots_gen_results.json`, and the same three as `slots2_ot_*`, `slots2_ome_*`, `slots3_*`, `slots4_*`, `slots5_*` |
| 3 | `python reinforce/volunteers.py all` | `gibberish_<part>.json`, `gibberish_fit.md` |
| 4.1 | `python reinforce/lengths.py` | `lengths_results.json`, `lengths.md` |
| 4.2 | `python reinforce/product.py heldout <text> <slot> [len]` for text voynich, v4, v5 and slot opener, middle, ending (with and without `len`), then `python reinforce/product.py report` | `product_heldout_<text>_<slot>[_len].json`, `product_heldout.md` |
| 4.3 | `python reinforce/slots6.py fit opener`, `fit middle`, `fit ending`; `python reinforce/slots6.py generate len5 prod6 prod6g prod6t prod6e`; `python reinforce/slots6.py report` (needs 4.2's weights) | `slots6_fit_<slot>.json`, `slots6_gen_<variant>.json`, `slots6_gen.md`, `slots6_gen_results.json` |
| 4.4 | `python reinforce/slots7.py generate tilt7_q0 tilt7_q10 tilt7_q20 notilt7_q10`; `python reinforce/slots7.py report` (needs 4.2's weights) | `slots7_gen_<variant>.json`, `slots7_gen.md`, `slots7_gen_results.json` |
| 4.6 | `python reinforce/robust.py run oddeven quires halves` (about 15 minutes a split); `python reinforce/robust.py report`; `python reinforce/recipe_free.py` | `robust_<split>.json`, `robust_results.json`, `robust.md`; `recipe_free_results.json`, `recipe_free.md` |
| 4.5 | `python reinforce/slots8.py generate norm8 cat8 emp8 cat8p emp8p lang8`; `python reinforce/slots8.py report` (about 2 minutes a variant; the report also reads 4.3's prod6e and 4.4's tilt7_q10 files) | `slots8_gen_<variant>.json`, `slots8_gen.md`, `slots8_gen_results.json` |

The battery and its match rule are `b3_bakeoff.py` (`battery`, `score`); the held-out items are those outside
`hybrid_model.TUNED_B3` (`research/voynich_siblings/`); scribe ratios and drift are `hpy.scribe_ratios`, `hpy.drift`;
the reference rows (Voynich, autocopist) are cached in `reinforce/reference_battery.json`. Run logs of this session's
runs are in `reinforce/logs/`.

## Files

`hpy.py` (model, fit, whole-word generator and scoring; `fit.md`, `fit_results.json`, `reference_battery.json`),
`check_fit.py` (`check_fit.json`), `ablate.py` (`ablate.md`), `pliny_fit.py` (`pliny_fit.md`), `slots.py`
(`slots_fit.json`, `slots_gen.md`), `slots2.py` (`slots2_ot_*`, `slots2_ome_*`), `slots3.py` (`slots3_*`), `slots4.py` (`slots4_*`), `slots5.py` (`slots5_*`).
Second session: `lengths.py` (`lengths.md`, `lengths_results.json`), `product.py` (`product_heldout.md`,
`product_heldout_<text>_<slot>[_len].json`), `slots6.py` (`slots6_fit_<slot>.json`, `slots6_gen_<variant>.json`,
`slots6_gen.md`, `slots6_gen_results.json`), `slots7.py` (`slots7_gen_<variant>.json`, `slots7_gen.md`), `slots8.py` (`slots8_gen_<variant>.json`, `slots8_gen.md`, `slots8_gen_results.json`); run logs in `logs/`.
`volunteers.py` (the volunteers with their own lines and pages: loader, line tests, whole-word and slot fits on both
corpora with the neutral split; `gibberish_fit.md`, `gibberish_lines.json`, `gibberish_writers.json`, `gibberish_reuse.json`,
`gibberish_habit.json`, `gibberish_slots_gib.json`, `gibberish_slots_voy.json`).
The restaurant bookkeeping in `hpy.py` keeps tables as size classes (rewritten during the session after the first
version went quadratic on frequent values at discounts near 1; the parameter-recovery test gives the same values).
Whole-word generation from the fitted model (`hpy.py generate`) was not run: the fit itself showed the whole word is
the wrong unit.
