# Microsoft Typography — Segoe UI font family (+ Consolas cross-check)
- URL: https://learn.microsoft.com/en-us/typography/font-list/segoe-ui
- Publisher: Microsoft Learn — official font documentation
- Tier: L1 | Fetched: 2026-11-23 | Worker: pyqt6 (Q3)

Key verbatim quotes:

1. Segoe UI = Windows' built-in UI font with full Cyrillic:
"Segoe UI is a version of Microsoft's branding typeface Segoe that is designed specifically for use on screen... It became Microsoft's default user interface font with the release of Windows Vista in 2007... Segoe UI supports a very wide range of languages and scripts, including the Latin, Greek, and Cyrillic alphabets, Arabic, Hebrew, Armenian, Georgian, Vietnamese, Lisu, and Volapuk, as well as digits (number symbols) for most writing systems."

2. Code pages explicitly include Cyrillic:
"Code pages | 1252 Latin 1 / 1250 Latin 2: Eastern Europe / 1251 Cyrillic / 1253 Greek / 1254 Turkish / 1255 Hebrew / 1256 Arabic / 1257 Windows Baltic / 1258 Vietnamese ..."

Cross-check — Consolas (bundled mono), https://learn.microsoft.com/en-us/typography/font-list/consolas:
"Consolas is aimed for use in programming environments and other circumstances where a monospaced font is specified... OpenType features include hanging or lining numerals; slashed, dotted and normal zeros; and alternative shapes for a number of lowercase letters."
Its code pages also include "1251 Cyrillic" (plus "855 IBM Cyrillic; primarily Russian", "866 MS-DOS Russian") — i.e. the Windows-bundled monospace option covers Cyrillic natively too.
