# correct_export — Reference implementation of a "correct" material export (analysis; not part of the runtime pipeline)

Date: 2026-09-28. Premise: fingerprint arbitration (pair_id_rejoin_audit)
proved the SR file carries the true compositions of the 630 candidates.
Candidate-library structure: complete pairwise combinations of 36
cluster-representative materials, C(36,2) = 630.

## Specification (six principles)

- P1 One canonical table keyed by the feature row (Pair_ID); composition
  annotation taken only from the fingerprint-verified source (SR file)
- P2 Every filter acts on the same canonical compositions (no per-side
  annotation drift)
- P3 Decisions ship with their evidence: predicted value, distances to
  band edges, class probability, margin to the 0.5 boundary
- P4 Borderline visibility: margin columns + flag (band edge < 0.10 log10
  or |prob - 0.5| < 0.05); near-miss "bench" list as a separate table, so
  wet-lab contingency is planned up front
- P5 Material-family exclusion applied by FAMILY (polyacrylamide family
  and cellulose-disaccharide family, including alternate notations), not
  by a single SMILES string spelling
- P6 No silent joins: every row carries Pair_ID; the gate rule is stated

## Gate rule

in_band (2.0 <= pred <= 3.3) AND Class1 AND family filter (true
compositions), sorted by band_margin descending.

## Results

- **6 pairs selected** (correct_material_export.csv), all containing a
  GelMA component: 39 (GelMA+collagen peptide), 41 (GelMA+PEG),
  1 (gelatin+GelMA), 53 (chitin disaccharide+GelMA),
  46 (cyclodextrin/dextran+GelMA), 37 (chitosan+GelMA)
- 4 pairs excluded at the **family level** (alternate notations the
  original literal regex missed): 19 (polyacrylamide-alt+gelatin),
  44 (cellulose-disaccharide-alt+GelMA), 124 (polyacrylamide-alt+PVA),
  229 (polyacrylamide-alt+PEG)
- Borderline: 4/6 (pairs 39, 41, 53, 46 with prob1 ~ 0.50-0.54)
- Bench of 9 alternates (alternates_bench.csv): all X+GelMA, in band but
  Class0 with prob1 in [0.45, 0.50) (e.g. 42 = alginate+GelMA at 0.454)

## Semantic decision point (team must read)

"'Correct' export = 6 pairs" depends on reading the exclusion rule as a
family-level intent (covering alternate notations). Under the
literal-regex reading (the code as written), the true-annotation
recomputation still yields 10 pairs (see pair_id_rejoin_audit). The
difference instantiates the notation-sensitivity limitation (B13/D7a).
Of the wet-lab 10, six survive under this reading; four are
family-excluded (Pair_124 is also the add32 flip-out — doubly
borderline).

## Files

- `01_correct_export.py` — reference implementation (36-material family
  dict embedded)
- `correct_material_export.csv` — 6 rows, 14 columns (incl.
  rank/margins/borderline/add32 evidence)
- `alternates_bench.csv` — 9 bench rows
- `family_map.csv` / `unique_materials.txt` — 36-material family mapping

## Running

```bash
cd Supervised_Learning/analyses/correct_export
C:/Users/Administrator/anaconda3/envs/supervised/python.exe 01_correct_export.py
```

Runs in seconds; reads only the two production prediction CSVs and
`../add_robustness/predictions/` (data source of the add32_evidence
column; if absent that column stays empty and the other outputs are
unaffected).

## Migration note

Promoted on 2026-09-28 from the repo-root sandbox `correct_export/`
(path constants adapted); the original sandbox is kept.

Note: family labels inside `family_map.csv` and the export CSVs remain in
Chinese (data, not README text); English renaming on request.
