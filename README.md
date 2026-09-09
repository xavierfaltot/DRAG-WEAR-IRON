# DRAG WEAR TOOL

Batch virtual try-on UI built for a locked-pose clothing animation workflow.

## Workflow

1. Drop one **BODY** master image.
2. Drop many **CLOTHES** images.
3. Generate every garment on the same person.
4. Export aligned PNGs as a ZIP.
5. Export a quick MP4 outfit-change preview.

## macOS

Double-click `INSTALL.command`, or run:

```bash
chmod +x run.sh
./run.sh
```

The first launch creates a Python virtual environment and installs the UI dependencies.

## Engine

The first build connects to a Gradio/Hugging Face virtual try-on backend. Default: `zhengchong/CatVTON`.

**Important:** CatVTON weights are licensed under CC BY-NC-SA 4.0, so use that default backend for non-commercial prototyping only. DRAG WEAR TOOL itself is backend-agnostic and can later be pointed at a commercially licensed compatible endpoint.

## Animation principle

All generated looks use the same BODY source and the same output canvas size. The exported MP4 switches garments without changing the framing, which gives a clean base for the locked-pose outfit animation.
