# ChurnIQ implementation checklist

This checklist describes the state of the delivered source package. “Implemented” means the relevant code exists; it does not imply the feature was verified against the user's live MySQL instance or production hosting.

## Existing features preserved

- [x] React/Vite single-page application and existing Overview
- [x] Customer directory, search, pagination, CRUD UI/API integration
- [x] Churn analysis charts and descriptive analytics
- [x] Business Insights and partner/state filters
- [x] CSV customer import workflow through Spring Boot
- [x] Existing individual churn-prediction workflow and reliability disclaimer
- [x] FastAPI analytics endpoints and shared Spring Boot/MySQL data loader
- [x] Existing notebooks, diagnostics, model artifact, and data files

## Intelligence additions

- [x] AI Intelligence navigation page
- [x] Conversational analytics over approved metrics
- [x] Optional OpenAI-compatible wording with aggregate-only context; deterministic fallback when no key or provider fails
- [x] Segment investigation with partner/state filters, descriptive findings, sample-size warning, and bounded recommendations
- [x] CSV report export from current records
- [x] Configurable churn-rate and minimum-segment-size thresholds persisted to local runtime JSON
- [x] On-demand and periodic background alert evaluation with local history
- [x] Model limitations disclosed in the AI experience
- [x] Periodic aggregate-only report snapshots (configurable interval)
- [x] Focused automated tests for new API endpoints (10 tests pass in the validation environment)
- [x] General-purpose AI routing separated from customer-data analytics; general questions no longer require a database connection
- [x] Backend health reports the expected scikit-learn version and compatibility status
- [x] Spring datasource credentials moved to environment variables; SQL logging disabled by default
- [x] Non-destructive multi-service smoke-test script added

## Known limits / follow-up for a production deployment

- [ ] Verify Spring Boot/MySQL integration on the target machine and confirm database credentials.
- [ ] Provide an optional `OPENAI_API_KEY` if LLM wording is wanted; the app works without it.
- [ ] Alert settings and history persist to local runtime files; configure durable shared storage/backups for multi-instance production deployments.
- [ ] Recurring checks log to local history; external notifications (email, Slack, etc.) require a configured delivery integration.
- [ ] Current churn model ROC-AUC is about 0.50; it must not be marketed as a reliable churn predictor.
- [ ] Establish the business definition and time window for the churn label before retraining or evaluating future churn.
- [ ] Add authentication/authorization before exposing customer records or exports to the public internet.
- [ ] Run frontend lint/build in a compatible Node environment. `npm run build` could not run here because Vite dependencies were not installed; package installation was blocked by unavailable network/DNS.
- [ ] Run the full application against the user's real MySQL instance and test CSV import, CRUD, analytics, and export end to end. The current workspace did not have the user's MySQL service/database available.
- [x] Fresh stratified 80/20 model-signal evaluation documented in `docs/MODEL_EVALUATION_2026-10.md`; results confirm near-random ranking and no model promotion was performed.
