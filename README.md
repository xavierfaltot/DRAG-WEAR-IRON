<img width="1163" height="941" alt="DRAGWEARIRON_LOGO" src="https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6" />

# DRAG WEAR IRON — v0.16 / WEAR IT ALL

Local Mac virtual try-on machine.

**BODY MASTER → GARMENTS → NANO BANANA PRO → LOOKS**

## v0.16

- new retro-futurist industrial UI using the DRAG / WEAR / IRON pink, cream and green palette
- large round green **WEAR IT ALL** button
- **WEAR IT ALL** automatically classifies garment references into `TOP / BOTTOM / JACKET / FULL`
- builds wearable combinations rather than meaningless permutations
- generates each complete look with the BODY plus multiple garment references in one Gemini request
- exports results to `ALL THAT YOU CAN WEAR/<date_time>/`
- creates `ALL_THAT_YOU_CAN_WEAR.zip`
- Gemini calls now use a fresh client for each request / retry to avoid stale SDK sessions and the `Cannot send a request, as the client has been closed` failure
- Gemini key test also creates and closes a fresh client explicitly
- classic **IRON ALL**, BODY LOCK, GARMENT LOCK, FRAME LOCK, retry and restore remain available

## WEAR IT ALL logic

Examples:

- `3 TOP × 2 BOTTOM = 6 base looks`
- with `2 JACKET` each base look is also generated with each jacket
- `FULL` garments are generated alone and with each jacket
- if only TOPs or only BOTTOMs are supplied, those standalone possibilities are still generated
- jackets are never stacked with other jackets and bottoms are never stacked with bottoms

The wardrobe classification for each run is saved in `wardrobe.json`.

## Engine

Default: Google Gemini API / **Gemini 3 Pro Image** (`gemini-3-pro-image`), aka Nano Banana Pro.

Garment sorting for WEAR IT ALL uses **Gemini 2.5 Flash**.

Replicate / IDM-VTON remains available as the legacy fallback for the classic IRON ALL workflow.

## macOS

Double-click `INSTALL.command`, or run:

```bash
chmod +x INSTALL.command run.sh
./run.sh
```

`run.sh` launches `app_v016.py`. It rebuilds an obsolete Python environment when necessary and installs dependencies from `requirements.txt`.

## First Gemini setup

1. Create a Gemini API key in Google AI Studio.
2. Paste it into **GEMINI API KEY**.
3. Click **TEST + SAVE GEMINI KEY**.
4. A successful test displays `● GEMINI READY`.
5. The key stays local and is never committed.

## Recommended quality setup

- ENGINE: **NANO BANANA PRO**
- GARMENT INPUT: **KEEP ORIGINAL**
- BODY LOCK: ON
- GARMENT LOCK: ON
- FRAME LOCK: ON
- VARIATION: FIDELITY
- FINAL DETAIL: 0.35

Use **CLEAN FIRST** only when a garment reference includes a distracting person, rack or background.

## Output folders

Classic IRON ALL:

`outputs/<date_time>/`

WEAR IT ALL:

`ALL THAT YOU CAN WEAR/<date_time>/`

Each run keeps stable input copies, generated PNGs and session metadata for restore / retry.
