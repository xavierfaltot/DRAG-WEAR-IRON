<img width="1163" height="941" alt="DRAGWEARIRON_LOGO" src="https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6" />

# DRAG WEAR IRON — v0.12 NANO BANANA PRO

Local Mac virtual try-on machine.

**BODY MASTER → GARMENT REFERENCE → NANO BANANA PRO → PNG SEQUENCE**

## Default engine

Google Gemini API / **Gemini 3 Pro Image** (`gemini-3-pro-image`), also known as Nano Banana Pro.

The previous Replicate / IDM-VTON engine remains available as **IDM-VTON LEGACY**.

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
Keeps the BODY image as the identity master: face, hairstyle, proportions, hands, pose, expression and anatomy.

### GARMENT LOCK
Asks Gemini to preserve the exact garment from the second image: silhouette, cut, length, color, fabric, texture, seams, pockets, buttons, zippers, labels and construction details.

### FRAME LOCK
Keeps the original BODY crop, camera position, scene, background and subject placement. Unlike the Google Flow prototype we studied, DRAG WEAR IRON does not force every image into a 3:4 frame.

### GARMENT TYPE
- AUTO
- TOP
- JACKET
- BOTTOM
- FULL

The prompt changes depending on the garment type. If the BODY already wears a jacket, enable **BODY already wears a jacket** to preserve layering.

### VARIATION
- **FIDELITY**: minimal changes, strongest reference stability.
- **NATURAL**: permits more realistic folds, drape and lighting integration while keeping BODY and GARMENT locks.

## Batch output

`IRON ALL` processes every garment and creates individual PNG files plus:

`DRAG_WEAR_IRON_SEQUENCE.zip`

## API / implementation

The Gemini engine sends:

- prompt
- BODY reference image
- GARMENT reference image

to `gemini-3-pro-image`, requesting an image response. The app then normalizes the result to the BODY canvas when FRAME LOCK is enabled.

## Legacy engine

Select **IDM-VTON LEGACY** to use the former Replicate workflow. Its token is saved locally in `.replicate_token`.

## Next finishing pass

1. Run A/B tests against the Google Flow result using the same BODY + garments.
2. Fix any Gemini API/schema issue against current official docs.
3. Add a stronger BODY LOCK compositing pass if the model changes non-garment pixels.
4. Add retry/regenerate for one look.
5. Add session restore / queue persistence.
6. Optionally restore GIF/video lookbook export without stretching frames.

See `NEXT_CHAT_HANDOFF.md` to continue the project cleanly in another ChatGPT conversation.
