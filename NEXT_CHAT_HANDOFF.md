# DRAG WEAR IRON — NEXT CHAT HANDOFF

Paste the text below into a new ChatGPT conversation to continue the project:

---

Je veux continuer et terminer **DRAG WEAR IRON**.

Repo GitHub:
https://github.com/xavierfaltot/DRAG-WEAR-IRON

Current target version:
**v0.12 — NANO BANANA PRO**

Current architecture:
- local Mac / Python / Gradio
- BODY MASTER + batch GARMENT references
- default engine = Google Gemini API `gemini-3-pro-image` / Nano Banana Pro
- fallback engine = Replicate IDM-VTON
- Gemini API key stored locally in `.gemini_api_key`
- Replicate token stored locally in `.replicate_token`
- BODY LOCK = preserve exact identity, face, pose, anatomy
- GARMENT LOCK = preserve exact garment construction/details
- FRAME LOCK = preserve crop/background/camera
- garment modes = AUTO / TOP / JACKET / BOTTOM / FULL
- variation = FIDELITY / NATURAL
- PNG batch export

Google Flow code we studied used:
- two image references: BODY + GARMENT
- Nano Banana Pro
- body identity lock
- garment-specific transfer prompts
- JACKET / BOTTOM / FULL logic
- stable/fidelity mode

Important improvements we deliberately kept:
- no forced 3:4 crop
- no stretched GIF
- BODY framing should remain the master frame
- originals should not be modified
- simplest possible Mac launch, preferably double-click

NEXT TASK:
1. Test v0.12 with a real Gemini API key.
2. Compare output against Google Flow on the same BODY + garments.
3. Fix any API/schema errors with the current official Gemini docs.
4. Improve BODY LOCK if Gemini changes face/background/body outside the garment.
5. Add retry/regenerate-one-look and session restore.
6. Keep GitHub repo updated after each stable fix.

Do not revert to IDM-VTON as the main engine unless Gemini fails.
Use Nano Banana Pro as the quality reference.

---
