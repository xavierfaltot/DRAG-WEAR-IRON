import os, re, time, zipfile, tempfile
from pathlib import Path
import gradio as gr
from PIL import Image
from gradio_client import Client, handle_file

APP_NAME="DRAG WEAR TOOL"
DEFAULT_SPACE="zhengchong/CatVTON"
WORK=Path("outputs"); WORK.mkdir(exist_ok=True)

CSS="""
body,.gradio-container{background:#0a0a0a!important;color:#eee!important}
.gradio-container{max-width:1280px!important}
.logo{display:grid;grid-template-columns:repeat(4,54px);width:max-content}
.logo span{width:54px;height:54px;display:flex;align-items:center;justify-content:center;background:#b9a98d;color:#0a0a0a;font:900 34px Impact,Arial Black;border:1px solid #111}
.logo .r{background:#b80000}
.brand{display:flex;gap:24px;align-items:center;margin:10px 0 24px}
.brand h1{margin:0;font:900 30px Arial}
.brand p{margin:8px 0 0;color:#aaa;font:12px monospace}
button.primary{background:#b80000!important}
footer{display:none!important}
"""

HEADER="""
<div class="brand">
<div class="logo">
<span>D</span><span>R</span><span>A</span><span>G</span>
<span class="r">W</span><span class="r">E</span><span class="r">A</span><span class="r">R</span>
<span>T</span><span>O</span><span>O</span><span>L</span>
</div>
<div><h1>DRAG WEAR TOOL</h1><p>ONE BODY → MANY CLOTHES → LOCKED POSE → ANIMATION READY</p></div>
</div>
"""

def auto_cat(name):
    n=name.lower()
    if any(k in n for k in ["dress","robe","overall","jumpsuit"]): return "overall"
    if any(k in n for k in ["skirt","jupe","pant","trouser","jean","short"]): return "lower"
    return "upper"

def api_name(client):
    try:
        d=client.view_api(return_format="dict")
        for k,v in d.get("named_endpoints",{}).items():
            if len(v.get("parameters",[]))==7: return k
    except: pass
    return "/submit_function"

def result_path(x):
    if isinstance(x,str) and os.path.exists(x): return x
    if isinstance(x,dict):
        for k in ("path","name"):
            if x.get(k) and os.path.exists(x[k]): return x[k]
    if isinstance(x,(list,tuple)):
        for i in x:
            p=result_path(i)
            if p: return p
    return None

def call_tryon(person, cloth, cat, steps, cfg, seed, space, token):
    c=Client(space or DEFAULT_SPACE, token=token or None)
    im=Image.open(person).convert("RGB")
    fd,mask=tempfile.mkstemp(suffix=".png"); os.close(fd)
    Image.new("L",im.size,0).save(mask)
    editor={"background":handle_file(person),"layers":[handle_file(mask)],"composite":None}
    try:
        r=c.predict(editor, handle_file(cloth), cat, int(steps), float(cfg), int(seed), "result only", api_name=api_name(c))
    finally:
        try: os.remove(mask)
        except: pass
    p=result_path(r)
    if not p: raise RuntimeError("Unsupported result from backend.")
    return p

def preview(paths,out,fps):
    try:
        import imageio.v3 as iio
        frames=[]; size=None
        for p in paths:
            im=Image.open(p).convert("RGB")
            if size is None:size=im.size
            if im.size!=size:im=im.resize(size,Image.Resampling.LANCZOS)
            frames += [im]*max(1,round(fps*.7))
        iio.imwrite(out,frames,fps=fps,codec="libx264",pixelformat="yuv420p")
        return str(out)
    except: return None

def run_all(person, garments, category, steps, cfg, seed, space, token, fps, progress=gr.Progress()):
    if not person: raise gr.Error("Drop one BODY image.")
    if not garments: raise gr.Error("Drop garment images.")
    rd=WORK/time.strftime("%Y%m%d_%H%M%S"); rd.mkdir(parents=True,exist_ok=True)
    outs=[]
    paths=[g if isinstance(g,str) else g.name for g in garments]
    for i,cloth in enumerate(paths):
        progress((i,len(paths)),desc=f"LOOK {i+1}/{len(paths)}")
        cat=auto_cat(cloth) if category=="AUTO" else category.lower()
        p=call_tryon(person,cloth,cat,steps,cfg,seed+i,space,token)
        out=rd/f"{i+1:03d}_{Path(cloth).stem}.png"
        Image.open(p).convert("RGB").save(out)
        outs.append(str(out))
    zp=rd/"DRAG_WEAR_SEQUENCE.zip"
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for p in outs:z.write(p,arcname=Path(p).name)
    mp4=preview(outs,rd/"DRAG_WEAR_PREVIEW.mp4",int(fps))
    return outs,str(zp),mp4,f"{len(outs)} LOOKS READY"

with gr.Blocks(title=APP_NAME,css=CSS) as demo:
    gr.HTML(HEADER)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 01 / BODY")
            person=gr.Image(type="filepath",label="MASTER BODY")
            gr.Markdown("### 02 / CLOTHES")
            garments=gr.File(file_count="multiple",file_types=["image"],label="DROP ALL GARMENTS")
        with gr.Column():
            gr.Markdown("### 03 / GENERATION")
            category=gr.Radio(["AUTO","UPPER","LOWER","OVERALL"],value="AUTO",label="CATEGORY")
            with gr.Accordion("ENGINE",open=False):
                space=gr.Textbox(value=DEFAULT_SPACE,label="HF / Gradio Space")
                token=gr.Textbox(type="password",label="HF TOKEN (optional)")
                gr.Markdown("Default CatVTON backend is for **non-commercial prototyping only**.")
            with gr.Accordion("CONTROL",open=False):
                steps=gr.Slider(10,100,50,step=5,label="STEPS")
                cfg=gr.Slider(0,7.5,2.5,step=.5,label="CFG")
                seed=gr.Number(value=42,precision=0,label="SEED")
                fps=gr.Slider(1,24,12,step=1,label="PREVIEW FPS")
            go=gr.Button("GENERATE ALL",variant="primary")
            status=gr.Textbox(label="STATUS")
    gr.Markdown("### 04 / OUTPUT")
    gallery=gr.Gallery(columns=4,label="LOOKS")
    with gr.Row():
        zipout=gr.File(label="PNG SEQUENCE")
        video=gr.Video(label="ANIMATION PREVIEW")
    go.click(run_all,[person,garments,category,steps,cfg,seed,space,token,fps],[gallery,zipout,video,status])

if __name__=="__main__":
    demo.queue().launch(inbrowser=True)
