# Criterion and Noncriterion Symptoms in Psychiatric Records: A Baseline for LLM Evaluation

## Summary

This retrospective single-center cross-sectional study of 1,252 psychiatric inpatients examined how often DSM-5 criterion and noncriterion symptoms are documented in admission chief problems, and whether documentation differs by discharge diagnostic category, specifier, course specifier, and comorbid diagnosis. Chief problems were mapped to a 105-item DSM-5 codebook, and item-level documentation rates were compared with Benjamini-Hochberg false discovery rate correction. Criterion items were documented unevenly and noncriterion anxiety or worry was recorded frequently; diagnostic category differences mostly involved group-defining items, while few differences were detected by diagnostic qualifiers. These single-center rates are reference values for tracing whether variation in language model–generated notes arises from source records or the model; an exploratory logistic regression on sentence text is also included.

## Research tool

https://5454dls.github.io/nonDSM/ returns a probability for each diagnostic group from 3 to 10 selected chief problems.

## Contents

| Path | Description |
|---|---|
| `analysis.ipynb` | Analysis notebook: documentation rates with bootstrap CIs, paired comparisons and six-axis group comparisons with FDR control, exploratory sentence-level logistic regression. |
| `diagnosis_rules.py` | Rules that map free-text diagnoses to diagnostic groups, specifiers, and stages; imported by the notebook. |
| `make_synthetic_data.py` | Generates the synthetic table with a fixed seed. |
| `synthetic/synthetic_chief_problems.csv` | Invented table in the layout of the study data: one row per chief-problem sentence (`dx1`, `dx2`, `dx3`, `cp_korean`, `cp_english`, `label_a`, `label_b`); 24 patients. |
| `synthetic/codebook.csv` | The 105-item codebook (code, domain, item). |
| `requirements.txt` | Python packages for the notebook. |
| `index.html`, `script.js`, `style.css` | The research tool (static page; computes in the browser). |
| `model_all_groups.json` | Model coefficients, cut-offs, and performance used by the tool. |
| `item_domains.json` | Codebook domain of each chief-problem item, used by the tool. |
| `.nojekyll` | Empty file; GitHub Pages serves the folder as it is. |
