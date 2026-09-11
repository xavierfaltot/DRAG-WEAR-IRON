# DRAG WEAR IRON — NEXT CHAT HANDOFF

Je veux continuer **DRAG WEAR IRON**.

Repo GitHub:
https://github.com/xavierfaltot/DRAG-WEAR-IRON

Current version:
**v0.13 — NANO BANANA PRO FINISH PASS**

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
- failed batch items no longer abort the complete run
- REGENERATE ONE LOOK
- RESTORE LAST SESSION
- persistent run `session.json`
- stable copies of BODY and GARMENT inputs inside each run
- `.last_session.json` pointer is local-only and Git ignored

Google API status checked against official docs on 2026-09-11:
- stable Nano Banana Pro model code is still `gemini-3-pro-image`
- image + text inputs and image output are supported
- `generate_content` remains documented
- image `response_format` supports aspect ratio and image size for Gemini 3 Pro Image
- current app requests 2K + BODY-nearest aspect ratio when supported
- safe SDK fallback remains if `response_format` is unavailable locally

Important design choices:
- no forced 3:4 crop
- no stretched GIF
- BODY framing remains the master frame
- originals are copied into the run; user originals are not modified
- simplest possible Mac launch
- Gemini remains the main engine

NEXT TASK / ACCEPTANCE TEST:
1. Pull/run v0.13 on the Mac.
2. Test the saved real Gemini API key with `TEST + SAVE GEMINI KEY`.
3. Run one BODY + one garment that was already tested in Google Flow.
4. Compare BODY identity, background stability and garment construction.
5. If the output is weak, test REGENERATE ONE LOOK.
6. Close/reopen the app and test RESTORE LAST SESSION.
7. Only if real-world A/B results show face/background drift, add a compositing/masking BODY LOCK pass.

Do not revert to IDM-VTON as the main engine unless Gemini actually fails.
Use Nano Banana Pro / Google Flow as the quality reference.
