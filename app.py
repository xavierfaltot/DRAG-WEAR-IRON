import os, time, zipfile, tempfile
from pathlib import Path
import gradio as gr
from PIL import Image, ImageFilter, ImageOps
from rembg import remove, new_session
import numpy as np
import requests
import replicate

APP_NAME = "DRAG WEAR IRON"
MODEL_VERSION = "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985"
ROOT = Path(__file__).resolve().parent
WORK = ROOT / "outputs"
CLEAN_DIR = ROOT / "cleaned"
TOKEN_FILE = ROOT / ".replicate_token"
WORK.mkdir(exist_ok=True); CLEAN_DIR.mkdir(exist_ok=True)
REMBG_SESSION = None

CSS = """
body,.gradio-container{background:#0b0b0b!important;color:#eee!important}.gradio-container{max-width:1320px!important}
.brand{margin:12px 0 24px}.brand h1{margin:0;font:900 34px Arial;letter-spacing:-1px}.brand p{color:#aaa;font:12px monospace;line-height:1.5}
button.primary{background:#111!important;border:1px solid #ff168d!important;color:white!important}.help{color:#999;font:11px monospace}footer{display:none!important}
"""
HEADER = '<div class="brand"><h1>DRAG WEAR IRON</h1><p>BODY → CLEAN CLOTH → TRY ON → PNG SEQUENCE<br>SAME PERSON · SAME FRAME · CLOTHES CHANGE</p></div>'

def saved_token():
    try: return TOKEN_FILE.read_text().strip()
    except: return ""

def save_token(t):
    t=(t or "").strip()
    if t:
        TOKEN_FILE.write_text(t)
        try: os.chmod(TOKEN_FILE,0o600)
        except: pass
    return t

def session():
    global REMBG_SESSION
    if REMBG_SESSION is None: REMBG_SESSION=new_session("u2net")
    return REMBG_SESSION

def files_list(files):
    if not files: return []
    return [f if isinstance(f,str) else f.name for f in files]

def rgb(path):
    with Image.open(path) as im: return ImageOps.exif_transpose(im).convert("RGB")

def tmp_jpg(path):
    im=rgb(path); fd,p=tempfile.mkstemp(suffix=".jpg"); os.close(fd); im.save(p,"JPEG",quality=96); return p

def center_focus(im, focus):
    fw,fh={"WIDE":(.92,.96),"TIGHT":(.66,.90)}.get(focus,(.78,.94)); w,h=im.size; nw,nh=int(w*fw),int(h*fh)
    l=(w-nw)//2; t=max(0,int((h-nh)*.35)); return im.crop((l,t,l+nw,t+nh))

def clean_one(path,focus="AUTO",padding=70):
    im=center_focus(rgb(path),focus)
    scale=min(1,1400/max(im.size))
    if scale<1: im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    rgba=remove(im,session=session()).convert("RGBA"); a=rgba.getchannel("A").filter(ImageFilter.MedianFilter(3)); rgba.putalpha(a); box=a.getbbox()
    if not box: raise RuntimeError("No garment detected")
    obj=rgba.crop(box); cw=max(768,obj.width+padding*2); ch=max(1024,obj.height+padding*2)
    if cw/ch>0.75: ch=int(cw/.75)
    else: cw=int(ch*.75)
    canvas=Image.new("RGB",(cw,ch),(245,243,239)); canvas.paste(obj,((cw-obj.width)//2,(ch-obj.height)//2),obj)
    out=CLEAN_DIR/f"{int(time.time()*1000)}_{Path(path).stem}_clean.jpg"; canvas.save(out,"JPEG",quality=96); return str(out)

def clean_batch(files,focus,padding,progress=gr.Progress()):
    ps=files_list(files)
    if not ps: raise gr.Error("Ajoute des vêtements")
    out=[]
    for i,p in enumerate(ps): progress((i,len(ps)),desc=f"CLEAN {i+1}/{len(ps)}"); out.append(clean_one(p,focus,int(padding)))
    return out,f"{len(out)} CLEAN CLOTH READY"

def auto_type(path):
    im=rgb(path); rgba=remove(im,session=session()).convert("RGBA"); a=rgba.getchannel("A"); box=a.getbbox()
    if not box: return "UPPER",0
    a=a.crop(box).resize((160,220),Image.Resampling.LANCZOS); m=np.asarray(a)>80; h,w=m.shape
    if not m.sum(): return "UPPER",0
    rows=m.sum(1)/w; lower=m[int(h*.48):]; center=lower[:,int(w*.43):int(w*.57)]; sides=lower[:,:int(w*.38)].sum(1)+lower[:,int(w*.62):].sum(1)
    split=((sides>w*.16)&(center.sum(1)<max(1,center.shape[1]*.12))).mean(); ys,xs=np.where(m); ratio=(ys.max()-ys.min()+1)/max(1,xs.max()-xs.min()+1); bottom=rows[int(h*.68):int(h*.92)].mean()
    if split>.18 and ratio>1.05: return "LOWER",min(.99,.65+split)
    if ratio>1.45 and bottom>.20: return "DRESS",min(.95,.60+min(.35,(ratio-1.45)*.25))
    return "UPPER",.78

def cat_map(cat): return {"UPPER":"upper_body","LOWER":"lower_body","DRESS":"dresses"}.get(cat,"upper_body")

def test_engine(token):
    token=(token or "").strip() or saved_token()
    if not token: return "TOKEN REQUIRED"
    try:
        replicate.Client(api_token=token).models.get("cuuupid/idm-vton"); save_token(token); return "ENGINE OK · TOKEN SAVED LOCALLY"
    except Exception as e: return "ENGINE ERROR · "+str(e)

def tryon(person,cloth,cat,description,steps,seed,token,preserve):
    token=(token or "").strip() or saved_token()
    if not token: raise RuntimeError("Replicate token missing")
    pj,cj=tmp_jpg(person),tmp_jpg(cloth)
    try:
        with open(pj,"rb") as hf, open(cj,"rb") as gf:
            output=replicate.Client(api_token=token).run(MODEL_VERSION,input={"human_img":hf,"garm_img":gf,"garment_des":description or "exact same garment","category":cat_map(cat),"crop":not bool(preserve),"steps":int(steps),"seed":int(seed),"force_dc":cat=="DRESS","mask_only":False})
    finally:
        for p in (pj,cj):
            try: os.remove(p)
            except: pass
    if hasattr(output,"url"): u=output.url if isinstance(output.url,str) else output.url()
    else: u=str(output)
    r=requests.get(u,timeout=180); r.raise_for_status(); fd,p=tempfile.mkstemp(suffix=".jpg"); os.close(fd); Path(p).write_bytes(r.content); return p

def sharpen(path,amount):
    if float(amount)<=0: return path
    im=Image.open(path).convert("RGB").filter(ImageFilter.UnsharpMask(1.15,int(70+float(amount)*55),3)); fd,p=tempfile.mkstemp(suffix=".jpg"); os.close(fd); im.save(p,"JPEG",quality=97); return p

def generate(person,raw_files,clean_mode,focus,padding,category,description,steps,seed,token,preserve,detail,progress=gr.Progress()):
    if not person: raise gr.Error("Ajoute un BODY")
    ps=files_list(raw_files)
    if not ps: raise gr.Error("Ajoute des vêtements")
    token=save_token((token or "").strip() or saved_token())
    if not token: raise gr.Error("Replicate token missing")
    gs=[clean_one(p,focus,int(padding)) for p in ps] if clean_mode=="CLEAN FIRST" else ps
    rd=WORK/time.strftime("%Y%m%d_%H%M%S"); rd.mkdir(parents=True,exist_ok=True); outs=[]; cats=[]
    for i,c in enumerate(gs):
        cat=category
        if category=="AUTO": cat,conf=auto_type(c); cats.append(f"{Path(ps[i]).name}: {cat} {conf:.0%}")
        else: cats.append(f"{Path(ps[i]).name}: {cat}")
        progress((i,len(gs)),desc=f"IRON {i+1}/{len(gs)} · {cat}")
        temp=tryon(person,c,cat,description,steps,int(seed)+i,token,preserve); final=sharpen(temp,detail); out=rd/f"{i+1:03d}_{Path(c).stem}.png"; Image.open(final).convert("RGB").save(out); outs.append(str(out))
        for q in set([temp,final]):
            try: os.remove(q)
            except: pass
    z=rd/"DRAG_WEAR_IRON_SEQUENCE.zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zz:
        for p in outs: zz.write(p,arcname=Path(p).name)
    return outs,str(z),"\n".join(cats)+f"\n{len(outs)} LOOKS READY"

with gr.Blocks(title=APP_NAME) as demo:
    gr.HTML(HEADER)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 01 / BODY"); person=gr.Image(type="filepath",label="MASTER BODY")
            gr.Markdown("### 02 / SHOP PHOTOS"); garments=gr.File(file_count="multiple",file_types=["image"],label="DROP GARMENTS"); clean_mode=gr.Radio(["CLEAN FIRST","KEEP ORIGINAL"],value="CLEAN FIRST",label="CLOTH PREP")
        with gr.Column():
            gr.Markdown("### 03 / CLEAN CLOTH"); focus=gr.Radio(["AUTO","WIDE","TIGHT"],value="AUTO",label="CENTER FOCUS"); padding=gr.Slider(20,180,70,step=10,label="CATALOGUE PADDING"); cb=gr.Button("PREVIEW CLEAN CLOTH"); cg=gr.Gallery(columns=3,label="CLEANED GARMENTS"); cs=gr.Textbox(label="CLEAN STATUS"); cb.click(clean_batch,[garments,focus,padding],[cg,cs])
        with gr.Column():
            gr.Markdown("### 04 / TRY ON"); token=gr.Textbox(value=saved_token(),type="password",label="REPLICATE API TOKEN"); test=gr.Button("TEST + SAVE TOKEN"); engine=gr.Textbox(label="ENGINE STATUS"); test.click(test_engine,[token],[engine])
            category=gr.Radio(["AUTO","UPPER","LOWER","DRESS"],value="AUTO",label="CATEGORY · AUTO = EACH GARMENT")
            description=gr.Textbox(value="exact same garment, preserve original color, fabric, cut, seams, pockets, buttons and details",label="GARMENT DESCRIPTION")
            preserve=gr.Checkbox(value=True,label="PRESERVE BODY FRAME / CROP")
            steps=gr.Slider(10,40,30,step=1,label="STEPS")
            detail=gr.Slider(0,2,.65,step=.05,label="FINAL DETAIL / ANTI-BLUR")
            seed=gr.Number(value=42,precision=0,label="SEED")
            go=gr.Button("IRON ALL",variant="primary"); status=gr.Textbox(label="STATUS")
    gr.Markdown("### 05 / OUTPUT"); gallery=gr.Gallery(columns=4,label="LOOKS"); zipout=gr.File(label="PNG SEQUENCE")
    go.click(generate,[person,garments,clean_mode,focus,padding,category,description,steps,seed,token,preserve,detail],[gallery,zipout,status])

if __name__=="__main__": demo.queue().launch(inbrowser=True,show_error=True,css=CSS)
