# ChurnIQ model evaluation — October 2026

## What was evaluated

The existing saved model (`models/churn_model.joblib`) was preserved. Its recorded feature schema expects the telecom-specific fields `telecom_partner`, `gender`, `age`, `state`, `city`, `num_dependents`, `estimated_salary`, `calls_made`, `sms_sent`, `data_used`, `tenure_months`, and `registration_year`.

The package does not include an independent, untouched test set or reliable artifact-level training provenance for that exact saved model. Evaluating that serialized artifact against the full cleaned CSV would risk testing on rows it may already have seen. Therefore, `churniq_model_diagnostics.py` was run as a **fresh stratified 80/20 holdout experiment** on `data/cleaned/telecom_churn_cleaned.csv`; this measures the available feature signal and baseline models, not an independent validation of the saved artifact.

## Holdout results

- Dataset rows: 243,553
- Training rows: 194,842
- Test rows: 48,711
- Churn prevalence in train and test: approximately 20.05%
- Identifier-like `customer_id` excluded from model features

| Fresh model | Accuracy | Balanced accuracy | Precision (churn) | Recall (churn) | F1 (churn) | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| Dummy most-frequent baseline | 0.7995 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5000 |
| Logistic Regression | 0.7995 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.5057 |
| Balanced Logistic Regression | 0.5177 | 0.5037 | 0.2030 | 0.4802 | 0.2853 | 0.5057 |

Balanced Logistic Regression confusion matrix on the held-out split (`[[TN, FP], [FN, TP]]`):

```text
[[20531 18415]
 [ 5076  4689]]
```

## Interpretation and decision

- ROC-AUC of 0.5057 is close to random ranking and is not sufficient for customer-level risk decisions.
- The unbalanced model achieves 79.95% accuracy by predicting every customer as retained; it has zero churn recall. That accuracy must not be presented as a useful churn model.
- Balancing classes improves recall but creates many false positives and does not improve ranking quality.
- Do not silently change thresholds to manufacture churn predictions. Keep the model marked **limited / demonstration only**.
- Before retraining, validate the churn label's business definition, observation window, and feature timing. Collect stronger predictive features, compare cross-validation results to a baseline, evaluate calibration and precision/recall at operational thresholds, and preserve a truly untouched test set.

## Compatibility

The serialized model was trained with scikit-learn `1.7.2`; `backend/requirements.txt` pins `scikit-learn==1.7.2`. The current isolated validation environment has `1.8.0`, and package installation was unavailable due to network/DNS restrictions. Consequently, test runs in that environment emit `InconsistentVersionWarning`; those warnings are not being hidden or described as resolved. Install the project's pinned requirements in the user's local virtual environment and confirm `/health` reports `model_compatibility: compatible_version` before relying on model predictions.
