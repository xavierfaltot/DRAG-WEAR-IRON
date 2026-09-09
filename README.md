# DRAG WEAR TOOL

Batch virtual try-on operator for generating multiple locked-pose clothing variations from one person image.

## Core idea

- Load one BODY reference image
- Drop a folder of CLOTHES
- Keep pose, framing, face, background and lighting locked
- Generate one or more outputs per garment
- Export an aligned PNG sequence ready for animation

## Target workflow

1. BODY — master person image
2. CLOTHES — folder of garment photos
3. POSE LOCK — preserve pose and framing
4. FACE LOCK — preserve identity
5. BACKGROUND LOCK — preserve scene
6. GENERATE ALL — batch all garments
7. EXPORT — PNG sequence / preview video

## Planned UI

```text
┌──────────────────────────────────────┐
│            DRAG WEAR TOOL            │
├──────────────────────────────────────┤
│ BODY         [ DROP IMAGE ]          │
│ CLOTHES      [ DROP FOLDER ]         │
│                                      │
│ CATEGORY     [ AUTO ]                │
│ POSE LOCK    [ ON ]                  │
│ FACE LOCK    [ ON ]                  │
│ BACKGROUND   [ LOCKED ]              │
│ OUTPUT       [ 9:16 / ORIGINAL ]     │
│                                      │
│          [ GENERATE ALL ]            │
├──────────────────────────────────────┤
│ LOOK 01  LOOK 02  LOOK 03  LOOK 04  │
│                                      │
│ [ EXPORT PNG SEQUENCE ]              │
│ [ EXPORT VIDEO PREVIEW ]             │
└──────────────────────────────────────┘
```

## Status

Initial project scaffold.
