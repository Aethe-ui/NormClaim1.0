# NormClaim Function Audit Report

Date: 2026-03-28
Scope: backend Python service only
Workspace: NormClaim1.0

## How this audit was done
- Searched for exact function names requested and likely equivalents across backend Python files.
- Verified router wiring in main app to determine whether endpoint functions are reachable.
- Checked static errors in backend (editor diagnostics).
- Ran syntax compilation check for backend Python files.
- Ran targeted runtime smoke tests for selected core functions.

## Verification summary
- Static errors: none found in backend (editor diagnostics).
- Syntax compile: pass using `/usr/local/bin/python3 -m compileall -q backend`.
- Runtime smoke tests:
  - `reconcile(...)`: pass (`missed=1`, `delta=4800.0`).
  - `build_fhir_bundle_local(...)`: pass (`resourceType=Bundle`, `entries=4`).
  - `preprocess(...)`: fail in current configured environment due missing spaCy model `en_core_web_sm`.

## Findings by requested feature function

| Requested function | Status | Implemented as / location | Used? | Working status | Notes |
|---|---|---|---|---|---|
| `upload_document(file)` | Present (exact) | `upload_document` in `backend/routers/documents.py:25` | Yes | Logic appears valid | Route is active via `main.py` router inclusion. |
| `store_in_supabase(file)` | Missing (exact), present inline | Inline storage upload in `backend/routers/documents.py:50` | Yes | Conditional on Supabase config | No separate helper function; behavior embedded in route. |
| `get_document(document_id)` | Missing | No exact equivalent endpoint | No | Not implemented | Only `list_documents()` exists for documents; no document-by-id route. |
| `extract_text_pdf(file_path)` | Missing (exact), equivalent present | `extract_text_from_pdf(file_bytes)` in `backend/services/pdf_parser.py:11` | Yes | Used in extraction flow | Signature differs (`bytes` not file path). |
| `detect_scanned_vs_digital(text)` | Missing (exact), equivalent logic present | Heuristic in `backend/services/extractor.py:131` (`if not raw_text or len(raw_text) < 100`) | Yes | Basic heuristic only | No dedicated function. |
| `fallback_ocr(image/pdf)` | Missing (exact), partial fallback present | `pdf_to_base64_image` in `backend/services/pdf_parser.py:28` | Yes | Partial | Converts PDF page to image for Gemini vision; not OCR text extraction. |
| `expand_abbreviations(text)` | Present (exact) | `backend/services/nlp_preprocessor.py:35` | Yes | Blocked at runtime in current env | Fails until spaCy model is installed because module loads spaCy at import time. |
| `detect_sections(doc)` | Present (exact) | `backend/services/nlp_preprocessor.py:42` | Yes | Blocked by same import dependency | Called by `preprocess`. |
| `detect_negations(doc)` | Missing (exact), equivalent present | `detect_negated_spans` in `backend/services/nlp_preprocessor.py:63` | Yes | Blocked by same import dependency | Uses medspaCy (optional) + regex patterns. |
| `build_spacy_output(text)` | Missing (exact), equivalent present | `preprocess(raw_text)` in `backend/services/nlp_preprocessor.py:95` | Yes | Runtime fail in current env | Output includes expanded text, section map, negated spans, script. |
| `call_gemini(spacy_output)` | Missing (exact), equivalent present | `_call_gemini_with_retry` in `backend/services/extractor.py:104` | Yes | Not fully runtime-tested | Invoked inside `extract_from_document`. |
| `parse_gemini_json(response)` | Missing (exact), equivalent present | `_parse_json` in `backend/services/extractor.py:93` | Yes | Not runtime-tested separately | Handles fenced JSON and fallback regex extraction. |
| `retry_with_backoff()` | Missing (exact), equivalent present | Retry loop + `RETRY_DELAYS=[2,4,8]` in `backend/services/extractor.py:104` | Yes | Not runtime-tested separately | Implemented inside Gemini call helper. |
| `apply_negation_override(result, negated_spans)` | Present (exact) | `backend/services/extractor.py:84` | Yes | Appears valid | Called after Gemini parse. |
| `normalize_icd_codes(result)` | Missing (exact), equivalent present | `validate_icd10_codes` in `backend/services/extractor.py:66` | Yes | Appears valid | Includes fuzzy correction with RapidFuzz. |
| `filter_low_confidence(result)` | Missing | No equivalent filter function | No | Not implemented | Low confidence is tracked (`low_confidence_flags`) but not filtered in service code. |
| `map_icd10(diagnosis)` | Missing | No exact function | No | Not implemented | Mapping is indirectly done in `validate_icd10_codes`. |
| `map_drug_to_generic(brand)` | Missing (exact), partial behavior present | Drug map injected into Gemini prompt in `backend/services/extractor.py` | Indirect | Not directly verifiable | No deterministic post-LLM mapping function. |
| `normalize_medications()` | Missing | No exact function | No | Not implemented | Medication normalization is limited to defaults while constructing models. |
| `build_fhir_bundle(extraction_result)` | Missing (exact), equivalents present | `generate_fhir_bundle` (`backend/services/fhir_client.py:17`) and `build_fhir_bundle_local` (`backend/services/fhir_mapper.py:33`) | Yes | Local builder runtime pass | Route chooses Java service first, local fallback second. |
| `create_condition_resources()` | Missing (exact), logic inline | Condition creation loop in `backend/services/fhir_mapper.py` | Yes | Works in local builder test | Not extracted as standalone function. |
| `validate_fhir_bundle()` | Missing | No explicit validation in backend Python | No | Not implemented in backend | Java HAPI service may validate internally, but no explicit backend function found. |
| `compare_with_original_bill(extracted_codes, billed_codes)` | Missing (exact), equivalent present | Set comparisons in `reconcile` (`backend/services/reconciler.py:40`) | Yes | Runtime pass via `reconcile` test | Not standalone helper. |
| `calculate_claim_value(codes)` | Missing (exact), equivalent present | `estimate_claim_value` in `backend/services/reconciler.py:29` | Yes | Runtime pass via `reconcile` test | Takes one ICD code at a time. |
| `calculate_delta(missed_codes)` | Missing (exact), equivalent present | `total_delta` aggregation in `backend/services/reconciler.py` | Yes | Runtime pass via `reconcile` test | Not standalone helper. |
| `generate_reconciliation_report()` | Missing (exact), equivalent present | `reconcile` returns `ReconciliationReport` in `backend/services/reconciler.py:40` | Yes | Runtime pass | This is the main report generator. |
| `get_review_data(document_id)` | Missing (exact), equivalent present | `get_review` in `backend/services/review_service.py:31`, `fetch_review` route in `backend/routers/review.py:33` | Yes | Appears valid | Functional equivalent exists. |
| `submit_review(corrections)` | Present (exact name in route) | `submit_review` in `backend/routers/review.py:23` | Yes | Appears valid | Calls `save_review`. |
| `apply_corrections_to_result()` | Missing | No implementation found | No | Not implemented | Reviews are stored, not applied to extraction payload. |
| `store_feedback(feedback_item)` | Missing (exact), equivalent present | `save_feedback` in `backend/services/feedback_service.py:14`; route `submit_feedback` in `backend/routers/feedback.py:25` | Yes | Appears valid | Equivalent feature exists. |
| `track_error_patterns()` | Missing (exact), partial equivalent present | Aggregated `correction_type_counts` in analytics (`backend/services/analytics_service.py`) | Indirect | Appears valid | No dedicated tracking function; pattern counts are computed in snapshot. |
| `insert_document()` | Missing (exact), equivalent inline | Inline insert in `backend/routers/documents.py:66` | Yes | Conditional on Supabase config | Not abstracted into service function. |
| `insert_extraction()` | Missing | No insert call found | No | Not implemented | Extractions stored only in in-memory `EXTRACTIONS`. |
| `insert_fhir_bundle()` | Missing | No insert call found | No | Not implemented | FHIR bundles stored only in in-memory `FHIR_BUNDLES`. |
| `insert_reconciliation()` | Missing | No insert call found | No | Not implemented | Reconciliation reports stored in-memory; analytics reads DB table if present but no writer found. |
| `insert_review()` | Missing (exact), equivalent present | Insert in `save_review` (`backend/services/review_service.py:19`) | Yes | Appears valid | Writes to `human_reviews` table if Supabase client is configured. |
| `insert_feedback()` | Missing (exact), equivalent present | Insert in `save_feedback` (`backend/services/feedback_service.py:19`) | Yes | Appears valid | Writes to `feedback` table if Supabase client is configured. |

## Additional code quality observations
- Duplicate/legacy pipeline file: `backend/nlp_pipe/extraction_pipeline.py` appears unused by active routers/services.
- Several requested features are implemented as inline logic instead of dedicated named functions, which makes traceability harder.
- Supabase persistence is partial: document/review/feedback writes exist; extraction/fhir/reconciliation writes are missing.
- Runtime dependency gap in current environment: `services/nlp_preprocessor.py` requires spaCy model `en_core_web_sm` at import time.

## Recommended fixes (priority order)
1. Add missing deterministic helper functions (or wrappers) for requested API parity:
   - `get_document`, `detect_scanned_vs_digital`, `fallback_ocr`, `filter_low_confidence`, `apply_corrections_to_result`, `track_error_patterns`.
2. Add persistence service layer with explicit Supabase insert functions:
   - `insert_document`, `insert_extraction`, `insert_fhir_bundle`, `insert_reconciliation`, `insert_review`, `insert_feedback`.
3. Install and pin NLP runtime model in deployment setup:
   - Ensure `en_core_web_sm` is installed in the active runtime environment.
4. Refactor inline logic into named units for testability:
   - FHIR condition creation, reconciliation code comparison and delta calculations.
5. Add automated tests for all feature contracts listed above.

## Final assessment
- Implemented exactly as named: 4 / 37
- Implemented via equivalent logic/name: 20 / 37
- Missing or not explicitly implemented: 13 / 37
- Confirmed runtime pass (smoke-tested): reconciliation + local FHIR
- Confirmed runtime blocker in current environment: spaCy preprocessing import/model dependency
