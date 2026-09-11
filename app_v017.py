import os, time, zipfile, tempfile, itertools, base64, json, math
from pathlib import Path

import gradio as gr
from PIL import Image, ImageFilter, ImageOps

APP_NAME = "DRAG WEAR IRON v0.17 — WEAR IT ALL"
IMAGE_MODEL = "gemini-3-pro-image"
CLASSIFIER_MODEL = "gemini-3.6-flash"
ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "ALL THAT YOU CAN WEAR"
ASSETS = ROOT / "assets"
LOGO = ASSETS / "DRAGWEARIRON_LOGO.webp"
KEY_FILE = ROOT / ".gemini_api_key"
OUT_ROOT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)

def secret():
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""

def save_key(key):
    key = (key or "").strip()
    if key:
        KEY_FILE.write_text(key, encoding="utf-8")
        try:
            os.chmod(KEY_FILE, 0o600)
        except Exception:
            pass
        return key, "● API KEY SAVED"
    return "", "○ ADD GEMINI API KEY"

def load_key():
    k = secret()
    return k, ("● API KEY SAVED" if k else "○ ADD GEMINI API KEY")

def rgb(path):
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")

def safe_stem(path):
    s = "".join(c if c.isalnum() or c in "-_" else "_" for c in Path(path).stem)
    return s[:60] or "garment"

def copy_png(src, dst):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    rgb(src).save(dst, "PNG")
    return str(dst)

ASPECTS = {
    "1:1":1.0,"1:4":.25,"1:8":.125,"2:3":2/3,"3:2":1.5,
    "3:4":.75,"4:1":4.0,"4:3":4/3,"4:5":.8,"5:4":1.25,
    "8:1":8.0,"9:16":9/16,"16:9":16/9,"21:9":21/9
}
def nearest_aspect(path):
    im = rgb(path)
    ratio = im.width / im.height
    return min(ASPECTS, key=lambda k: abs(math.log(ratio / ASPECTS[k])))

def normalize_to_body(result_path, body_path):
    body = rgb(body_path)
    result = rgb(result_path)
    bw,bh = body.size
    br = bw/bh
    rr = result.width/result.height
    if abs(br-rr)/br < .025:
        result = result.resize((bw,bh), Image.Resampling.LANCZOS)
    else:
        result = ImageOps.fit(result,(bw,bh),Image.Resampling.LANCZOS,centering=(.5,.5))
    fd,p = tempfile.mkstemp(suffix=".png"); os.close(fd)
    result.save(p,"PNG")
    return p

def response_parts(response):
    parts = list(getattr(response, "parts", []) or [])
    if parts:
        return parts
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        parts.extend(list(getattr(content, "parts", []) or []))
    return parts

def response_image(response):
    for part in response_parts(response):
        if getattr(part, "inline_data", None) is None:
            continue
        try:
            image = part.as_image()
        except Exception:
            image = None
        if image is not None:
            return image
    return None

def no_image_reason(response):
    feedback = getattr(response, "prompt_feedback", None)
    block = getattr(feedback, "block_reason", None) if feedback else None
    if block:
        return f"Gemini returned no image ({block})"
    texts=[]
    for part in response_parts(response):
        t=getattr(part,"text",None)
        if t: texts.append(str(t).strip())
    return "Gemini returned no image" + (": " + " ".join(texts)[:400] if texts else "")

def test_key(key):
    key = (key or "").strip() or secret()
    if not key:
        return "○ ADD GEMINI API KEY"
    from google import genai
    client = None
    try:
        client = genai.Client(api_key=key)
        client.models.get(model=IMAGE_MODEL)
        save_key(key)
        return "● GEMINI READY"
    except Exception as e:
        return "● GEMINI ERROR • " + str(e)
    finally:
        if client is not None:
            try: client.close()
            except Exception: pass

def classify(path, key):
    from google import genai
    prompt = """Classify this clothing reference into exactly ONE wearable slot.
Reply with only one word: TOP, BOTTOM, JACKET, or FULL.
TOP = shirt, tee, blouse, sweater, vest as main upper garment.
BOTTOM = pants, jeans, shorts, skirt.
JACKET = coat, blazer, overshirt, cardigan or outer layer.
FULL = dress, jumpsuit, one-piece outfit or complete full-body outfit.
No explanation."""
    last=None
    for attempt in range(2):
        client=None
        try:
            client=genai.Client(api_key=key)
            r=client.models.generate_content(model=CLASSIFIER_MODEL, contents=[prompt, rgb(path)])
            text=(getattr(r,"text","") or "").upper()
            for cat in ("JACKET","BOTTOM","FULL","TOP"):
                if cat in text:
                    return cat
            return "TOP"
        except Exception as e:
            last=e
            if attempt == 0: time.sleep(.7)
        finally:
            if client is not None:
                try: client.close()
                except Exception: pass
    raise RuntimeError(f"Garment classification failed: {last}")

def combinations(groups):
    tops,bottoms,jackets,fulls=[groups[k] for k in ("TOP","BOTTOM","JACKET","FULL")]
    bases=[]
    if tops and bottoms:
        bases += [([t,b],["TOP","BOTTOM"]) for t,b in itertools.product(tops,bottoms)]
    elif tops:
        bases += [([t],["TOP"]) for t in tops]
    elif bottoms:
        bases += [([b],["BOTTOM"]) for b in bottoms]
    bases += [([f],["FULL"]) for f in fulls]
    combos=[]
    for entries, labels in bases:
        combos.append((entries,labels))
        for j in jackets:
            combos.append((entries+[j],labels+["JACKET"]))
    if not bases:
        combos += [([j],["JACKET"]) for j in jackets]
    return combos

def combo_prompt(labels):
    refs="\n".join(f"IMAGE {i} = {label} GARMENT REFERENCE" for i,label in enumerate(labels,start=2))
    return f"""Create ONE photorealistic fashion image using all references.

IMAGE 1 = BODY MASTER. Keep the exact same person, face, hair, expression, hands,
body proportions, pose, camera, crop, background, lighting, scale and placement.

{refs}

Wear ALL garment references together as one coherent outfit.
A TOP must be worn as a top, a BOTTOM as a bottom, a JACKET as outerwear,
and FULL means the supplied one-piece/full outfit.

GARMENT LOCK: reproduce each supplied garment faithfully: exact color, silhouette,
length, cut, fabric, texture, print, seams, pockets, buttons, zippers, labels,
cuffs, collars and hems. Do not redesign, invent, omit or duplicate garments.

Use the smallest possible edit region. Preserve realistic layering and occlusion
between garments, hair, hands and arms. Do not add accessories or props.
Return one final edited photograph only."""

def generate_multi(body, cloth_paths, labels, key):
    from google import genai
    from google.genai import types
    kwargs={"response_modalities":["IMAGE"]}
    kwargs["response_format"]={"image":{"aspect_ratio":nearest_aspect(body),"image_size":"2K"}}
    try:
        config=types.GenerateContentConfig(**kwargs)
    except Exception:
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    contents=[combo_prompt(labels), rgb(body)] + [rgb(p) for p in cloth_paths]
    last=None
    for attempt in range(3):
        client=None
        try:
            client=genai.Client(api_key=key)
            r=client.models.generate_content(model=IMAGE_MODEL, contents=contents, config=config)
            im=response_image(r)
            if im is None:
                raise RuntimeError(no_image_reason(r))
            fd,p=tempfile.mkstemp(suffix=".png"); os.close(fd)
            im.convert("RGB").save(p,"PNG")
            q=normalize_to_body(p,body)
            try: os.remove(p)
            except Exception: pass
            return q
        except Exception as e:
            last=e
            if attempt<2: time.sleep(1.5*(attempt+1))
        finally:
            if client is not None:
                try: client.close()
                except Exception: pass
    raise RuntimeError(str(last))

def build_zip(run_dir, outputs, wardrobe):
    run_dir=Path(run_dir)
    (run_dir/"wardrobe.json").write_text(json.dumps(wardrobe,indent=2),encoding="utf-8")
    zp=run_dir/"ALL_THAT_YOU_CAN_WEAR.zip"
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for p in outputs:
            z.write(p,arcname=Path(p).name)
        z.write(run_dir/"wardrobe.json",arcname="wardrobe.json")
    return str(zp)

def wear_it_all(body, files, key):
    if not body:
        raise gr.Error("DROP A BODY FIRST")
    if not files:
        raise gr.Error("DROP CLOTHES FIRST")
    paths=[f if isinstance(f,str) else f.name for f in files]
    key=(key or "").strip() or secret()
    if not key:
        raise gr.Error("ADD YOUR GEMINI API KEY ONCE IN SETUP")
    save_key(key)

    run_dir=OUT_ROOT/time.strftime("%Y%m%d_%H%M%S")
    if run_dir.exists():
        run_dir=OUT_ROOT/f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)%1000:03d}"
    body_copy=copy_png(body,run_dir/"inputs"/"body.png")
    groups={k:[] for k in ("TOP","BOTTOM","JACKET","FULL")}
    wardrobe=[]

    yield [], None, "STARTING • READING YOUR WARDROBE"

    for i,p in enumerate(paths,start=1):
        yield [], None, f"SORTING {i}/{len(paths)}"
        raw=copy_png(p,run_dir/"inputs"/"garments"/f"{i:03d}_{safe_stem(p)}.png")
        cat=classify(raw,key)
        entry={"index":i,"source_name":Path(p).name,"raw":raw,"category":cat}
        wardrobe.append(entry)
        groups[cat].append(entry)

    combos=combinations(groups)
    if not combos:
        raise gr.Error("NO WEARABLE COMBINATION FOUND")

    yield [], None, f"{len(combos)} LOOKS TO MAKE"

    outputs=[]
    failed=[]
    for idx,(entries,labels) in enumerate(combos,start=1):
        yield outputs, None, f"GENERATING {idx}/{len(combos)}"
        temp=None
        try:
            cloths=[e["raw"] for e in entries]
            temp=generate_multi(body_copy,cloths,labels,key)
            slug="__".join(f"{lab}-{safe_stem(e['source_name'])}" for lab,e in zip(labels,entries))
            out=run_dir/f"{idx:03d}_{slug}.png"
            rgb(temp).filter(ImageFilter.UnsharpMask(1.05,70,3)).save(out,"PNG")
            outputs.append(str(out))
        except Exception as e:
            failed.append({"look":idx,"error":str(e)})
        finally:
            if temp:
                try: os.remove(temp)
                except Exception: pass

    wardrobe_doc={
        "created_at":time.strftime("%Y-%m-%d %H:%M:%S"),
        "garments":wardrobe,
        "combinations":len(combos),
        "failed":failed
    }
    zp=build_zip(run_dir,outputs,wardrobe_doc)
    status=f"DONE • {len(outputs)}/{len(combos)} LOOKS • SAVED IN ALL THAT YOU CAN WEAR"
    if failed:
        status += f" • {len(failed)} FAILED"
    yield outputs, zp, status

def last_results():
    runs=sorted([p for p in OUT_ROOT.iterdir() if p.is_dir()], reverse=True)
    if not runs:
        return [], None, "NO PREVIOUS SESSION"
    rd=runs[0]
    outs=sorted(str(p) for p in rd.glob("*.png"))
    zp=rd/"ALL_THAT_YOU_CAN_WEAR.zip"
    return outs, (str(zp) if zp.exists() else None), f"LAST SESSION • {len(outs)} LOOKS"

def logo_uri():
    if LOGO.exists():
        return "data:image/webp;base64,"+base64.b64encode(LOGO.read_bytes()).decode()
    return ""

CSS = r"""
:root{--pink:#ff0b7a;--cream:#efe7d6;--green:#55d51b;--black:#090909}
body,.gradio-container{background:#090909!important;color:#f5f2e9!important;font-family:ui-monospace,SFMono-Regular,Menlo,monospace!important}
.gradio-container{max-width:1180px!important;padding:20px!important}
#shell{background:#111;border:1px solid #333;border-radius:24px;padding:18px;box-shadow:0 18px 50px #0009}
#logo img{max-width:300px;width:100%;border-radius:14px;display:block;margin:auto}
h1,h2,h3{letter-spacing:-.5px!important}
.gradio-container .block{background:#111!important;border-color:#343434!important;border-radius:18px!important}
#bodybox,#clothbox{min-height:310px}
#wear{background:radial-gradient(circle at 34% 28%,#7bf23d,#50ce17 46%,#2e9e0a 100%)!important;color:#050505!important;border:7px solid #101010!important;border-radius:999px!important;width:210px!important;height:210px!important;min-width:210px!important;max-width:210px!important;margin:22px auto!important;font:950 25px/.92 Arial,sans-serif!important;letter-spacing:-1px!important;box-shadow:0 0 0 2px #555,0 0 0 5px #050505,inset 0 7px 14px #ffffff42,inset 0 -10px 20px #164f0a88,0 18px 35px #000b!important}
#wear:hover{transform:scale(1.03)}
#status textarea{font-size:13px!important;letter-spacing:1px!important;text-align:center!important}
#setup{opacity:.78}
footer{display:none!important}
"""

header = f"""
<div id="shell">
  <div id="logo">{('<img src="'+logo_uri()+'">') if logo_uri() else '<h1>DRAG WEAR IRON</h1>'}</div>
  <div style="text-align:center;margin-top:14px;letter-spacing:2px;font-size:11px;color:#aaa">
    BODY → CLOTHES → WEAR IT ALL
  </div>
</div>
"""

with gr.Blocks(title=APP_NAME) as demo:
    gr.HTML(header)

    with gr.Row():
        body=gr.Image(type="filepath",label="1 / BODY",elem_id="bodybox")
        clothes=gr.File(file_count="multiple",file_types=["image"],label="2 / CLOTHES",elem_id="clothbox")

    wear=gr.Button("WEAR\nIT ALL",elem_id="wear")
    status=gr.Textbox(value="READY",label="",interactive=False,elem_id="status")

    gallery=gr.Gallery(columns=4,label="ALL THAT YOU CAN WEAR")
    download=gr.File(label="DOWNLOAD ALL LOOKS")

    last=gr.Button("LAST SESSION")

    with gr.Accordion("SETUP / GEMINI API KEY",open=False,elem_id="setup"):
        key=gr.Textbox(value="",type="password",label="GEMINI API KEY")
        key_status=gr.Textbox(value="",label="",interactive=False)
        check=gr.Button("CHECK CONNECTION")

    key.change(save_key,[key],[key,key_status],queue=False)
    key.submit(save_key,[key],[key,key_status],queue=False)
    check.click(test_key,[key],[key_status],queue=False)
    demo.load(load_key,outputs=[key,key_status],queue=False)

    wear.click(wear_it_all,[body,clothes,key],[gallery,download,status])
    last.click(last_results,[],[gallery,download,status],queue=False)

if __name__=="__main__":
    demo.queue(default_concurrency_limit=1).launch(inbrowser=True,show_error=True,css=CSS)
