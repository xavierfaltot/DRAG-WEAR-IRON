<img width="1163" height="941" alt="DRAGWEARIRON_LOGO" src="https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6" />

# DRAG WEAR IRON — v0.13 NANO BANANA PRO

Local Mac virtual try-on machine.

**BODY MASTER → GARMENT REFERENCE → NANO BANANA PRO → PNG SEQUENCE**

## Default engine

Google Gemini API / **Gemini 3 Pro Image** (`gemini-3-pro-image`), aka Nano Banana Pro.

Replicate / IDM-VTON remains available only as **IDM-VTON LEGACY** fallback.

## What v0.13 adds

- stronger BODY LOCK prompt: identity / face / anatomy / pose explicitly treated as immutable
- stronger FRAME LOCK prompt
- Gemini output aspect ratio chosen from the BODY master ratio before generation
- 2K Gemini image request when the installed SDK supports `response_format`
- safe fallback to image-only generation if an older SDK rejects that option
- every run copies BODY + garment inputs into its own persistent session folder
- batch continues if one garment fails
- failed look numbers are reported instead of destroying the whole run
- **REGENERATE ONE LOOK**
- **RESTORE LAST SESSION**
- persistent `session.json` per run
- regenerated looks automatically rebuild the PNG ZIP

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

When FRAME LOCK is enabled, v0.13 also requests the nearest supported BODY aspect ratio and 2K output where supported by the installed `google-genai` SDK.

## Legacy engine

Select **IDM-VTON LEGACY** only if Gemini is unavailable. Its Replicate token is stored locally in `.replicate_token`.

## Validation still required on the Mac

The code path is complete, but one thing cannot be validated from GitHub alone: a real Gemini image request using your local `.gemini_api_key`.

The final acceptance test is therefore:

1. launch v0.13
2. **TEST + SAVE GEMINI KEY**
3. run the same BODY + garment in Google Flow and DRAG WEAR IRON
4. compare face/background/garment fidelity
5. use **REGENERATE ONE LOOK** on any weak output
6. close/reopen and test **RESTORE LAST SESSION**

See `NEXT_CHAT_HANDOFF.md` for the exact continuation state.
