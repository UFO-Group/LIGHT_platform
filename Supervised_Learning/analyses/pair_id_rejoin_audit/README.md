# pair_id_rejoin_audit — Candidate annotation misalignment audit (analysis; not part of the runtime pipeline)

Date: 2026-09-27. Trigger: while looking up Pair_124 and the PEG/GelMA
pair ID, we found that `kmeans_results.csv` and `SwellingRatio_predict.csv`
assign different compositions to the same Pair_ID (617 of 630 differ).

## Arbitration (decisive)

Both annotations were re-pooled with the production parameters
(alpha 3 / radius 3 / 1024, polymer cols A+B) and compared row-by-row
against the feature file `kmeans-pooled.csv`:

| Annotation | Fingerprint-identical rows |
|---|---|
| **SR file (SwellingRatio_predict.csv)** | **630/630** <- ground truth |
| kmeans_results.csv | 14/630 <- misaligned |

That is: the SR file's SMILE A/B are the true compositions of the feature
rows; the SMILES columns of kmeans_results.csv are misaligned with them
(root cause not fully traced: its row order/enumeration differs from the
pooling run; all files share the 3-19 mtime, suggesting multiple same-day
generations; predict.py merges on row_index and silently aligns by row
number whenever the source lacks that column).

## Impact (item by item)

1. **The final-selection ID set is unaffected**: band/class decisions are
   made per feature row (Pair_ID = row number), independent of the
   annotation. The composition-level recomputation (both sides on true
   annotations, Selection_pipeline rule, `02_composition_rejoin.py`)
   reproduces the final 10 exactly (dropped/added empty).
2. **The YM-side material-family regex filter ran on the wrong
   compositions** (the kmeans annotation). The recomputation shows this
   happened not to change the selection (it removed other rows).
3. **The exported report's compositions were wrong for 8/10**:
   `Agent/Selection_pipeline.py` exports `SMILE A_YM` (kmeans side). Only
   Pair_1 and Pair_37 had correct exported compositions
   (`final10_true_compositions.csv` lists all true compositions).
4. **Wet-lab correspondence to be confirmed by the team**: if materials
   were prepared from the exported CSV's SMILES, then only 2/10 of those
   exported compositions carry full model evidence (in-band AND Class1);
   e.g. Pair_124's exported composition (PLGA+PVA) is truly row Pair_119,
   pred 5.972, out of band, Class0. The true compositions (e.g.
   Pair_41 = PEG+GelMA, pred 2.853, Class1 prob 0.502) are fully
   evidenced.

## Files

- `01_fingerprint_arbitration.py` — arbitration reproduction: re-pools
  both annotations and compares fingerprints row-by-row (writes
  arbitration_summary.json; tmp intermediates auto-cleaned)
- `02_composition_rejoin.py` — composition-level recomputation (result:
  10/10 identical)
- `arbitration_summary.json` — arbitration verdict (kmeans 14/630 vs
  SR 630/630)
- `corrected_selection.csv` — final-selection table under true
  annotations (incl. prob)
- `final10_true_compositions.csv` — true compositions of the final 10 +
  whether the export was correct
- `rejoin_summary.json` — kept/dropped/added summary

## Running

```bash
cd Supervised_Learning/analyses/pair_id_rejoin_audit
C:/Users/Administrator/anaconda3/envs/supervised/python.exe 01_fingerprint_arbitration.py
C:/Users/Administrator/anaconda3/envs/supervised/python.exe 02_composition_rejoin.py
```

01 ~1 min (two subprocess poolings + comparison); 02 runs in seconds.

## Migration note

Promoted on 2026-09-28 from the repo-root sandbox `pair_id_rejoin_audit/`
(path constants adapted; the 01 arbitration script was written at
promotion time — the original sandbox ran the check as an ad-hoc command,
here it is fixed as a reproducible script); the original sandbox is kept.

## Suggested follow-ups (team decisions)

- Trace and fix the row-order consistency of the kmeans_results.csv
  generation chain (unsupervised_learning_automation), or switch
  consumers to the SR annotation / composition-keyed joins
- Cross-check the actually synthesized wet-lab systems against
  `final10_true_compositions.csv`
- Fold this conclusion into the limitations draft (as an "exported
  annotation wrong but selection unchanged" item)
