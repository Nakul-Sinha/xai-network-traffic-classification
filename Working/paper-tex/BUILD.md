# Building the IEEEtran PDF (camera-ready style)

Two-column IEEE-Transactions build of the manuscript (matches the IEEE TNSM target format),
converted from `../manuscript.md`.

## Files (self-contained)
- `main.tex`      the paper, IEEEtran two-column
- `IEEEtran.cls`  IEEE Transactions document class (bundled so it compiles without a system install)
- `IEEEtran.bst`  IEEE bibliography style
- `refs.bib`      bibliography (copy of `../references.bib`)
- `figures/`      the four figures (Fig 1 operator validity, Fig 2 necessity, Fig 3 false-confidence,
                  Fig 4 threshold sensitivity)
- `paper.pdf`     the compiled output (14 pp, two-column; references [1]-[37])

## Rebuild
Needs a LaTeX distribution (TeX Live / TinyTeX / MiKTeX) providing `pdflatex` and `bibtex`.

    pdflatex main
    bibtex   main
    pdflatex main
    pdflatex main

(or `latexmk -pdf main`). The result is `main.pdf`; `paper.pdf` is a copy of it.

## Notes
- Wide tables (Table IV, the two-corpus / three-model byte-level audit) use `table*` so they span both
  columns and do not overflow; the rest are single-column.
- Citations render as IEEE numbers via `\bibliographystyle{IEEEtran}` + bibtex; the compile is clean
  (no undefined references or citations, no overfull boxes).
