# Voynich siblings: archival search for comparable 15th-century cipher books and sign systems

Status: in progress

Session of 27 Oct 2026. Question: is there anything in archives or the literature that is *like* the Voynich
manuscript (Beinecke MS 408, vellum 1404-1438), close enough in date, region, genre or glyph shapes to test the two
live hypotheses in `targets/voynich/NOTES.md` section 1: (a) a verbose / slot cipher, (b) structured meaningless text?
A second text in Voynichese is not expected (none is known after a century of search); the realistic finds are
period books in invented alphabets, and period ciphers using Voynich-shaped signs or verbose sign pairs.

## 0. Results so far (27-28 Oct 2026), with files

| Result | File |
|---|---|
| Karlsruhe 399 f. 229r (Bischoff 16c, "ungelesen" since 1954) read: Ps. 50:3 *Miserere mei deus ...* in a reciprocal letter-pair cipher, 39 of 46 letters on the key | `bischoff_unread/karlsruhe399.md` |
| Voynich word openings and endings are 3-7x more independent than Latin/German/English; self-citation, grille and Naibbe match, whole-word verbose ciphers (fixed or homophonic) do not | `slot_independence.md` |
| Slot-HMM (hidden state per word emitting prefix, gallows, middle, ending): the state chain's apparent letter-like dependence (0.54 bits, Latin letters 0.54) is about 60% line position and section; order-specific gain 0.06 bits/token against 0.47 for a one-letter-per-word slot cipher (which the model recovers at 99%), about that of a 1-2 letter unit cipher (0.045); ending predicts next ending (0.03) | `slot_hmm.md` |
| Fontana's *Secretum* (c. 1430) letter wheels as a dated slot device; Fontana's *Secretum* also a whole book in cipher by a physician, which corrects the "scale has no parallel" claim | `slot_independence.md`, `physicians_ciphers.md` |
| Parse defect fixed (`targets/voynich/parse_ivtff.py --fixed`), Voynich-side statistics re-run: every predicted correction reproduced; new: Currier A is under-dispersed too (dispersion 0.99 -> 0.74) | `targets/voynich/results/d1_parsefix.md`, `targets/voynich/NOTES.md` section 0 |
| Zolner's sign-family script (Clm 644 ff. 51v-52r), a designed alphabet whose circle family gives o, ∂, ɑ, 9; never used for text | `zolner_clm644.md` |
| Table of 22 physicians' and alchemists' book ciphers 1370-1470: the genre hides small units with simple systems; Voynich fits its subject, not its method | `physicians_ciphers.md` |
| Labels: no taxonomic prefix clustering (power: 30% detected at z 5.7); labels not enriched in their own page's text (z 0.6) while paragraph words are (z 6.3) | `label_prefix_test.md`, `label_page_test.md` |
| Numeral-mixed secret alphabets (Bischoff C: 4, o, 8, 9 as letters) in Venice, Prague, Franconia, Bavaria; Cpg 597 f. 7r box drafted (key B) | `bischoff_shapes.md`, `targets/heidelberg597/texts/f7r_box_draft.md` |
| Negative or blocked: CCCC 96 (key families exhausted; pastedown not imaged), Lambeth 477 (text not online), DECODE dump (login), Parker/MDZ/manuscripta viewers (refuse scripts) | `bischoff_unread/README.md`, section "Checked" below |

Step 1 (literature) done in outline; step 2 (DECODE/Gallica query) only from material already in this repository:
a fresh DECODE list dump was not made this session (the API needs a login token; `catalogue_harvest/decode/dump_list.py`
expects `targets/bordeaux/decode/cookie.txt`).

## 1. What the literature already covers

- **Dunin & Schmeh 2022**, "The Voynich Manuscript Compared with Other Encrypted Books", Voynich conference Malta,
  CEUR-WS vol. 3313 paper 15 (https://ceur-ws.org/Vol-3313/paper15.pdf). 118 encrypted *books* (Schmeh's list,
  https://scienceblogs.de/klausis-krypto-kolumne/klaus-schmehs-list-of-encrypted-books/). Only six are 15th century:
  Voynich; Fontana's *Bellicorum instrumentorum liber* (BSB Cod. icon. 242, c. 1420) and two more Fontana books;
  "Codex Palatinus Germanicus" (= Heidelberg Cod. Pal. germ. 597, 1426, Schmeh no. 00044); Trithemius's
  *Steganographia*. Fontana and Cpg 597 are named as the closest visually. Only 15 of 118 are unbroken, and Voynich
  is the only pre-1900 one. Their conclusion asks for more 15th/16th-century comparison works: this search is that.
  Purpose classification: knowledge book or hoax; letters, slips and short runs are out of their scope.
- **Zandbergen 2019**, "No News about the Voynich Manuscript?" (https://www.voynich.nu/papers/NoNews_RZ_2019.pdf),
  fig. 5: Voynich text against known early-15th-c. cipher texts and unknown scripts; the visual difference is
  clear, and Voynichese has far fewer valid character combinations. His comment on Cipher Mysteries (Jan 2018):
  Bischoff's census manuscripts all hold *simple* ciphers; some use invented alphabets; the shape overlap with
  diplomatic ciphers is "not great".
- **Bischoff 1954**, "Übersicht über die nichtdiplomatischen Geheimschriften des Mittelalters" (MIÖG 62): the
  standard census of medieval non-diplomatic secret scripts (Cpg 597 is his nos. 70-71). Not yet read here.
- **Stephan Müller (Vienna)**, *Handbuch der deutschen Glossen und Texte des Mittelalters in Geheimschrift
  (8.-15. Jh.)*, DFG project finished, due De Gruyter 2027: over 100 texts plus about 150 gloss witnesses. The
  Augsburg Glossenwiki names Voynich as the only undeciphered item. Lead: Müller et al., "Vame rumbsa mepesor. Zu
  einer bislang nicht bekannten Geheimschrift des Mittelalters" (FS Hellmuth 2015, pp. 143-150), not yet read.
- **Pelling** (*The Curse of the Voynich*, 2006; Cipher Mysteries 2010, 2025): the "4o" pair as a verbose cipher
  token in North Italian / Milanese ciphers, said to occur from 1424 and 1435 and 1440-56; gallows as selectors.
  He dates the MS to c. 1450 Milan from that, against the 1404-1438 vellum.
- Repository sweeps that already closed the 15th-c. field for *text ciphers* (`research/oldest/`): Kyeser
  *Bellifortis* (reversed words, read), Fontana (read by W. Meyer; transliteration Cod. icon. 242a), Rudolf IV's
  alphabet, Friedrich III's notebook, Bohemian, Hanseatic, Baltic, Swedish, Polish editions: nothing undeciphered
  before 1450 except Voynich. `CANDIDATES.md` set Voynich aside as "not a text cipher of this kind".

## 2. What this repository already holds that bears on it

- **Cpg 597 is a target here** (`targets/heidelberg597/`): three sign alphabets keyed and checked. It is the nearest
  book in date (1426), region (Passau, East Bavaria; the Voynich marginalia are German) and genre (alchemy and
  medicine with a cisioianus and calendar). All three are simple substitutions (Wattenbach 1869: "wie alle einfache
  Chiffren, leicht zu enträthseln"). **Gap:** the recipe cipher (ff. 7r-22r, 46r-v, 54r-61r) was never
  transcribed, so the book is missing from the `targets/voynich/data/period/` control set and `c3_period.py`.
- **"4o" in dated ciphers held here.** `targets/florence1429/` (early 1425): 4o is a *nomenclator* sign for
  "Carlo" [Malatesta], standing alone and also a homophone for Q. That is a dated instance of the shape before
  1438, but as a code word, not as a verbose letter pair. `targets/kaa4591/` (Bavaria, 1580s): 4o = "und"/"et"
  or "Ro", far too late. `riksarkivet1628`: 4o as a scribal variant of 40.
- **c3 (period ciphers, 17 datasets, 18,604 signs, 1400-1490)**: every one sits 0.85-2.2 bits above Voynichese
  on h2. The nearest structural features are the Siena undated sheets with superscripted *f o^n* units
  (siena1421_no20_23, 4,931 signs, unread, now read by Lasry and others for nos. 20 and 23) and the syllable signs
  in Mantua R1854 and Buda 1489. None is verbose in the Voynich sense (fixed 2-3 sign groups per letter).

## 2a. Bischoff 1954, read in full

B. Bischoff, "Übersicht über die nichtdiplomatischen Geheimschriften des Mittelalters", MIÖG 62 (1954) 1-27, free
scan at https://www.mgh-bibliothek.de/dokumente/b/b023446.pdf (MGH library; image PDF, no text layer). Numbered
census (nos. 1-162, gaps left for additions) of book (not chancery) secret scripts, 8th-15th c., with a sign table
on pp. 24-25 for nos. 38-127. Footnote 5 excludes "die rätselhafte geheimwissenschaftliche Voynich-Hs." on purpose
(then dated after the Middle Ages, after Manly), so his census was never read *as a Voynich comparator*. Almost
everything in it is a simple system (vowel substitution, letter shift, foreign alphabets, sign alphabets). Items
of the 14th-15th c. that he marks unread (**ungelesen / ungedeutet**) or that bear on the Voynich setting:

| No. | Manuscript | Date | What Bischoff says | Why it matters here |
|---|---|---|---|---|
| 16c | Karlsruhe, Karlsr. 399, fol. 229r | 15th c. | "Ne(?)figgii nie tiof fiqomthm nhrmhn nifigiqugtehm dohn", **ungelesen** | unread letter cipher, short |
| 19b | London, Lambeth Palace 477, fols. 120v, 142v (additions) | 15th c. | "Cmapmabmd mafmb madmafx ⊛⊛⊛ mafx ... ymbns farte xmbfmd", **ungelesen** | repetitive *maf-/mab-/mad-* units with inserted letters: verbose-looking; transcribe and test |
| 137 | Cambridge, Corpus Christi College 96, fol. 240r | c. 1425 | "p³p³lap³edff.p⁴.g.gggharazy p³ar.", **ungedeutet**, in a mixed p-stroke system | exactly the Voynich date window; Parker Library is fully imaged |
| 69 | Prague, Metropolitan Chapter Library O. LXXVIII (1662), fol. 295v | 15th c. | Czech ownership note ("[t]yto knizky slozil gest geden kniez gnemem ...") with eight signs like schematic memory-alphabet drawings | Bohemia, signs of the memorial-alphabet kind |
| 45, 107 | Prague, Metrop. M. CXXV, fol. 1 | 15th c. | secret alphabet in "geschwungenen Zügen" headed "Grecum alpha", digits for vowels | Prague |
| 104 | Prague, Metrop. M. XVII (1370), fols. 1r-10r | 14th c. | cipher in chemical recipes, incomplete key inside the cover | Prague, alchemy; key incomplete |
| 73 | Munich, Clm 644 (Heinrich Zolner), fols. 51v-52r | 15th c. | self-invented script: five vowel shapes (point, line, triangle up, circle, triangle down), consonants built *onto* the vowel sign up to the next vowel | a syllabic invented script: the nearest thing in the census to Voynich's glyph-group structure |
| 106 | Wolfenbüttel 55.7 Aug. 4°, flyleaf | 15th c. | alchemical, digits for vowels | alchemy |
| 74 | Göttingen, Morbio 15 | entry 1484 | cipher note among astronomical entries, only partly read | |
| 75 | Vatican, Borghes. 239, fol. 16r | late medieval | 22-sign alphabet, assignment of signs uncertain | |
| 62 | Rudolf IV's alphabet in at least ten 15th-c. MSS (Clm 671, 5173, 14684, 641, 3131, 405; Munich UB 4° 810; Leipzig 1048 of 1444; Prague Metrop. A LIX 6) | 15th c. | labelled "chaldaic", "arabic", "de India maiori"; used in recipes ("fliegen", "hasen") | a known invented alphabet in South-German / Bohemian recipe books of the Voynich decades |
| fn. 24 | Johannes Hartlieb, *28 Häuser des Mondes*, 1456 (once Gilhofer & Ranschburg, Vienna, cat. 265 no. 7), fols. 22r-24r | 1456 | a collection of alphabets; "eine Untersuchung der Hs. wäre erwünscht" | Bavarian court physician, magic and herbs; present location to trace |
| p. 23 | Weimar O. 111, fols. 46v-47 | 15th c. | alphabets "Caldeorum, Sirorum, Arabicorum, Philistinorum, Turcorum, Sarracenorum", part of a lost set of 18 (Greater and Lesser India, Persian, Russian, "Litawer Lande") | invented "exotic" alphabets; compare shapes with EVA |

Lesson: Bischoff's census is the right shape-comparison corpus for EVA, and it has never been compared with it
sign by sign (as far as found). His p. 24-25 table could be digitised and set against the EVA glyph inventory.

## 2b. Foreign-language and catalogue searches (dead ends, with one precedent)

- Web searches in Czech, Polish, Hungarian and Italian for undeciphered 15th-c. manuscripts in an unknown script:
  every result is about Voynich itself. General web search cannot find catalogue-level items; the catalogues must
  be searched directly.
- Handschriftenportal (German union catalogue): JavaScript search page, not readable by fetch; a site-restricted
  web search for "Geheimschrift 15. Jh." returned only unrelated 15th-c. records. manuscripta.at (Austria) has a
  "Geheimschrift" checkbox in its detailed search but returns 403 to fetch; one hit by web search: Klagenfurt,
  Geschichtsverein 5/42, a parchment roll "mit Geheimzeichen und -sprüchen" (Latin/German), not checked.
  e-codices: only early-medieval bfk glosses (St. Gallen); St. Gallen Cod. Sang. 278 p. 514 has a verse in secret
  script, not checked.
- Handschriftencensus cites Bischoff 1954 by item number in its descriptions (Cpg 597 = nos. 70-71; Vienna 2674 =
  no. 12c), so a census-wide search for "Bischoff" + "Geheimschriften" would list every German-language item.
- **Precedent (Rohonc).** Láng, Bobory, Király, Tokai, *Cryptologia* 2026, doi 10.1080/01611194.2026.2711207
  (reported by Múlt-kor, 15 Oct 2026): four pages in the Rohonc Codex's script, enclosed with a 1571 letter of
  Farkas Porhócs, steward of Toronya, to Boldizsár Batthyány, Hungarian National Archives. Found by Béla Hanák
  during routine digitisation of 16th-century correspondence, not by a search; a key applied to them gives Luke.
  So a sibling of a famous undeciphered book did turn up, as loose sheets in the letters of the people around it.

## 2c. Is Voynich "too elaborate to be a one-off"? Survival and precedent

**Survival (L).** Neddermeyer: about 1 in 15 (7%) of 14th-15th-c. manuscripts survive, about 20% for high-end codices
(Holy Roman Empire). Buringh 2011: loss 25-40% per century, about 32% per century in the 14th-15th. Kestemont et al.,
*Science* 2022 (unseen-species model, medieval vernacular literature): about 9% of copies survive, but about 68% of
*works* survive in at least one copy. Arithmetic*: with independent survival p = 0.1-0.2, a group of N books in one
system leaves one or no survivors with probability 0.39 (N = 20, p = 0.1) or 0.74 (N = 10, p = 0.1) or 0.38
(N = 10, p = 0.2). So a handful of lost siblings is unremarkable; dozens of books with only one survivor is not likely.
Kestemont's works-survive-better point cuts the other way: if the *system* had circulated (taught, copied,
keyed), traces such as key sheets or alphabet trials would be expected somewhere. None is known: the erased
alphabet columns on f1r (multispectral images, published 2024) are a later owner's decoding attempt, matched to
Marci's hand (owner 1662-65; Art Newspaper, 25 Sept 2024), not a period key.

**Precedents of the idea (L).** An invented script, or an invented language with its own alphabet, was not new in
the Voynich decades: Hildegard of Bingen's *lingua ignota* with *litterae ignotae* (1150s; 1,011 coined words, two
MSS c. 1200, Wiesbaden "Riesencodex" and Berlin); Hrabanus's *De inventione linguarum* alphabets (Bischoff no. 11a
ff.); the *Ars notoria* notae (13th-15th c., N. Italy); Rudolf IV's alphabet reused in ten South-German and
Bohemian recipe MSS (Bischoff no. 62); Fontana's sign alphabet (c. 1420); Zolner's syllabic invented script
(Clm 644, Bischoff no. 73); Cpg 597's three alphabets (1426). What has no parallel is the combination (a whole illustrated book, unread, by several scribes) and the
statistics (low h2, slot grammar). Correction, 27 Oct: Fontana's *Secretum* (Bischoff no. 67, BnF n.a.l. 635) is a
whole book in cipher by a physician c. 1430, so scale alone is not unparalleled; see `physicians_ciphers.md`; every precedent above is a simple substitution or a
word list, and none is Voynich-like at the text level. D'Imperio 1978 (NSA, DTIC ADA070618) has the older survey of
this background ("Artificial and secret languages", Ars notoria, Picatrix), not re-read here.

## 3. Leads, ranked

1. **Transcribe the Cpg 597 recipe cipher** from the public-domain images (digi.ub.uni-heidelberg.de/diglit/cpg597)
   and add it as a c3 dataset. Expected result: monoalphabetic German, h2 near German, i.e. not Voynich-like. It is
   still the one contemporary knowledge book in an invented alphabet with a known plaintext language, the closest
   control the field has, and nobody has scored it.
2. **A 4o / verbose-pair census** over dated key collections: Tranchedini's keys (ÖNB Cod. 2398, 1450-1474, in
   DECODE), the Mantua R1854 keys, the Florence 1429 key, Cicco Simonetta's *Regule* material. Question: is there
   any key before 1440 where *one plaintext letter* is a fixed two-sign group? That is the testable form of
   Pelling's claim and of hypothesis (a). The 1424 and 1435 instances he cites need their shelfmarks.
3. **Müller's handbook and Bischoff 1954**: ask for any German Geheimschrift item of 1400-1450 left unresolved or
   using an invented alphabet with ligatured or gallows-like signs. The "Vame rumbsa mepesor" paper first.
4. **DECODE query** (needs a login token): records 1380-1470, symbol set "graphic signs" or "mixed", any status,
   including keys, for sign shapes matching EVA k t p f, 4o, 8, 9 (-us/con) and ch/sh.
5. **Bischoff's unread 15th-c. items** (section 2a): CCCC 96 f. 240r (c. 1425, imaged on Parker on the Web) and
   Lambeth 477 ff. 120v, 142v first; then Karlsruhe 399 f. 229r. Small, but the only unread book ciphers of the
   Voynich decades named in the census.
6. **The Rohonc route for Voynich**: loose sheets in the correspondence of its known owners and handlers (Baresch,
   Marci, Kircher, Tepenec, Rudolf II's court, Kinner). The Kircher letters (APUG) were searched by Voynich
   researchers when Baresch's 1639 letter was found; Baresch's 1637 sample copy for Kircher is lost. Prague
   archives of the 17th-c. owners and the Rudolfine court records are the places a stray sample could sit.
7. **Zolner (Clm 644)**: done, see `zolner_clm644.md`. **Shape census**: Bischoff's sign table (pp. 24-25) and Zolner's syllabic script (Clm 644) against the EVA
   glyph inventory.
8. **Fontana's other two books** (Dunin & Schmeh): identify the shelfmarks (one is BSB Cod. icon. 242's sibling
   *Liber instrumentorum iconographicus*, "not available online" per Schmeh) and check whether Meyer's key covers
   them all.

## Checked this session (27 Oct 2026), including dead ends

| # | What | Where | Result |
|---|---|---|---|
| 1 | Repository: Voynich target, its period control set and the README rows | `targets/voynich/NOTES.md`, `data/period/README.md` | Statistics only, no archival sibling search; parse defect (section 0) still in `parse_ivtff.py` l. 26 |
| 2 | Repository: oldest-cipher sweep and its regional scans | `research/oldest/CANDIDATES.md`, `scan_2026-09-23/*.md` | Voynich set aside as "not a text cipher of this kind"; nothing undeciphered before 1450 found in German, Bohemian, Hanseatic, Baltic, Swedish or Polish editions |
| 3 | Repository: grep for Fontana, Borg.lat.898, Silencium Dei, Adelsbach, Kassel, Pal. germ., Kyeser, Hartlieb | all `*.md` | Only Cpg 597 (target), Fontana and Kyeser (scan notes, both read) |
| 4 | Repository: grep for "4o", verbose, Tranchedini, Cod. 2398 | `targets/`, `research/` | 4o in florence1429 (1425, code for Carlo), kaa4591 (1580s), riksarkivet1628 (numeral variant), rome1536; no verbose letter pair before 1440 |
| 5 | Repository: DECODE harvest | `research/catalogue_harvest/decode/` | Only 920 records not already referenced in the repo; the full list dump is not committed. A fresh dump was not made (needs login token) |
| 6 | Web: comparable manuscripts, invented scripts, alchemical herbals | general search | Only secondary press (archaeologymag 2026, Art Newspaper 2025); no named sibling |
| 7 | Web: Fontana / Cod. icon. 242 against Voynich | general search | voynich.ninja thread-2714; viridisgreen "computational palaeography" (Fontana's script closest to the Voynich *marginalia*, but its diagonality sets it apart); Bax blog; two 2026 Zenodo working papers self-described as unvalidated (not used) |
| 8 | Dunin & Schmeh 2022, full text | CEUR-WS 3313 paper 15 | Read in full; section 1 |
| 9 | Schmeh's list of encrypted books | scienceblogs.de | Entries 00001-00117 read (page truncated after); pre-1600: Voynich, Rohonc, Codex Igo, Subtlety of Witches, Fontana x2, Humphrey, Cpg 597, Soyga. Borg.lat.898 is 17th c., Adelsbach undated, Silencium Dei 1798, Kassel Zauberhandschrift 18th c.: none comparable |
| 10 | Web: voynich.ninja / gallows parallels in other manuscripts | general search | No sibling reported; closest: a urine symbol in D'Imperio 1978 p. 122 like one gallows (Cipher Mysteries comment) |
| 11 | voynich.nu comparison page | `voynich.nu/extra/sp_comp.html` | 404 (guessed URL) |
| 12 | Web: Zandbergen on comparisons | search | NoNews 2019 paper; his 2018 comment on Bischoff's census |
| 13 | Web: Müller's Geheimschrift handbook | univie.ac.at, Glossenwiki | Census due 2027; "Vame rumbsa mepesor" 2015 as a lead |
| 14 | Web: Pelling verbose / 4o / Averlino | ciphermysteries.com | Claims summarised in section 1; his 1424 and 1435 instances are second-hand (a commenter), no shelfmarks |
| 15 | Bischoff 1954, full scan | mgh-bibliothek.de b023446.pdf | Read in full (pp. 1-27); section 2a |
| 16 | Web, German catalogue terms ("in Geheimschrift", "unbekannte Schrift", Kräuterbuch, Alchemie) | general search | KdiH alchemy list, Trier Hs. 1025/1944, GNM 3227a: no secret script mentioned |
| 17 | Web, Italian ("alfabeto segreto", "scrittura cifrata", ricettario, erbario) | general search | Voynich only |
| 18 | Web, English ("undeciphered", "unknown script", herbal, alchemical) | general search | Voynich only; Zandbergen quoted: no other document in the script is known |
| 19 | Web, voynich.ninja / new finds 2024-2026 | general search | none reported |
| 20 | Handschriftenportal direct search | handschriftenportal.de/search?q=Geheimschrift | JS page, unreadable by fetch; site search gave unrelated records |
| 21 | manuscripta.at | hs_suche.php | 403; site search found Klagenfurt GV 5/42 (roll of secret signs) |
| 22 | e-codices | site search | bfk glosses (St. Gallen, 10th-11th c.); Cod. Sang. 278 p. 514 |
| 23 | Web, Bischoff list citations | search | Handschriftencensus 10300 (Cpg 597), 11086 (Vienna 2674) cite him by number; led to the MGH scan |
| 24 | Web, Czech ("rukopis 15. století neznámé písmo šifra", Prague chapter library) | general search | Voynich only |
| 25 | Web, Polish ("rękopis XV wiek nieznane pismo szyfr") | general search | Voynich only |
| 26 | Web, Hungarian ("titkosírás kódex 15. század ismeretlen írás") | general search | Rohonc 2026 find (section 2b); kripto.blog.hu "ten most mysterious coded books" behind a login redirect, not read |
| 27 | Web, CCCC 96 f. 240 and Lambeth 477 cipher strings | search | no later reading found; M. R. James's catalogues (archive.org) and Parker on the Web are the next step |
| 28 | Múlt-kor report on the Rohonc sheets | mult-kor.hu, 15 Oct 2026 | Confirmed details and DOI; the Cryptologia paper itself not read |
| 29 | Cpg 597 PDF from UB Heidelberg (downloaded by the user in a browser) | local, not committed | 86 pages, embedded images 583 x 845 px: enough to locate cipher (f. 7r boxed four-line block wholly in cipher; f. 9r cipher words in clear recipes), too small to transcribe invented signs reliably. A higher-resolution copy is needed |
| 30 | IIIF image API for Cpg 597 page images | digi.ub.uni-heidelberg.de/iiif/2/... | 403 without a browser identity (manifest itself fetches); not pursued |
| 31 | M. R. James, *Descriptive catalogue ... Corpus Christi College* vol. 1 (1912), OCR | archive.org descriptivecatal01corprich | **CCCC 96** = "Chronicon dictum Joh. Brompton", c. 1425 (Liebermann), Jervaulx Abbey ("Liber monasterii Joreuallis ex procuracione domini Johannis Bromton abbatis"); f. 240 is stuck to the cover, with scribbles: two Latin proverbs, "Jeruax" twice, the cipher, an English couplet, names R. Gloucestr., Henry ffytzhugh. James reads the cipher "ipolapedff. o.g.gg gharazy p ar", Bischoff "p³p³lap³edff.p⁴.g.gggharazy p³ar." |
| 32 | Brute force on CCCC 96: p-stroke count as vowel (a-u or u-a) + Caesar shift 0-25 on the rest | `ccc96.py` (scratch) | no reading; the two transcriptions disagree, so the image is needed first |
| 33 | Parker on the Web catalogue search; MDZ search for Clm 644 | parker.stanford.edu, digitale-sammlungen.de | both reject automated requests; images to be fetched by hand |
| 34 | Web: Lambeth 477, Karlsruhe 399, Clm 644 digitisation | search | Lambeth 477 described by James & Jenkins 1930-32 (vol. 2), Biblissima lists it; Karlsruhe 399 not found online; Clm 644 should be in Halm's catalogue and MDZ |
| 35 | Web: invented languages before 1500; ars notoria and magical characters | search | section 2c |
| 36 | Web: manuscript survival rates | search | section 2c |
| 37 | Clm 644 (Zolner), MDZ PDF of the BSB microfilm, downloaded by the user | 745 images, local | ff. 51v-52r = PDF 109-110: the script tables, transcribed in `zolner_clm644.md`; Schedel's *Vita* of Zolner (PDF 8-13); all 745 pages scanned as contact sheets, no other page in the script |
| 38 | Cpg 597, second PDF from UB Heidelberg (user) | local, 1219 x 1766 px | about twice the first; usable for transcription |
| 39 | CCCC 96 on Parker on the Web (user, by hand) | viewer | foliation ends at 239; the f. 240 pastedown with the cipher is not among the images, or shows blank. Rebinding after James 1912 is possible; open |

## Not done

No archive images viewed; no DECODE query; Müller 2015 not read; Bischoff read (section 2a); Pelling's 1424/1435 instances
not traced to shelfmarks. Every claim in section 1 is from the cited pages as fetched on 27 Oct 2026.
