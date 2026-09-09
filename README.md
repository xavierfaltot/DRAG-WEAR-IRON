<img width="1163" height="941" alt="DRAGWEARIRON_LOGO" src="https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6" />

# DRAG WEAR IRON — v0.11 AUTO

Virtual try-on machine for turning real shop garment photos into a consistent worn-look sequence.

**BODY → CLEAN CLOTH → AUTO CATEGORY → IRON → PNG SEQUENCE**

## Current engine

Replicate / IDM-VTON. CLEAN CLOTH and AUTO CATEGORY run locally. The Replicate token is stored only in `.replicate_token`, which is ignored by Git.

## macOS

Double-click `INSTALL.command`, or from Terminal:

```bash
chmod +x INSTALL.command run.sh
./run.sh
```

The launcher creates `.venv`, installs/checks dependencies and opens the app in the browser.

## Visible controls

### MASTER BODY
The reference person. This is the body, pose, framing and identity the try-on engine starts from.

### CLOTH PREP
- **CLEAN FIRST**: removes the shop/rack/background around each garment and puts it on a neutral catalogue canvas before try-on. Recommended for messy shop photos.
- **KEEP ORIGINAL**: sends the original garment photo directly to the model.

### CENTER FOCUS
Controls how aggressively CLEAN CLOTH looks around the center of the source garment photo before background removal.
- **AUTO**: balanced default.
- **WIDE**: keeps more of the source image; useful for coats, wide garments or imperfect framing.
- **TIGHT**: concentrates more strongly on the center; useful when neighboring clothes interfere.

### CATALOGUE PADDING
Space left around the isolated garment on its neutral background. More padding = smaller garment with more breathing room. Less padding = garment fills more of the conditioning image.

### CATEGORY
- **AUTO**: classifies every garment separately, so tops, trousers/skirts and dresses can be mixed in one batch.
- **UPPER**: force upper-body clothing.
- **LOWER**: force trousers/skirts/lower-body clothing.
- **DRESS**: force dresses/one-piece clothing.

AUTO is silhouette-based and can make mistakes; the manual modes are overrides.

### GARMENT DESCRIPTION
Text conditioning sent with the garment. The default asks the model to preserve color, fabric, cut, seams, pockets, buttons and details. Edit it when a garment has an important feature the model keeps losing.

### PRESERVE BODY FRAME / CROP
When ON, asks the backend not to use its automatic person crop. Recommended when the original framing matters. This reduces unwanted reframing but cannot guarantee pixel-perfect body preservation because IDM-VTON still generates the try-on result.

### STEPS
Number of diffusion/inference steps used by IDM-VTON. Higher can improve convergence/detail but costs more time and does not automatically mean a more faithful garment. Default: 30.

### FINAL DETAIL / ANTI-BLUR
A mild local sharpening pass after generation. It can recover apparent detail, but it does **not** fix a bad VTON mask or a generated halo. Keep it moderate; too high can create edge halos.

### SEED
Starting random seed. It controls repeatability. The batch currently uses `seed + garment index`, so each garment gets a deterministic but different seed.

### TEST + SAVE TOKEN
Checks the Replicate connection and stores the token locally on this Mac. Never commit or paste the token into GitHub.

### PREVIEW CLEAN CLOTH
Shows what the garment looks like after local cleanup, before spending a Replicate generation. This is the best place to catch a bad cutout.

### IRON ALL
Processes the whole batch and exports the generated looks plus `DRAG_WEAR_IRON_SEQUENCE.zip`.

## Known image-quality issue

A halo/blur or body deformation can still come from IDM-VTON regenerating more of the person than desired. The next architecture target is **BODY LOCK / GARMENT ONLY**: preserve original BODY pixels outside the clothing transition region instead of trying to repair the whole generated image with sharpening.

## Licensing

Verify the current IDM-VTON / hosted model license before commercial deployment.
