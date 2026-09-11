import os,time,zipfile,tempfile,base64
from pathlib import Path
import gradio as gr
from PIL import Image,ImageFilter,ImageOps
from rembg import remove,new_session
import requests,replicate

APP_NAME='DRAG WEAR IRON v0.12'
GEMINI_MODEL='gemini-3-pro-image'
IDM_MODEL='cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985'
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'outputs'; CLEAN=ROOT/'cleaned'; ASSETS=ROOT/'assets'
GEMINI_KEY=ROOT/'.gemini_api_key'; REPLICATE_KEY=ROOT/'.replicate_token'; LOGO=ASSETS/'DRAGWEARIRON_LOGO.png'
WORK.mkdir(exist_ok=True); CLEAN.mkdir(exist_ok=True)
REMBG=None
CSS='''body,.gradio-container{background:#0b0b0b!important;color:#eee!important}.gradio-container{max-width:1360px!important}.brand{display:flex;gap:24px;align-items:center;margin:12px 0 24px}.brand img{width:260px;max-width:38vw}.brand h1{margin:0;font:900 31px Arial;letter-spacing:-1px}.brand p{margin:8px 0 0;color:#aaa;font:12px monospace;line-height:1.5}button.primary{background:#111!important;border:1px solid #ff168d!important;color:white!important}.note{font:11px monospace;color:#999}footer{display:none!important}'''

def secret(path):
    try:return path.read_text().strip()
    except:return ''
def save_secret(path,value):
    value=(value or '').strip()
    if value:
        path.write_text(value)
        try:os.chmod(path,0o600)
        except:pass
    return value
def logo_uri():
    if not LOGO.exists(): return ''
    return 'data:image/png;base64,'+base64.b64encode(LOGO.read_bytes()).decode()
L=logo_uri(); IMG=f'<img src="{L}" alt="DRAG WEAR IRON">' if L else ''
HEADER=f'<div class="brand">{IMG}<div><h1>DRAG WEAR IRON</h1><p>BODY MASTER → GARMENT → NANO BANANA PRO → LOOKS<br>BODY LOCK · GARMENT LOCK · FRAME LOCK · BATCH EXPORT</p></div></div>'

def files_list(files):
    if not files:return []
    return [f if isinstance(f,str) else f.name for f in files]
def rgb(path):
    with Image.open(path) as im:return ImageOps.exif_transpose(im).convert('RGB')
def tmp_jpg(path):
    fd,p=tempfile.mkstemp(suffix='.jpg');os.close(fd);rgb(path).save(p,'JPEG',quality=96,optimize=True);return p
def session():
    global REMBG
    if REMBG is None:REMBG=new_session('u2net')
    return REMBG

def center_focus(im,focus):
    fw,fh={'WIDE':(.92,.96),'TIGHT':(.66,.90)}.get(focus,(.78,.94));w,h=im.size;nw,nh=int(w*fw),int(h*fh);l=(w-nw)//2;t=max(0,int((h-nh)*.35));return im.crop((l,t,l+nw,t+nh))
def clean_one(path,focus='AUTO',padding=70):
    im=center_focus(rgb(path),focus); scale=min(1,1800/max(im.size))
    if scale<1:im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    rgba=remove(im,session=session()).convert('RGBA');a=rgba.getchannel('A').filter(ImageFilter.MedianFilter(3));rgba.putalpha(a);box=a.getbbox()
    if not box:raise RuntimeError('No garment detected')
    obj=rgba.crop(box);cw=max(900,obj.width+padding*2);ch=max(1200,obj.height+padding*2)
    if cw/ch>.75:ch=int(cw/.75)
    else:cw=int(ch*.75)
    canvas=Image.new('RGB',(cw,ch),(245,243,239));canvas.paste(obj,((cw-obj.width)//2,(ch-obj.height)//2),obj)
    out=CLEAN/f'{int(time.time()*1000)}_{Path(path).stem}_clean.jpg';canvas.save(out,'JPEG',quality=97,optimize=True);return str(out)
def clean_batch(files,focus,padding,progress=gr.Progress()):
    ps=files_list(files)
    if not ps:raise gr.Error('Ajoute au moins une photo de vêtement.')
    outs=[]
    for i,p in enumerate(ps):progress((i,len(ps)),desc=f'CLEAN {i+1}/{len(ps)}');outs.append(clean_one(p,focus,int(padding)))
    return outs,f'{len(outs)} CLEAN CLOTH READY'

def prompt_for(category,has_jacket,body_lock,garment_lock,frame_lock,variation,notes):
    if category=='JACKET':task='TASK: LAYERED DRESSING. Put the exact jacket from IMAGE 2 over the clothes already worn in IMAGE 1. Keep all non-jacket garments from IMAGE 1.'
    elif category=='BOTTOM':task='TASK: LOWER GARMENT CHANGE. Replace only the pants/skirt/shorts on IMAGE 1 with IMAGE 2. Keep upper clothing unchanged.'+(' Keep the existing jacket exactly unchanged.' if has_jacket else '')
    elif category=='TOP':task='TASK: UPPER GARMENT CHANGE. Replace only the top/shirt/sweater on IMAGE 1 with IMAGE 2. Keep lower garments unchanged.'+(' Preserve the jacket and place the top underneath it.' if has_jacket else '')
    elif category=='FULL':task='TASK: COMPLETE OUTFIT TRANSFER. Replace the clothing on IMAGE 1 with the exact outfit shown in IMAGE 2.'
    else:task='TASK: AUTOMATIC GARMENT TRANSFER. Infer what garment IMAGE 2 contains and replace only the corresponding clothing region on IMAGE 1.'
    locks=[]
    if body_lock:locks.append('BODY LOCK: IMAGE 1 is immutable. Preserve exact face, identity, hairstyle, body proportions, skin, hands, pose, expression and anatomy.')
    if frame_lock:locks.append('FRAME LOCK: Preserve IMAGE 1 crop, camera, framing, perspective, background, lighting direction and subject placement. Do not zoom or reframe.')
    if garment_lock:locks.append('GARMENT LOCK: IMAGE 2 is immutable. Preserve exact silhouette, length, cut, color, fabric, texture, print, seams, pockets, buttons, zippers, labels and construction details. Do not redesign it.')
    var='VARIATION: MINIMAL. Prioritize reference fidelity and pixel stability. Change only what is necessary.' if variation=='FIDELITY' else 'VARIATION: NATURAL. Keep identity and garment fidelity locked, but allow realistic drape, folds, shadows and lighting integration.'
    extra=f'ADDITIONAL GARMENT NOTES: {notes.strip()}' if (notes or '').strip() else ''
    return f'''Professional high-end fashion catalogue image editing.\n\nIMAGE 1 = BODY MASTER / PERSON / SCENE.\nIMAGE 2 = GARMENT REFERENCE.\n\n{task}\n\n{' '.join(locks)}\n\n{var}\n\n{extra}\n\nFINAL RULES:\n- The final image must still look like the original photograph in IMAGE 1.\n- The person must remain the same person.\n- The garment must remain the same garment from IMAGE 2.\n- No extra people, accessories, text, logos or scene changes unless already present.\n- Photorealistic result, natural fabric physics, clean edges, realistic occlusion and shadows.\n- Return one final edited fashion photograph only.'''

def normalize_to_body(result_path,body_path):
    body=rgb(body_path);result=rgb(result_path);bw,bh=body.size;rw,rh=result.size;br=bw/bh;rr=rw/rh
    if abs(br-rr)/br<.02:result=result.resize((bw,bh),Image.Resampling.LANCZOS)
    else:result=ImageOps.fit(result,(bw,bh),Image.Resampling.LANCZOS,centering=(.5,.5))
    fd,p=tempfile.mkstemp(suffix='.png');os.close(fd);result.save(p,'PNG');return p

def run_gemini(person,cloth,prompt,key,frame_lock=True):
    key=(key or '').strip() or secret(GEMINI_KEY)
    if not key:raise RuntimeError('Gemini API key missing')
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=key)
    response=client.models.generate_content(model=GEMINI_MODEL,contents=[prompt,rgb(person),rgb(cloth)],config=types.GenerateContentConfig(response_modalities=['IMAGE']))
    image=None
    for part in getattr(response,'parts',[]) or []:
        if getattr(part,'inline_data',None) is not None:
            try:image=part.as_image()
            except:image=None
            if image is not None:break
    if image is None:raise RuntimeError('Gemini returned no image')
    fd,p=tempfile.mkstemp(suffix='.png');os.close(fd);image.convert('RGB').save(p,'PNG')
    if frame_lock:
        q=normalize_to_body(p,person)
        try:os.remove(p)
        except:pass
        return q
    return p

def run_idm(person,cloth,category,description,steps,seed,token,preserve):
    token=(token or '').strip() or secret(REPLICATE_KEY)
    if not token:raise RuntimeError('Replicate token missing')
    cat={'TOP':'upper_body','JACKET':'upper_body','BOTTOM':'lower_body','FULL':'dresses','AUTO':'upper_body'}.get(category,'upper_body')
    pj,cj=tmp_jpg(person),tmp_jpg(cloth)
    try:
        with open(pj,'rb') as hf,open(cj,'rb') as gf:
            output=replicate.Client(api_token=token).run(IDM_MODEL,input={'human_img':hf,'garm_img':gf,'garment_des':description or 'exact same garment','category':cat,'crop':not bool(preserve),'steps':int(steps),'seed':int(seed),'force_dc':category=='FULL','mask_only':False})
    finally:
        for p in (pj,cj):
            try:os.remove(p)
            except:pass
    u=output.url if hasattr(output,'url') and isinstance(output.url,str) else (output.url() if hasattr(output,'url') else str(output));r=requests.get(u,timeout=180);r.raise_for_status();fd,p=tempfile.mkstemp(suffix='.jpg');os.close(fd);Path(p).write_bytes(r.content);return p

def test_gemini(key):
    key=(key or '').strip() or secret(GEMINI_KEY)
    if not key:return 'GEMINI KEY REQUIRED'
    try:
        from google import genai
        genai.Client(api_key=key).models.get(model=GEMINI_MODEL);save_secret(GEMINI_KEY,key);return f'ENGINE OK • {GEMINI_MODEL} • KEY SAVED LOCALLY'
    except Exception as e:return 'GEMINI ERROR • '+str(e)
def test_replicate(token):
    token=(token or '').strip() or secret(REPLICATE_KEY)
    if not token:return 'REPLICATE TOKEN REQUIRED'
    try:replicate.Client(api_token=token).models.get('cuuupid/idm-vton');save_secret(REPLICATE_KEY,token);return 'LEGACY ENGINE OK • IDM-VTON READY'
    except Exception as e:return 'REPLICATE ERROR • '+str(e)
def sharpen(path,amount):
    if float(amount)<=0:return path
    im=Image.open(path).convert('RGB').filter(ImageFilter.UnsharpMask(1.05,int(55+float(amount)*45),3));fd,p=tempfile.mkstemp(suffix='.jpg');os.close(fd);im.save(p,'JPEG',quality=97,optimize=True);return p

def generate(person,raw_files,clean_mode,focus,padding,engine,category,has_jacket,body_lock,garment_lock,frame_lock,variation,notes,gkey,rtoken,steps,seed,detail,progress=gr.Progress()):
    if not person:raise gr.Error('Ajoute un BODY.')
    ps=files_list(raw_files)
    if not ps:raise gr.Error('Ajoute au moins un vêtement.')
    if engine=='NANO BANANA PRO':
        if not ((gkey or '').strip() or secret(GEMINI_KEY)):raise gr.Error('Ajoute ta GEMINI API KEY une fois.')
        save_secret(GEMINI_KEY,(gkey or '').strip() or secret(GEMINI_KEY))
    else:
        if not ((rtoken or '').strip() or secret(REPLICATE_KEY)):raise gr.Error('Ajoute ton REPLICATE API TOKEN.')
        save_secret(REPLICATE_KEY,(rtoken or '').strip() or secret(REPLICATE_KEY))
    gs=[clean_one(p,focus,int(padding)) for p in ps] if clean_mode=='CLEAN FIRST' else ps
    rd=WORK/time.strftime('%Y%m%d_%H%M%S');rd.mkdir(parents=True,exist_ok=True);outs=[]
    for i,cloth in enumerate(gs):
        progress((i,len(gs)),desc=f'IRON {i+1}/{len(gs)}')
        prompt=prompt_for(category,has_jacket,body_lock,garment_lock,frame_lock,variation,notes)
        try:temp=run_gemini(person,cloth,prompt,gkey,frame_lock) if engine=='NANO BANANA PRO' else run_idm(person,cloth,category,notes,steps,int(seed),rtoken,frame_lock)
        except Exception as e:raise gr.Error(f'LOOK {i+1} failed: {e}')
        final=sharpen(temp,detail);out=rd/f'{i+1:03d}_{Path(cloth).stem}.png';Image.open(final).convert('RGB').save(out,'PNG');outs.append(str(out))
        for q in {temp,final}:
            try:os.remove(q)
            except:pass
    zp=rd/'DRAG_WEAR_IRON_SEQUENCE.zip'
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in outs:z.write(p,arcname=Path(p).name)
    return outs,str(zp),f'{len(outs)} LOOKS READY • ENGINE: {engine}'

with gr.Blocks(title=APP_NAME) as demo:
    gr.HTML(HEADER)
    with gr.Row():
        with gr.Column():
            gr.Markdown('### 01 / BODY MASTER');person=gr.Image(type='filepath',label='MASTER BODY')
            gr.Markdown('### 02 / GARMENTS');garments=gr.File(file_count='multiple',file_types=['image'],label='DROP GARMENT PHOTOS');clean_mode=gr.Radio(['KEEP ORIGINAL','CLEAN FIRST'],value='KEEP ORIGINAL',label='GARMENT INPUT');focus=gr.Radio(['AUTO','WIDE','TIGHT'],value='AUTO',label='CLEAN FOCUS');padding=gr.Slider(20,180,70,step=10,label='CLEAN PADDING');cb=gr.Button('PREVIEW CLEAN CLOTH');cg=gr.Gallery(columns=3,label='CLEANED GARMENTS');cs=gr.Textbox(label='CLEAN STATUS');cb.click(clean_batch,[garments,focus,padding],[cg,cs])
        with gr.Column():
            gr.Markdown('### 03 / ENGINE');engine=gr.Radio(['NANO BANANA PRO','IDM-VTON LEGACY'],value='NANO BANANA PRO',label='IMAGE ENGINE');gr.HTML('<div class="note">DEFAULT = Gemini 3 Pro Image / Nano Banana Pro. IDM-VTON remains as fallback.</div>');gkey=gr.Textbox(value=secret(GEMINI_KEY),type='password',label='GEMINI API KEY');tg=gr.Button('TEST + SAVE GEMINI KEY');gs=gr.Textbox(label='GEMINI STATUS');tg.click(test_gemini,[gkey],[gs]);rtoken=gr.Textbox(value=secret(REPLICATE_KEY),type='password',label='REPLICATE TOKEN — LEGACY ONLY');tr=gr.Button('TEST REPLICATE LEGACY');rs=gr.Textbox(label='LEGACY STATUS');tr.click(test_replicate,[rtoken],[rs])
        with gr.Column():
            gr.Markdown('### 04 / LOCKS');body_lock=gr.Checkbox(True,label='BODY LOCK — identity / pose / anatomy');garment_lock=gr.Checkbox(True,label='GARMENT LOCK — exact garment');frame_lock=gr.Checkbox(True,label='FRAME LOCK — same crop / background');has_jacket=gr.Checkbox(False,label='BODY already wears a jacket');category=gr.Radio(['AUTO','TOP','JACKET','BOTTOM','FULL'],value='AUTO',label='GARMENT TYPE');variation=gr.Radio(['FIDELITY','NATURAL'],value='FIDELITY',label='VARIATION');notes=gr.Textbox(value='Preserve exact garment color, fabric, cut, seams, pockets, buttons, labels and construction details.',label='GARMENT NOTES');steps=gr.Slider(10,40,30,step=1,label='IDM-VTON STEPS');seed=gr.Number(42,precision=0,label='SEED');detail=gr.Slider(0,2,.35,step=.05,label='FINAL DETAIL / ANTI-BLUR');go=gr.Button('IRON ALL',variant='primary');status=gr.Textbox(label='STATUS')
    gr.Markdown('### 05 / OUTPUT');gallery=gr.Gallery(columns=4,label='LOOKS');zipout=gr.File(label='PNG SEQUENCE')
    go.click(generate,[person,garments,clean_mode,focus,padding,engine,category,has_jacket,body_lock,garment_lock,frame_lock,variation,notes,gkey,rtoken,steps,seed,detail],[gallery,zipout,status])

if __name__=='__main__':demo.queue().launch(inbrowser=True,show_error=True,css=CSS)
