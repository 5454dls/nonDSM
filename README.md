# Symptom Documentation and Diagnostic Labels Capture Different Information in Psychiatric Admission Records

Code and research tool for the manuscript "Symptom Documentation and Diagnostic Labels Capture Different Information in Psychiatric Admission Records: Implications for Cohort and Reference Label Definition in Electronic Health Record Research".

## Summary

Studies that use electronic health records define cohorts and reference labels by coded diagnoses and their qualifiers, by symptoms documented in clinical text, or by automated extraction from it. This retrospective cross-sectional study of 1,252 psychiatric ward admissions in Korea from 2012 to 2020 audited whether these sources select the same admissions. Chief problem sentences were coded with a 105-item codebook mapped to the DSM-5 and compared with discharge diagnoses and qualifiers, and item-level comparisons used Benjamini-Hochberg false discovery rate control. An example symptom-extraction model, a logistic regression on character n-grams, was trained and tested on separate admissions. Documented symptoms and diagnostic labels captured different information, so the source that defines a phenotype changes which admissions are analysed.

The study data are not public. The notebook runs on the synthetic table in `synthetic/`, which has the layout of the study data but invented content. The notebook reproduces the main documentation-rate and group-comparison analyses; the supplementary regression, recalibration, and Bayes factor analyses reported in the manuscript are not included.

## Research tool

https://5454dls.github.io/nonDSM/ returns a probability for each diagnostic group from 3 to 10 selected chief problems. It is for research use only and is not a diagnostic instrument.

## Contents

| Path | Description |
|---|---|
| `analysis.ipynb` | Analysis notebook: documentation rates with confidence intervals, paired comparisons and six-axis group comparisons with FDR control, exploratory sentence-level logistic regression. |
| `diagnosis_rules.py` | Rules that map free-text diagnoses to diagnostic groups, specifiers, and stages; imported by the notebook. |
| `make_synthetic_data.py` | Generates the synthetic table with a fixed seed. |
| `synthetic/synthetic_chief_problems.csv` | Invented table in the layout of the study data: one row per chief-problem sentence (`dx1`, `dx2`, `dx3`, `cp_korean`, `cp_english`, `label_a`, `label_b`); 24 synthetic admissions. |
| `synthetic/codebook.csv` | The 105-item codebook (code, domain, item). |
| `requirements.txt` | Python packages for the notebook. |
| `index.html`, `script.js`, `style.css` | The research tool (static page; computes in the browser). |
| `model_all_groups.json` | Model coefficients, cut-offs, and performance used by the tool. |
| `item_domains.json` | Codebook domain of each chief-problem item, used by the tool. |
| `.nojekyll` | Empty file; GitHub Pages serves the folder as it is. |
