# DRAG WEAR IRON — NEXT CHAT HANDOFF

Je veux continuer **DRAG WEAR IRON**.

Repo GitHub:
https://github.com/xavierfaltot/DRAG-WEAR-IRON

Current version:
**v0.14 — NANO BANANA PRO PRODUCTION FINISH**

Current architecture:
- local Mac / Python / Gradio
- BODY MASTER + batch GARMENT references
- default engine = Google Gemini API `gemini-3-pro-image` / Nano Banana Pro
- fallback engine = Replicate IDM-VTON
- Gemini API key stored locally in `.gemini_api_key`
- Replicate token stored locally in `.replicate_token`
- BODY LOCK = exact identity / face / pose / anatomy preservation prompt
- GARMENT LOCK = exact garment construction/details
- FRAME LOCK = BODY composition + nearest supported Gemini aspect ratio + normalization to BODY canvas
- garment modes = AUTO / TOP / JACKET / BOTTOM / FULL
- variation = FIDELITY / NATURAL
- PNG batch export
- failed batch items do not abort the complete run
- REGENERATE ONE LOOK
- RESTORE LAST SESSION
- persistent run `session.json`
- stable copies of BODY and GARMENT inputs inside each run
- `.last_session.json` pointer is local-only and Git ignored

v0.14 production hardening:
- Gemini request automatically retries up to 3 times with short backoff
- image extraction handles both `response.parts` and `candidates[].content.parts`
- no-image / block reason is surfaced more clearly
- CLEAN FIRST preview continues when one garment fails
- CLEAN FIRST during IRON ALL no longer aborts the whole batch
- REGENERATE ONE LOOK retries CLEAN FIRST first when preparation failed
- FINAL DETAIL sharpening now keeps a PNG intermediate instead of JPEG
- launchers + run manifests identify v0.14

Google API status checked against official docs on 2026-09-11:
- `gemini-3-pro-image` supports image generation/editing
- image + text inputs and image output are supported
- `generate_content` remains documented
- `response_format` supports aspect ratio and image size for Gemini 3 Pro Image
- current app requests 2K + BODY-nearest supported aspect ratio when FRAME LOCK is enabled
- safe SDK fallback remains if `response_format` is unavailable locally

Important design choices:
- no forced 3:4 crop
- no stretched GIF
- BODY framing remains the master frame
- originals are copied into the run; user originals are not modified
- simplest possible Mac launch
- Gemini remains the main engine
- do NOT add compositing/masking BODY LOCK unless the real A/B test demonstrates actual face/background drift

NEXT TASK / ACCEPTANCE TEST:
1. Pull/run v0.14 on the Mac.
2. Test the saved real Gemini API key with `TEST + SAVE GEMINI KEY`.
3. Run one BODY + one garment already tested in Google Flow.
4. Compare BODY identity, background stability and garment construction.
5. Test REGENERATE ONE LOOK once, including a deliberately weak or failed result if possible.
6. Close/reopen the app and test RESTORE LAST SESSION.
7. Test CLEAN FIRST on a small batch and confirm one bad garment does not kill the rest.
8. Only if real-world A/B results show face/background drift, add a compositing/masking BODY LOCK pass.

Do not revert to IDM-VTON as the main engine unless Gemini actually fails.
Use Nano Banana Pro / Google Flow as the quality reference.
