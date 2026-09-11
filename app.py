import os, time, zipfile, tempfile, base64, json, math
from pathlib import Path

import gradio as gr
from PIL import Image, ImageFilter, ImageOps
from rembg import remove, new_session
import requests, replicate

APP_NAME = 'DRAG WEAR IRON v0.13'
GEMINI_MODEL = 'gemini-3-pro-image'
IDM_MODEL = 'cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985'

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'outputs'
CLEAN = ROOT / 'cleaned'
ASSETS = ROOT / 'assets'
GEMINI_KEY = ROOT / '.gemini_api_key'
REPLICATE_KEY = ROOT / '.replicate_token'
LAST_SESSION = ROOT / '.last_session.json'
LOGO = ASSETS / 'DRAGWEARIRON_LOGO.png'

WORK.mkdir(exist_ok=True)
CLEAN.mkdir(exist_ok=True)
REMBG = None

CSS = '''
body,.gradio-container{background:#0b0b0b!important;color:#eee!important}
.gradio-container{max-width:1360px!important}
.brand{display:flex;gap:24px;align-items:center;margin:12px 0 24px}
.brand img{width:260px;max-width:38vw}
.brand h1{margin:0;font:900 31px Arial;letter-spacing:-1px}
.brand p{margin:8px 0 0;color:#aaa;font:12px monospace;line-height:1.5}
button.primary{background:#111!important;border:1px solid #ff168d!important;color:white!important}
.note{font:11px monospace;color:#999}
footer{display:none!important}
'''

def secret(path):
    try:
        return path.read_text().strip()
    except Exception:
        return ''

def save_secret(path, value):
    value = (value or '').strip()
    if value:
        path.write_text(value)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
    return value

def logo_uri():
    if not LOGO.exists():
        return ''
    return 'data:image/png;base64,' + base64.b64encode(LOGO.read_bytes()).decode()

L = logo_uri()
IMG = f'<img src="{L}" alt="DRAG WEAR IRON">' if L else ''
HEADER = f'''<div class="brand">{IMG}<div><h1>DRAG WEAR IRON</h1>
<p>BODY MASTER → GARMENT → NANO BANANA PRO → LOOKS<br>
BODY LOCK · GARMENT LOCK · FRAME LOCK · RETRY · SESSION RESTORE · PNG BATCH</p></div></div>'''

def files_list(files):
    if not files:
        return []
    return [f if isinstance(f, str) else f.name for f in files]

def rgb(path):
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert('RGB')

def tmp_jpg(path):
    fd, p = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    rgb(path).save(p, 'JPEG', quality=96, optimize=True)
    return p

def session():
    global REMBG
    if REMBG is None:
        REMBG = new_session('u2net')
    return REMBG

def center_focus(im, focus):
    fw, fh = {'WIDE': (.92, .96), 'TIGHT': (.66, .90)}.get(focus, (.78, .94))
    w, h = im.size
    nw, nh = int(w * fw), int(h * fh)
    l = (w - nw) // 2
    t = max(0, int((h - nh) * .35))
    return im.crop((l, t, l + nw, t + nh))

def clean_one(path, focus='AUTO', padding=70, out_dir=None):
    im = center_focus(rgb(path), focus)
    scale = min(1, 1800 / max(im.size))
    if scale < 1:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
    rgba = remove(im, session=session()).convert('RGBA')
    a = rgba.getchannel('A').filter(ImageFilter.MedianFilter(3))
    rgba.putalpha(a)
    box = a.getbbox()
    if not box:
        raise RuntimeError('No garment detected')
    obj = rgba.crop(box)
    cw = max(900, obj.width + padding * 2)
    ch = max(1200, obj.height + padding * 2)
    if cw / ch > .75:
        ch = int(cw / .75)
    else:
        cw = int(ch * .75)
    canvas = Image.new('RGB', (cw, ch), (245, 243, 239))
    canvas.paste(obj, ((cw - obj.width) // 2, (ch - obj.height) // 2), obj)
    dest = Path(out_dir) if out_dir else CLEAN
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / f'{int(time.time()*1000)}_{Path(path).stem}_clean.jpg'
    canvas.save(out, 'JPEG', quality=97, optimize=True)
    return str(out)

def clean_batch(files, focus, padding, progress=gr.Progress()):
    ps = files_list(files)
    if not ps:
        raise gr.Error('Ajoute au moins une photo de vêtement.')
    outs = []
    for i, p in enumerate(ps):
        progress((i, len(ps)), desc=f'CLEAN {i+1}/{len(ps)}')
        outs.append(clean_one(p, focus, int(padding)))
    return outs, f'{len(outs)} CLEAN CLOTH READY'

def prompt_for(category, has_jacket, body_lock, garment_lock, frame_lock, variation, notes):
    if category == 'JACKET':
        task = 'TASK: LAYERED DRESSING. Put the exact jacket from IMAGE 2 over the clothes already worn in IMAGE 1. Keep all non-jacket garments from IMAGE 1.'
    elif category == 'BOTTOM':
        task = 'TASK: LOWER GARMENT CHANGE. Replace only the pants/skirt/shorts on IMAGE 1 with IMAGE 2. Keep upper clothing unchanged.' + (' Keep the existing jacket exactly unchanged.' if has_jacket else '')
    elif category == 'TOP':
        task = 'TASK: UPPER GARMENT CHANGE. Replace only the top/shirt/sweater on IMAGE 1 with IMAGE 2. Keep lower garments unchanged.' + (' Preserve the jacket and place the top underneath it.' if has_jacket else '')
    elif category == 'FULL':
        task = 'TASK: COMPLETE OUTFIT TRANSFER. Replace the clothing on IMAGE 1 with the exact outfit shown in IMAGE 2.'
    else:
        task = 'TASK: AUTOMATIC GARMENT TRANSFER. Infer what garment IMAGE 2 contains and replace only the corresponding clothing region on IMAGE 1.'

    locks = []
    if body_lock:
        locks.append(
            'BODY LOCK — ABSOLUTE: IMAGE 1 is the master photograph, not inspiration. '
            'Preserve the exact same person, face, facial geometry, eyes, nose, mouth, ears, hairline, hairstyle, skin tone, age, expression, hands, fingers, body proportions, pose and anatomy. '
            'Do not beautify, reshape, retouch, de-age, re-pose or reinterpret the person. Non-garment body pixels should remain visually unchanged.'
        )
    if frame_lock:
        locks.append(
            'FRAME LOCK — ABSOLUTE: Preserve IMAGE 1 canvas orientation, crop, camera position, lens feel, perspective, subject scale, subject placement, background, floor, walls, furniture, lighting direction and depth of field. '
            'Do not zoom, crop, extend, rotate, recenter or redesign the scene.'
        )
    if garment_lock:
        locks.append(
            'GARMENT LOCK — ABSOLUTE: IMAGE 2 is the garment construction reference. Preserve its silhouette, length, cut, color, fabric, texture, weave, print, seams, pockets, buttons, zippers, labels, cuffs, collar, hems and construction details. '
            'Do not simplify, redesign, recolor or invent details.'
        )

    var = (
        'VARIATION: MINIMAL. Perform a surgical edit. Change only pixels necessary to dress the garment and create physically plausible occlusion/shadows.'
        if variation == 'FIDELITY'
        else 'VARIATION: NATURAL. Keep BODY and GARMENT identity locked, while allowing realistic drape, folds, tension, shadows and lighting integration.'
    )
    extra = f'ADDITIONAL GARMENT NOTES: {notes.strip()}' if (notes or '').strip() else ''

    return f'''You are performing a precise two-reference fashion photo edit.

REFERENCE ORDER IS CRITICAL:
IMAGE 1 = BODY MASTER / PERSON / CAMERA / BACKGROUND / COMPOSITION.
IMAGE 2 = GARMENT REFERENCE ONLY.

{task}

{' '.join(locks)}

{var}

{extra}

EDIT DISCIPLINE:
- Treat IMAGE 1 as the base layer.
- Edit the smallest possible region needed for the garment transfer.
- Keep every unrelated object and body feature from IMAGE 1 untouched.
- Preserve natural overlaps between hair, hands, arms, jacket layers and the transferred garment.
- Preserve existing accessories unless the garment physically covers them.
- Do not add text, people, props, logos or accessories that are not present in the references.

FINAL CHECK BEFORE OUTPUT:
1. Same person as IMAGE 1.
2. Same pose and anatomy as IMAGE 1.
3. Same framing/background as IMAGE 1.
4. Same garment construction as IMAGE 2.
5. Only the intended clothing region changed.
6. Photorealistic fabric physics, edges, occlusion and shadows.
7. Return one final edited fashion photograph only.'''

ASPECTS = {
    '1:1': 1.0, '1:4': .25, '1:8': .125, '2:3': 2/3, '3:2': 1.5,
    '3:4': .75, '4:1': 4.0, '4:3': 4/3, '4:5': .8, '5:4': 1.25,
    '8:1': 8.0, '9:16': 9/16, '16:9': 16/9, '21:9': 21/9
}

def nearest_aspect(path):
    im = rgb(path)
    ratio = im.width / im.height
    return min(ASPECTS, key=lambda k: abs(math.log(ratio / ASPECTS[k])))

def normalize_to_body(result_path, body_path):
    body = rgb(body_path)
    result = rgb(result_path)
    bw, bh = body.size
    rw, rh = result.size
    br, rr = bw / bh, rw / rh
    if abs(br - rr) / br < .025:
        result = result.resize((bw, bh), Image.Resampling.LANCZOS)
    else:
        result = ImageOps.fit(result, (bw, bh), Image.Resampling.LANCZOS, centering=(.5, .5))
    fd, p = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    result.save(p, 'PNG')
    return p

def run_gemini(person, cloth, prompt, key, frame_lock=True):
    key = (key or '').strip() or secret(GEMINI_KEY)
    if not key:
        raise RuntimeError('Gemini API key missing')
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    config_kwargs = {'response_modalities': ['IMAGE']}
    if frame_lock:
        config_kwargs['response_format'] = {
            'image': {'aspect_ratio': nearest_aspect(person), 'image_size': '2K'}
        }

    try:
        config = types.GenerateContentConfig(**config_kwargs)
    except Exception:
        config = types.GenerateContentConfig(response_modalities=['IMAGE'])

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, rgb(person), rgb(cloth)],
        config=config
    )

    image = None
    for part in getattr(response, 'parts', []) or []:
        if getattr(part, 'inline_data', None) is not None:
            try:
                image = part.as_image()
            except Exception:
                image = None
            if image is not None:
                break
    if image is None:
        raise RuntimeError('Gemini returned no image')

    fd, p = tempfile.mkstemp(suffix='.png')
    os.close(fd)
    image.convert('RGB').save(p, 'PNG')
    if frame_lock:
        q = normalize_to_body(p, person)
        try:
            os.remove(p)
        except Exception:
            pass
        return q
    return p

def run_idm(person, cloth, category, description, steps, seed, token, preserve):
    token = (token or '').strip() or secret(REPLICATE_KEY)
    if not token:
        raise RuntimeError('Replicate token missing')
    cat = {'TOP': 'upper_body', 'JACKET': 'upper_body', 'BOTTOM': 'lower_body', 'FULL': 'dresses', 'AUTO': 'upper_body'}.get(category, 'upper_body')
    pj, cj = tmp_jpg(person), tmp_jpg(cloth)
    try:
        with open(pj, 'rb') as hf, open(cj, 'rb') as gf:
            output = replicate.Client(api_token=token).run(
                IDM_MODEL,
                input={
                    'human_img': hf, 'garm_img': gf, 'garment_des': description or 'exact same garment',
                    'category': cat, 'crop': not bool(preserve), 'steps': int(steps),
                    'seed': int(seed), 'force_dc': category == 'FULL', 'mask_only': False
                }
            )
    finally:
        for p in (pj, cj):
            try:
                os.remove(p)
            except Exception:
                pass
    u = output.url if hasattr(output, 'url') and isinstance(output.url, str) else (output.url() if hasattr(output, 'url') else str(output))
    r = requests.get(u, timeout=180)
    r.raise_for_status()
    fd, p = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    Path(p).write_bytes(r.content)
    return p

def test_gemini(key):
    key = (key or '').strip() or secret(GEMINI_KEY)
    if not key:
        return 'GEMINI KEY REQUIRED'
    try:
        from google import genai
        genai.Client(api_key=key).models.get(model=GEMINI_MODEL)
        save_secret(GEMINI_KEY, key)
        return f'ENGINE OK • {GEMINI_MODEL} • KEY SAVED LOCALLY'
    except Exception as e:
        return 'GEMINI ERROR • ' + str(e)

def test_replicate(token):
    token = (token or '').strip() or secret(REPLICATE_KEY)
    if not token:
        return 'REPLICATE TOKEN REQUIRED'
    try:
        replicate.Client(api_token=token).models.get('cuuupid/idm-vton')
        save_secret(REPLICATE_KEY, token)
        return 'LEGACY ENGINE OK • IDM-VTON READY'
    except Exception as e:
        return 'REPLICATE ERROR • ' + str(e)

def sharpen(path, amount):
    if float(amount) <= 0:
        return path
    im = Image.open(path).convert('RGB').filter(ImageFilter.UnsharpMask(1.05, int(55 + float(amount) * 45), 3))
    fd, p = tempfile.mkstemp(suffix='.jpg')
    os.close(fd)
    im.save(p, 'JPEG', quality=97, optimize=True)
    return p

def safe_stem(path):
    s = ''.join(c if c.isalnum() or c in '-_' else '_' for c in Path(path).stem)
    return s[:70] or 'garment'

def save_input_copy(src, dst):
    im = rgb(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, 'PNG')
    return str(dst)

def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding='utf-8')

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def build_zip(manifest):
    rd = Path(manifest['run_dir'])
    zp = rd / 'DRAG_WEAR_IRON_SEQUENCE.zip'
    outputs = [item.get('output') for item in manifest['items'] if item.get('output') and Path(item['output']).exists()]
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in outputs:
            z.write(p, arcname=Path(p).name)
    return str(zp), outputs

def persist_manifest(manifest):
    path = Path(manifest['run_dir']) / 'session.json'
    write_json(path, manifest)
    write_json(LAST_SESSION, {'manifest': str(path)})
    return str(path)

def engine_run(person, cloth, cfg, gkey, rtoken):
    prompt = prompt_for(
        cfg['category'], cfg['has_jacket'], cfg['body_lock'], cfg['garment_lock'],
        cfg['frame_lock'], cfg['variation'], cfg['notes']
    )
    if cfg['engine'] == 'NANO BANANA PRO':
        return run_gemini(person, cloth, prompt, gkey, cfg['frame_lock'])
    return run_idm(
        person, cloth, cfg['category'], cfg['notes'], cfg['steps'],
        cfg['seed'], rtoken, cfg['frame_lock']
    )

def generate(person, raw_files, clean_mode, focus, padding, engine, category, has_jacket,
             body_lock, garment_lock, frame_lock, variation, notes, gkey, rtoken,
             steps, seed, detail, progress=gr.Progress()):
    if not person:
        raise gr.Error('Ajoute un BODY.')
    ps = files_list(raw_files)
    if not ps:
        raise gr.Error('Ajoute au moins un vêtement.')

    if engine == 'NANO BANANA PRO':
        if not ((gkey or '').strip() or secret(GEMINI_KEY)):
            raise gr.Error('Ajoute ta GEMINI API KEY une fois.')
        save_secret(GEMINI_KEY, (gkey or '').strip() or secret(GEMINI_KEY))
    else:
        if not ((rtoken or '').strip() or secret(REPLICATE_KEY)):
            raise gr.Error('Ajoute ton REPLICATE API TOKEN.')
        save_secret(REPLICATE_KEY, (rtoken or '').strip() or secret(REPLICATE_KEY))

    rd = WORK / time.strftime('%Y%m%d_%H%M%S')
    if rd.exists():
        rd = WORK / f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)%1000:03d}"
    raw_dir = rd / 'inputs' / 'garments'
    clean_dir = rd / 'inputs' / 'cleaned'
    body_path = save_input_copy(person, rd / 'inputs' / 'body.png')

    cfg = {
        'clean_mode': clean_mode, 'focus': focus, 'padding': int(padding),
        'engine': engine, 'category': category, 'has_jacket': bool(has_jacket),
        'body_lock': bool(body_lock), 'garment_lock': bool(garment_lock),
        'frame_lock': bool(frame_lock), 'variation': variation, 'notes': notes or '',
        'steps': int(steps), 'seed': int(seed), 'detail': float(detail)
    }

    manifest = {
        'version': '0.13', 'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'run_dir': str(rd), 'body': body_path, 'config': cfg, 'items': []
    }

    for i, p in enumerate(ps, start=1):
        raw_copy = save_input_copy(p, raw_dir / f'{i:03d}_{safe_stem(p)}.png')
        cloth = clean_one(raw_copy, focus, int(padding), clean_dir) if clean_mode == 'CLEAN FIRST' else raw_copy
        manifest['items'].append({
            'index': i, 'source_name': Path(p).name, 'raw': raw_copy,
            'cloth': cloth, 'output': None, 'error': None
        })

    manifest_path = persist_manifest(manifest)

    for i, item in enumerate(manifest['items']):
        progress((i, len(manifest['items'])), desc=f'IRON {i+1}/{len(manifest["items"])}')
        temp = final = None
        try:
            temp = engine_run(body_path, item['cloth'], cfg, gkey, rtoken)
            final = sharpen(temp, cfg['detail'])
            out = rd / f'{item["index"]:03d}_{safe_stem(item["source_name"])}.png'
            Image.open(final).convert('RGB').save(out, 'PNG')
            item['output'] = str(out)
            item['error'] = None
        except Exception as e:
            item['output'] = None
            item['error'] = str(e)
        finally:
            for q in {temp, final}:
                if q:
                    try:
                        if Path(q).exists() and not str(q).startswith(str(rd)):
                            os.remove(q)
                    except Exception:
                        pass
            persist_manifest(manifest)

    zp, outs = build_zip(manifest)
    failed = [str(i['index']) for i in manifest['items'] if i.get('error')]
    status = f'{len(outs)}/{len(manifest["items"])} LOOKS READY • ENGINE: {engine}'
    if failed:
        status += ' • RETRY LOOK: ' + ', '.join(failed)
    return outs, zp, status, manifest_path

def regenerate_one(look_number, manifest_path, gkey, rtoken):
    try:
        idx = int(look_number)
    except Exception:
        raise gr.Error('LOOK # doit être un nombre.')
    if not manifest_path or not Path(manifest_path).exists():
        raise gr.Error('Aucune session active. Lance IRON ALL ou RESTORE LAST SESSION.')
    manifest = read_json(manifest_path)
    items = manifest.get('items', [])
    if idx < 1 or idx > len(items):
        raise gr.Error(f'LOOK # doit être entre 1 et {len(items)}.')

    cfg = manifest['config']
    item = items[idx - 1]
    temp = final = None
    try:
        temp = engine_run(manifest['body'], item['cloth'], cfg, gkey, rtoken)
        final = sharpen(temp, cfg.get('detail', .35))
        out = Path(manifest['run_dir']) / f'{idx:03d}_{safe_stem(item["source_name"])}.png'
        Image.open(final).convert('RGB').save(out, 'PNG')
        item['output'] = str(out)
        item['error'] = None
    except Exception as e:
        item['error'] = str(e)
        persist_manifest(manifest)
        raise gr.Error(f'LOOK {idx} failed: {e}')
    finally:
        for q in {temp, final}:
            if q:
                try:
                    if Path(q).exists() and not str(q).startswith(str(manifest['run_dir'])):
                        os.remove(q)
                except Exception:
                    pass

    persist_manifest(manifest)
    zp, outs = build_zip(manifest)
    return outs, zp, f'LOOK {idx} REGENERATED • {len(outs)}/{len(items)} READY', manifest_path

def restore_last_session():
    if not LAST_SESSION.exists():
        raise gr.Error('Aucune session sauvegardée.')
    pointer = read_json(LAST_SESSION)
    manifest_path = pointer.get('manifest')
    if not manifest_path or not Path(manifest_path).exists():
        raise gr.Error('La dernière session n’existe plus sur ce Mac.')
    manifest = read_json(manifest_path)
    raw_files = [item['raw'] for item in manifest.get('items', []) if Path(item.get('raw', '')).exists()]
    zp, outs = build_zip(manifest)
    failed = [str(i['index']) for i in manifest['items'] if i.get('error')]
    status = f'LAST SESSION RESTORED • {len(outs)}/{len(manifest["items"])} READY'
    if failed:
        status += ' • RETRY LOOK: ' + ', '.join(failed)
    return manifest['body'], raw_files, outs, zp, status, manifest_path

with gr.Blocks(title=APP_NAME) as demo:
    gr.HTML(HEADER)
    manifest_state = gr.State(value='')

    with gr.Row():
        with gr.Column():
            gr.Markdown('### 01 / BODY MASTER')
            person = gr.Image(type='filepath', label='MASTER BODY')

            gr.Markdown('### 02 / GARMENTS')
            garments = gr.File(file_count='multiple', file_types=['image'], label='DROP GARMENT PHOTOS')
            clean_mode = gr.Radio(['KEEP ORIGINAL', 'CLEAN FIRST'], value='KEEP ORIGINAL', label='GARMENT INPUT')
            focus = gr.Radio(['AUTO', 'WIDE', 'TIGHT'], value='AUTO', label='CLEAN FOCUS')
            padding = gr.Slider(20, 180, 70, step=10, label='CLEAN PADDING')
            cb = gr.Button('PREVIEW CLEAN CLOTH')
            cg = gr.Gallery(columns=3, label='CLEANED GARMENTS')
            cs = gr.Textbox(label='CLEAN STATUS')
            cb.click(clean_batch, [garments, focus, padding], [cg, cs])

        with gr.Column():
            gr.Markdown('### 03 / ENGINE')
            engine = gr.Radio(['NANO BANANA PRO', 'IDM-VTON LEGACY'], value='NANO BANANA PRO', label='IMAGE ENGINE')
            gr.HTML('<div class="note">DEFAULT = Gemini 3 Pro Image / Nano Banana Pro. IDM-VTON remains as fallback.</div>')
            gkey = gr.Textbox(value=secret(GEMINI_KEY), type='password', label='GEMINI API KEY')
            tg = gr.Button('TEST + SAVE GEMINI KEY')
            gs = gr.Textbox(label='GEMINI STATUS')
            tg.click(test_gemini, [gkey], [gs])
            rtoken = gr.Textbox(value=secret(REPLICATE_KEY), type='password', label='REPLICATE TOKEN — LEGACY ONLY')
            tr = gr.Button('TEST REPLICATE LEGACY')
            rs = gr.Textbox(label='LEGACY STATUS')
            tr.click(test_replicate, [rtoken], [rs])

        with gr.Column():
            gr.Markdown('### 04 / LOCKS')
            body_lock = gr.Checkbox(True, label='BODY LOCK — identity / pose / anatomy')
            garment_lock = gr.Checkbox(True, label='GARMENT LOCK — exact garment')
            frame_lock = gr.Checkbox(True, label='FRAME LOCK — same crop / background')
            has_jacket = gr.Checkbox(False, label='BODY already wears a jacket')
            category = gr.Radio(['AUTO', 'TOP', 'JACKET', 'BOTTOM', 'FULL'], value='AUTO', label='GARMENT TYPE')
            variation = gr.Radio(['FIDELITY', 'NATURAL'], value='FIDELITY', label='VARIATION')
            notes = gr.Textbox(
                value='Preserve exact garment color, fabric, cut, seams, pockets, buttons, labels and construction details.',
                label='GARMENT NOTES'
            )
            steps = gr.Slider(10, 40, 30, step=1, label='IDM-VTON STEPS')
            seed = gr.Number(42, precision=0, label='SEED')
            detail = gr.Slider(0, 2, .35, step=.05, label='FINAL DETAIL / ANTI-BLUR')
            go = gr.Button('IRON ALL', variant='primary')
            restore = gr.Button('RESTORE LAST SESSION')
            status = gr.Textbox(label='STATUS')

    gr.Markdown('### 05 / OUTPUT')
    gallery = gr.Gallery(columns=4, label='LOOKS')
    zipout = gr.File(label='PNG SEQUENCE')

    gr.Markdown('### 06 / RETRY')
    with gr.Row():
        look_number = gr.Number(1, precision=0, label='LOOK #')
        retry = gr.Button('REGENERATE ONE LOOK', variant='primary')

    go.click(
        generate,
        [person, garments, clean_mode, focus, padding, engine, category, has_jacket,
         body_lock, garment_lock, frame_lock, variation, notes, gkey, rtoken,
         steps, seed, detail],
        [gallery, zipout, status, manifest_state]
    )
    retry.click(
        regenerate_one,
        [look_number, manifest_state, gkey, rtoken],
        [gallery, zipout, status, manifest_state]
    )
    restore.click(
        restore_last_session,
        [],
        [person, garments, gallery, zipout, status, manifest_state]
    )

if __name__ == '__main__':
    demo.queue().launch(inbrowser=True, show_error=True, css=CSS)
