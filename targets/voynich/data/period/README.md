# Period ciphers, 14th-15th century: a control set for the Voynich statistics

Genuine ciphertexts of c. 1400-1490 taken from this repository's own targets, to test whether any real cipher system of the period gives Voynich-like character statistics (in particular a very low conditional entropy h2). One JSON per cipher system. Built by `_extract.py` (deterministic; reads only the target folders; rerun with `PYTHONUTF8=1 python targets/voynich/data/period/_extract.py`, which also rewrites this file).

## Format

Each JSON has `dataset`, `target`, `piece`, `date`, `year` (null if undated), `date_basis`, `shelfmark`, `system`, `language`, `outcome`, `sign_inventory_note`, `counts`, `plaintext`, `plaintext_source`, `source_files`, `caveats`, `line_ids` and `lines`.

- `lines`: list of lines, each a list of sign tokens in reading order, in the target's own sign ids.
- `|` = a separator the scribe wrote (word points, dot groups, //); `N:x` = nomenclator/code sign (a name or a whole word, including et-signs); `0:x` = null by the key. Strip the prefixes to get the raw sign stream.
- Clear text is left out; a cipher run between clear words is its own line. An illegible, lost or struck sign ends the line (the rest is a new line with a suffixed id), so no false sign pair crosses a gap. A sign the transcriber marked doubtful is kept.
- `plaintext`: the reading of those passages, lowercase a-z and spaces; unread signs, editorial insertions, code expansions and clear words left out; null if there is no reading.
- `counts`: computed by the script: `sign_tokens` (all tokens except `|`), `distinct_signs` (prefixes stripped), letter/code/null tokens and distinct types, `dividers`, `lines`, `plaintext_letters`, and the number of doubtful signs kept and illegible signs dropped.

## Extracted

| dataset | date | system | sign tokens | distinct signs (letter / code / null) | dividers | plaintext | main caveat |
|---|---|---|---:|---|---:|---|---|
| benedict1399 | 22 June 1400 | simple substitution, one sign per letter (c=i, u=v); name sign; null separator groups; Latin | 788 | 21 (19 / 1 / 1) | 0 | yes | RECONSTRUCTED from Puig's text + rebuilt key (only image is a 1920 halftone), not transcribed |
| siena1421_no14 | undated, c. 1409-1429 (Carlo Malatesta alive) | substitution with a few homophones; word points; person codes; Italian | 1453 | 49 (46 / 10 / 0) | 239 | partial | date c. 1409-29 from content only; 59% of tokens read as sense |
| florence1429 | early 1425 (1424 Florentine style) | homophonic + 17 nulls + nomenclator; short runs in clear Italian | 99 | 50 (39 / 7 / 5) | 0 | yes | 99 signs: too short alone |
| r1854_p1 | 22 Apr 1428 | unknown; letter-like signs in 3 runs with separator marks; in clear Latin | 261 | 28 (28 / 0 / 0) | 56 | no | 262 signs; unread |
| r1854_p2 | 9 Aug 1428 | homophonic + 13 null signs + syllable signs (con, rum) + et-sign + 2 codes; Latin | 1802 | 53 (37 / 3 / 13) | 13 | yes | - |
| r1854_p3 | 6 Nov 1428 | homophonic + 10 null signs + 3 name codes; runs in clear Italian | 893 | 55 (42 / 3 / 10) | 2 | yes | runs short, glossed at the time |
| r1854_p4p5 | 13 and 21 Feb 1430 | homophonic (up to 4 signs per letter) + 3 et-signs + syllable signs; Latin | 1736 | 47 (44 / 3 / 0) | 0 | yes | - |
| maria1435 | 5 Aug 1435 | unknown; 3 short runs in a Catalan register copy | 42 | 21 (21 / 0 / 0) | 0 | no | 42 signs: far too short |
| it1583_f68 | 4 May 1446 | Sforza family: homophonic with syllable/word signs (probable); dot separators | 404 | 26 (26 / 0 / 0) | 23 | no | unread; draft from a binarized scan |
| it1583_f70 | 4 May 1446 | same family as f. 68, other hand | 390 | 31 (31 / 0 / 0) | 6 | no | unread; sign ids not comparable with f. 68 |
| siena1421_no07 | c. 1454 (undated) | mixed digits/letters/signs, homophonic-looking; runs in clear | 363 | 45 (45 / 0 / 0) | 0 | no | unread; date from context |
| siena1421_no04 | 12 May 1456 | letter substitution in 15 runs + Latin code words | 153 | 52 (45 / 7 / 0) | 5 | partial | 153 signs: too short |
| siena1421_no11 | 13 June 1478 | Florentine cipher, 44 sign types, no word division | 409 | 44 (44 / 0 / 0) | 0 | no | unread |
| buda1489 | 12 Jan 1490 and 2 Apr 1490 | homophonic + syllable signs (letter+superscript) + nulls + nomenclator; Italian | 690 | 75 (69 / 2 / 4) | 0 | yes | R1098 is a noisy first-pass transcription |
| siena1421_no06_24 | undated; 15th-century hand (no. 6) | unidentified, ~70 types incl. crossed variants; not plain homophonic | 3694 | 73 (73 / 0 / 0) | 0 | no | date from hand only; unread; two transcribers |
| siena1421_no20_23 | undated | unidentified, superscripted signs, 'f o^n' units; not plain homophonic | 4931 | 86 (86 / 0 / 0) | 0 | no | UNDATED (fascicle 1421-1547); unread |
| siena1421_no25 | undated | simple substitution, one sign per letter; word points; Italian | 496 | 21 (20 / 1 / 0) | 54 | yes | UNDATED (fascicle 1421-1547) |

Total: 17 datasets, 18604 sign tokens.

## Which to use

- Long enough for h2 on their own (700+ signs): benedict1399 (788), siena1421_no14 (1453), r1854_p2 (1802), r1854_p3 (893), r1854_p4p5 (1736), siena1421_no06_24 (3694), siena1421_no20_23 (4931).
- Securely dated 1400-1490 among those: r1854_p2 (1428), r1854_p4p5 (1430), r1854_p3 (1428), siena1421_no14 (c. 1409-29, by content), benedict1399 (1400, reconstructed, so its h2 is that of Latin with c=i and u=v merged).
- The two largest, siena1421_no06_24 (15th-century hand) and siena1421_no20_23 (undated), are unread systems that are not plain homophonic substitution; they are the most interesting controls and the least certain in date and sign inventory.
- Everything under 500 signs (florence1429, maria1435, siena1421_no04, r1854_p1, siena1421_no07, siena1421_no11, it1583_f68, it1583_f70, siena1421_no25) is too short for a stable h2 on its own; use it pooled or as a sanity check only.

## Looked at and skipped

| target | date | reason |
|---|---|---|
| florence1414 | 1414 | No ciphertext reachable: the letters are not online (ASF Signori, Responsive); only Gabbrielli's partial key (KEY.md). |
| medici1425 | 1425 | Ciphertext not online (ASF Dieci di Balìa, Responsive, Oct 1425); nothing transcribed. |
| heidelberg597 | 1426 | Read by Wattenbach 1869; only the alphabets were recovered here, the running cipher of the recipes has never been transcribed. |
| matthias1482 | 1482 | About 330 signs of homophonic cipher, read against Fraknói's print, but no sign-by-sign transcription is kept (only the reading and a key table); homophones rule out rebuilding the signs from the text. |
| sadoleto1482 | 1482 | Readings, alignments and a working key only; no sign-level token file (seg/ holds unlabelled glyph boxes); homophonic, so not rebuildable from the text. |
| beatrice1482 | 1482-86 | Deciphered in print 1877-78 (MDE III-IV); no transcription in the folder. |
| esp318 | 1497-1504 | No. 5 (1497) was printed by Parisi 2020 but not transcribed here; no. 95 (1497) exists only as machine-clustered letter decodes without sign ids; no. 92 (Aug 1500) and nos. 93-94 (1503-04) are the Catholic Monarchs' CVC-code family of 1500 and later. |
| research/oldest (ACA Reserva 12) | 1413-16 | A columnar transposition of clear Catalan (Salas 1931), not a sign cipher; no transcription under targets/. |
| siena1421, other pieces | 1421-1547 | No. 1 (1421) and nos. 2, 26-28 not photographed; nos. 9, 19, 21 and R4794 too short (46-170 signs) and undated; nos. 8, 10, 12 read at the time or marked decrypted on DECODE, no transcription here; nos. 13/16, 15, 17, 18 are 16th century; no. 22 clear drafts with number codes; no. 29 a scrap; the no. 24 dorse run-over (about 640 signs) is not in a token file. |
| buda1489, other pieces | 1489-92 | Vestigia 2831 (22 Nov 1489, about 2,000 signs) has sign notes only in prose reading files, no token file; R1146, R1147, R1158 (1491-92) are other systems and not transcribed. |
| florence1429 siblings | 1424-25 | R3755-R3757: about 270 signs of glossed runs, only as a markdown table (TRANSCRIPTION.md); left out. |

