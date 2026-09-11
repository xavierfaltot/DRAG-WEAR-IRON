<img width="1163" height="941" alt="DRAGWEARIRON_LOGO" src="https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6" />

# DRAG WEAR IRON — v0.14 NANO BANANA PRO

Local Mac virtual try-on machine.

**BODY MASTER → GARMENT REFERENCE → NANO BANANA PRO → PNG SEQUENCE**

## Default engine

Google Gemini API / **Gemini 3 Pro Image** (`gemini-3-pro-image`), aka Nano Banana Pro.

Replicate / IDM-VTON remains available only as **IDM-VTON LEGACY** fallback.

## What v0.14 adds

- production hardening on top of v0.13
- Gemini generation retries automatically up to 3 times with short backoff
- Gemini image extraction accepts both `response.parts` and candidate content parts
- clearer no-image / blocked-response error reporting
- CLEAN FIRST preview continues if one garment clean fails
- CLEAN FIRST inside IRON ALL no longer aborts the complete batch
- REGENERATE ONE LOOK retries the cleaning pass first when that look failed during CLEAN FIRST
- FINAL DETAIL sharpening now stays lossless PNG instead of using an intermediate JPEG
- launchers and manifests updated to v0.14

## Existing v0.13 core kept intact

- BODY MASTER + batch GARMENT references
- BODY LOCK = identity / face / pose / anatomy preservation
- GARMENT LOCK = exact garment construction/details
- FRAME LOCK = BODY composition + nearest supported Gemini aspect ratio + normalization to BODY canvas
- 2K Gemini request when supported
- garment modes = AUTO / TOP / JACKET / BOTTOM / FULL
- variation = FIDELITY / NATURAL
- PNG batch export
- failed generation items do not abort the complete run
- REGENERATE ONE LOOK
- RESTORE LAST SESSION
- persistent `session.json`
- stable copies of BODY and GARMENT inputs inside each run
- `.last_session.json` pointer is local-only and Git ignored

## macOS

Double-click `INSTALL.command`, or run:

```bash
chmod +x INSTALL.command run.sh
./run.sh
```

The launcher creates `.venv`, installs dependencies and opens the Gradio UI.

## First Gemini setup

1. Create a Gemini API key in Google AI Studio.
2. Paste it into **GEMINI API KEY**.
3. Click **TEST + SAVE GEMINI KEY**.
4. The key is saved only on this Mac in `.gemini_api_key`.
5. `.gemini_api_key` is ignored by Git and must never be committed.

## Recommended quality setup

- ENGINE: **NANO BANANA PRO**
- GARMENT INPUT: **KEEP ORIGINAL**
- BODY LOCK: ON
- GARMENT LOCK: ON
- FRAME LOCK: ON
- GARMENT TYPE: AUTO
- VARIATION: FIDELITY
- FINAL DETAIL: 0.35

Use **CLEAN FIRST** only when the garment reference includes a distracting person, rack or background.

## Controls

### BODY LOCK

Treats the BODY photo as the immutable identity master. The prompt explicitly locks face geometry, hair, skin, age, expression, hands, fingers, body proportions, pose and anatomy.

### GARMENT LOCK

Asks Gemini to preserve the exact garment construction: silhouette, cut, length, color, fabric, texture, print, seams, pockets, buttons, zippers, labels, cuffs, collar and hems.

### FRAME LOCK

Preserves the BODY master composition and sends Gemini the nearest supported aspect ratio before generation. The result is then normalized back to the BODY canvas.

DRAG WEAR IRON does **not** force a universal 3:4 crop.

### GARMENT TYPE

- AUTO
- TOP
- JACKET
- BOTTOM
- FULL

If the BODY already wears a jacket, enable **BODY already wears a jacket** to preserve layering.

### VARIATION

- **FIDELITY**: surgical edit / smallest possible changed region.
- **NATURAL**: allows more drape, folds and lighting integration while keeping the BODY and GARMENT references locked.

## Batch + retry

`IRON ALL` processes every garment and creates PNG outputs plus:

`DRAG_WEAR_IRON_SEQUENCE.zip`

If one look fails, the rest of the batch continues. The status reports the look number to retry.

Enter that number under **LOOK #** and click **REGENERATE ONE LOOK**.

With v0.14, a look that failed during CLEAN FIRST will retry the cleaning pass before regeneration.

## Session restore

Each run stores:

- a stable copy of the BODY
- stable copies of garment inputs
- cleaned references when CLEAN FIRST is used
- generated outputs
- `session.json`
- the rebuilt ZIP

Click **RESTORE LAST SESSION** after reopening the app to recover the previous BODY, garment list and generated looks.

Secrets are never stored in `session.json`.

## Gemini implementation

The main engine sends:

1. the editing prompt
2. BODY reference image
3. GARMENT reference image

to `gemini-3-pro-image`, requesting an image response.

When FRAME LOCK is enabled, DRAG WEAR IRON also requests the nearest supported BODY aspect ratio and 2K output where supported by the installed `google-genai` SDK.

## Legacy engine

Select **IDM-VTON LEGACY** only if Gemini is unavailable. Its Replicate token is stored locally in `.replicate_token`.

## Final acceptance test on the Mac

The code path is finished, but a real image request still has to run on the Mac that owns the local API key.

1. pull v0.14
2. launch the app
3. **TEST + SAVE GEMINI KEY**
4. run the same BODY + garment in Google Flow and DRAG WEAR IRON
5. compare face/background/garment fidelity
6. test **REGENERATE ONE LOOK**
7. close/reopen and test **RESTORE LAST SESSION**

Only if the real A/B test still shows unacceptable face/background drift should a compositing/masking BODY LOCK pass be added.

See `NEXT_CHAT_HANDOFF.md` for the exact continuation state.
