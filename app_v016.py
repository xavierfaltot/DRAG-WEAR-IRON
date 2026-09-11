import os, time, zipfile, tempfile, itertools, base64
from pathlib import Path

import gradio as gr
from PIL import Image
import app as core

APP_NAME = 'DRAG WEAR IRON v0.16 — WEAR IT ALL'
CLASSIFIER_MODEL = 'gemini-2.5-flash'
ROOT = Path(__file__).resolve().parent
ALL_WEAR = ROOT / 'ALL THAT YOU CAN WEAR'
ASSETS = ROOT / 'assets'
LOGO = ASSETS / 'DRAGWEARIRON_LOGO.webp'
ALL_WEAR.mkdir(exist_ok=True)

CSS = '''
:root{--pink:#ff0b7a;--cream:#efe7d6;--green:#55d51b;--black:#090909;--panel:#141414;--line:#373737}
body,.gradio-container{background:#090909!important;color:#f5f2e9!important;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace!important}
.gradio-container{max-width:1500px!important;padding:18px!important}
.brand{display:grid;grid-template-columns:minmax(220px,360px) 1fr;gap:22px;align-items:stretch;margin:2px 0 22px}
.brand-logo{background:#101010;border:1px solid #323232;border-radius:24px;padding:14px;box-shadow:inset 0 0 0 1px #000,0 12px 35px #0008}
.brand-logo img{width:100%;display:block;border-radius:13px}
.brand-copy{position:relative;background:linear-gradient(180deg,#181818,#101010);border:1px solid #383838;border-radius:24px;padding:25px 28px;box-shadow:inset 0 1px #ffffff0c,0 12px 35px #0008;overflow:hidden}
.brand-copy:after{content:'●  NANO BANANA PRO';position:absolute;right:24px;top:24px;color:var(--green);font-size:11px;letter-spacing:2px}
.brand h1{margin:0;font:700 clamp(25px,3vw,46px)/.95 Arial,sans-serif;letter-spacing:-2px;color:#f5f2e9;max-width:700px}
.brand p{margin:16px 0 0;color:#aaa;font:11px/1.65 ui-monospace,SFMono-Regular,monospace;letter-spacing:1.4px;text-transform:uppercase}
.brand .tag{display:inline-block;margin-top:20px;padding:8px 11px;border:1px solid #555;border-radius:7px;background:var(--cream);color:#0b0b0b;font-weight:800;font-size:11px;letter-spacing:1.5px}
.gradio-container .block{background:#111!important;border-color:#343434!important;border-radius:18px!important}
.gradio-container label,.gradio-container .label-wrap{font-family:ui-monospace,SFMono-Regular,monospace!important;letter-spacing:.55px!important}
.gradio-container button{min-height:44px!important;border-radius:10px!important;background:#171717!important;border:1px solid #454545!important;color:#f2eee2!important;font-weight:800!important;letter-spacing:.7px!important;box-shadow:inset 0 1px #ffffff0c!important;transition:transform .12s ease,border-color .12s ease,filter .12s ease!important}
.gradio-container button:hover{transform:translateY(-1px);border-color:#777!important}
button.primary{background:#141414!important;border:1px solid var(--pink)!important;color:#fff!important;box-shadow:inset 0 0 0 1px #ff0b7a22!important}
#wear_it_all{background:radial-gradient(circle at 34% 28%,#7bf23d,#50ce17 45%,#2e9e0a 100%)!important;color:#050505!important;border:7px solid #111!important;border-radius:999px!important;width:188px!important;height:188px!important;min-width:188px!important;max-width:188px!important;font:950 22px/.92 Arial,sans-serif!important;letter-spacing:-.6px!important;box-shadow:0 0 0 2px #555,0 0 0 5px #070707,inset 0 7px 14px #ffffff42,inset 0 -10px 20px #164f0a88,0 18px 35px #000b!important;margin:18px auto 16px!important;text-shadow:0 1px #ffffff55!important}
#wear_it_all:hover{transform:scale(1.035)!important;filter:saturate(1.15) brightness(1.03)!important}
#wear_it_all:active{transform:scale(.985)!important}
#wear_label{text-align:center;color:#aaa;font:10px/1.5 ui-monospace,SFMono-Regular,monospace;letter-spacing:2px;text-transform:uppercase;margin-top:-7px}
.note{font:10px/1.55 ui-monospace,SFMono-Regular,monospace;color:#989898;letter-spacing:.7px}
.retro-strip{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:4px 0 14px}
.retro-chip{padding:7px 9px;border-radius:6px;border:1px solid #3a3a3a;background:#111;color:#aaa;font-size:10px;letter-spacing:1px}
.retro-chip.pink{background:var(--pink);color:#080808;border-color:#ff5fa7;font-weight:900}
.retro-chip.cream{background:var(--cream);color:#101010;border-color:#fff8e8;font-weight:900}
.retro-chip.green{background:var(--green);color:#071006;border-color:#82ee54;font-weight:900}
footer{display:none!important}
@media(max-width:900px){.brand{grid-template-columns:1fr}.brand-logo{max-width:420px}.brand-copy:after{position:static;display:block;margin-bottom:12px}.brand h1{font-size:32px}}
'''

def logo_uri():
    if LOGO.exists():
        return 'data:image/webp;base64,' + base64.b64encode(LOGO.read_bytes()).decode()
    return 'https://github.com/user-attachments/assets/d7342a7e-3cc4-4651-8eda-69229e573ee6'

HEADER = f'''<div class="brand"><div class="brand-logo"><img src="{logo_uri()}" alt="DRAG WEAR IRON"></div><div class="brand-copy"><h1>DRAG WEAR IRON</h1><p>AI CLOTHES ON LIFE<br>BODY MASTER → GARMENTS → NANO BANANA PRO → LOOKS<br>BODY LOCK · GARMENT LOCK · FRAME LOCK · WEAR IT ALL</p><div class="retro-strip"><span class="retro-chip pink">DRAG</span><span class="retro-chip cream">WEAR</span><span class="retro-chip green">IRON</span></div><span class="tag">v0.16 / WEAR IT ALL</span></div></div>'''

def test_gemini(key):
    key=(key or '').strip() or core.secret(core.GEMINI_KEY)
    if not key: return 'GEMINI KEY REQUIRED'
    last=None
    for attempt in range(2):
        client=None
        try:
            from google import genai
            client=genai.Client(api_key=key)
            client.models.get(model=core.GEMINI_MODEL)
            core.save_secret(core.GEMINI_KEY,key)
            return f'● GEMINI READY • {core.GEMINI_MODEL} • KEY SAVED LOCALLY'
        except Exception as e:
            last=e
            time.sleep(.4)
        finally:
            if client is not None:
                try: client.close()
                except Exception: pass
    return 'GEMINI ERROR • '+str(last)

def run_gemini_multi(person, cloths, prompt, key, frame_lock=True):
    key=(key or '').strip() or core.secret(core.GEMINI_KEY)
    if not key: raise RuntimeError('Gemini API key missing')
    from google import genai
    from google.genai import types
    kwargs={'response_modalities':['IMAGE']}
    if frame_lock:
        kwargs['response_format']={'image':{'aspect_ratio':core.nearest_aspect(person),'image_size':'2K'}}
    try: config=types.GenerateContentConfig(**kwargs)
    except Exception: config=types.GenerateContentConfig(response_modalities=['IMAGE'])
    contents=[prompt,core.rgb(person)]+[core.rgb(c) for c in cloths]
    last=None
    for attempt in range(1,core.GEMINI_ATTEMPTS+1):
        client=None
        try:
            client=genai.Client(api_key=key)
            response=client.models.generate_content(model=core.GEMINI_MODEL,contents=contents,config=config)
            image=core.response_image(response)
            if image is None: raise RuntimeError(core.gemini_no_image_reason(response))
            fd,p=tempfile.mkstemp(suffix='.png'); os.close(fd); image.convert('RGB').save(p,'PNG')
            if frame_lock:
                q=core.normalize_to_body(p,person)
                try: os.remove(p)
                except Exception: pass
                return q
            return p
        except Exception as e:
            last=e
            if attempt<core.GEMINI_ATTEMPTS: time.sleep(1.5*attempt)
        finally:
            if client is not None:
                try: client.close()
                except Exception: pass
    raise RuntimeError(f'Gemini failed after {core.GEMINI_ATTEMPTS} attempts: {last}')

def classify_garment(path,key):
    key=(key or '').strip() or core.secret(core.GEMINI_KEY)
    from google import genai
    prompt='''Classify this clothing reference into exactly ONE wearable slot. Reply with only one word: TOP, BOTTOM, JACKET, or FULL. TOP = shirt, tee, blouse, sweater, vest worn as main upper garment. BOTTOM = pants, jeans, shorts, skirt. JACKET = coat, blazer, overshirt, cardigan or outerwear intended as a layer. FULL = dress, jumpsuit, one-piece outfit, or complete coordinated full-body outfit that should be worn as one unit. No explanation.'''
    last=None
    for attempt in range(2):
        client=None
        try:
            client=genai.Client(api_key=key)
            response=client.models.generate_content(model=CLASSIFIER_MODEL,contents=[prompt,core.rgb(path)])
            text=(getattr(response,'text','') or '').upper()
            for cat in ('JACKET','BOTTOM','FULL','TOP'):
                if cat in text: return cat
            return 'TOP'
        except Exception as e:
            last=e
            if attempt==0: time.sleep(.5)
        finally:
            if client is not None:
                try: client.close()
                except Exception: pass
    raise RuntimeError(f'Garment classification failed: {last}')

def wearable_combinations(groups):
    tops,bottoms,jackets,fulls=[groups[k] for k in ('TOP','BOTTOM','JACKET','FULL')]
    bases=[]
    if tops and bottoms: bases += [([t,b],['TOP','BOTTOM']) for t,b in itertools.product(tops,bottoms)]
    elif tops: bases += [([t],['TOP']) for t in tops]
    elif bottoms: bases += [([b],['BOTTOM']) for b in bottoms]
    bases += [([f],['FULL']) for f in fulls]
    combos=[]
    for cloths,labels in bases:
        combos.append((cloths,labels))
        for j in jackets: combos.append((cloths+[j],labels+['JACKET']))
    if not bases: combos += [([j],['JACKET']) for j in jackets]
    return combos

def combo_prompt(labels, body_lock, garment_lock, frame_lock, variation, notes):
    refs='\n'.join(f'IMAGE {i} = {label} GARMENT REFERENCE' for i,label in enumerate(labels,start=2))
    locks=[]
    if body_lock: locks.append('BODY LOCK — ABSOLUTE: keep exact identity, face, hair, expression, hands, proportions, pose and anatomy from IMAGE 1.')
    if frame_lock: locks.append('FRAME LOCK — ABSOLUTE: keep exact crop, camera, background, lighting, scale and placement from IMAGE 1.')
    if garment_lock: locks.append('GARMENT LOCK — ABSOLUTE: reproduce every supplied garment faithfully: exact color, cut, fabric, texture, print, seams, pockets, closures, labels, cuffs, collars and hems.')
    var='Use the smallest possible edit region.' if variation=='FIDELITY' else 'Allow natural folds, drape, tension and shadows while keeping all references faithful.'
    extra=f'Additional notes: {(notes or "").strip()}' if (notes or '').strip() else ''
    return f'''Create ONE complete wearable outfit on the person in IMAGE 1 using ALL supplied garment references together.\n\nIMAGE 1 = BODY MASTER / CAMERA / BACKGROUND.\n{refs}\n\nEach garment reference has already been classified. Combine them as a coherent outfit without omitting, duplicating, swapping, redesigning or inventing garments. A TOP must be worn as a top, a BOTTOM as a bottom, a JACKET as outerwear, and FULL means the complete one-piece garment.\n\n{' '.join(locks)}\n{var}\n{extra}\n\nPreserve realistic layering and occlusion between garments, hair, hands and arms. Do not add accessories or props. Return one final photorealistic fashion photograph only.'''

def build_wear_zip(manifest):
    rd=Path(manifest['run_dir']); zp=rd/'ALL_THAT_YOU_CAN_WEAR.zip'
    outputs=[i.get('output') for i in manifest['items'] if i.get('output') and Path(i['output']).exists()]
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in outputs: z.write(p,arcname=Path(p).name)
        if (rd/'wardrobe.json').exists(): z.write(rd/'wardrobe.json',arcname='wardrobe.json')
        if (rd/'session.json').exists(): z.write(rd/'session.json',arcname='session.json')
    return str(zp),outputs

def wear_it_all(person, raw_files, clean_mode, focus, padding, body_lock, garment_lock, frame_lock, variation, notes, gkey, detail, progress=gr.Progress()):
    if not person: raise gr.Error('Ajoute un BODY.')
    ps=core.files_list(raw_files)
    if not ps: raise gr.Error('Ajoute au moins un vêtement.')
    key=(gkey or '').strip() or core.secret(core.GEMINI_KEY)
    if not key: raise gr.Error('Ajoute ta GEMINI API KEY une fois.')
    core.save_secret(core.GEMINI_KEY,key)
    rd=ALL_WEAR/time.strftime('%Y%m%d_%H%M%S')
    if rd.exists(): rd=ALL_WEAR/f"{time.strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)%1000:03d}"
    raw_dir,clean_dir=rd/'inputs'/'garments',rd/'inputs'/'cleaned'
    body_path=core.save_input_copy(person,rd/'inputs'/'body.png')
    groups={k:[] for k in ('TOP','BOTTOM','JACKET','FULL')}; wardrobe=[]
    for i,p in enumerate(ps,start=1):
        progress((i-1,max(1,len(ps))),desc=f'SORT WEAR {i}/{len(ps)}')
        raw_copy=core.save_input_copy(p,raw_dir/f'{i:03d}_{core.safe_stem(p)}.png')
        cat=classify_garment(raw_copy,key); cloth=raw_copy; clean_error=None
        if clean_mode=='CLEAN FIRST':
            try: cloth=core.clean_one(raw_copy,focus,int(padding),clean_dir)
            except Exception as e: clean_error=str(e)
        entry={'index':i,'source_name':Path(p).name,'raw':raw_copy,'cloth':cloth,'category':cat,'clean_error':clean_error}
        wardrobe.append(entry)
        if not clean_error: groups[cat].append(entry)
    combos=wearable_combinations(groups)
    if not combos: raise gr.Error('Aucune combinaison portable détectée.')
    core.write_json(rd/'wardrobe.json',{'created_at':time.strftime('%Y-%m-%d %H:%M:%S'),'garments':wardrobe,'combination_count':len(combos)})
    cfg={'engine':'NANO BANANA PRO','body_lock':bool(body_lock),'garment_lock':bool(garment_lock),'frame_lock':bool(frame_lock),'variation':variation,'notes':notes or '','detail':float(detail),'clean_mode':clean_mode,'focus':focus,'padding':int(padding)}
    manifest={'version':'0.16','mode':'wear_it_all','created_at':time.strftime('%Y-%m-%d %H:%M:%S'),'run_dir':str(rd),'body':body_path,'config':cfg,'wardrobe':wardrobe,'items':[]}
    for idx,(entries,labels) in enumerate(combos,start=1):
        manifest['items'].append({'index':idx,'source_name':' + '.join(e['source_name'] for e in entries),'cloths':[e['cloth'] for e in entries],'labels':labels,'output':None,'error':None})
    manifest_path=core.persist_manifest(manifest)
    for i,item in enumerate(manifest['items']):
        progress((i,len(manifest['items'])),desc=f'WEAR IT ALL {i+1}/{len(manifest["items"])}')
        temp=final=None
        try:
            temp=run_gemini_multi(body_path,item['cloths'],combo_prompt(item['labels'],cfg['body_lock'],cfg['garment_lock'],cfg['frame_lock'],cfg['variation'],cfg['notes']),key,cfg['frame_lock'])
            final=core.sharpen(temp,cfg['detail'])
            slug='__'.join(f'{lab}-{core.safe_stem(p)}' for lab,p in zip(item['labels'],item['cloths']))
            out=rd/f'{item["index"]:03d}_{slug}.png'; Image.open(final).convert('RGB').save(out,'PNG'); item['output']=str(out); item['error']=None
        except Exception as e: item['error']=str(e)
        finally:
            for q in {temp,final}:
                if q:
                    try:
                        if Path(q).exists() and not str(q).startswith(str(rd)): os.remove(q)
                    except Exception: pass
            core.persist_manifest(manifest)
    zp,outs=build_wear_zip(manifest)
    counts=', '.join(f'{k}:{len(groups[k])}' for k in ('TOP','BOTTOM','JACKET','FULL'))
    failed=sum(1 for i in manifest['items'] if i.get('error'))
    status=f'WEAR IT ALL • {len(outs)}/{len(combos)} LOOKS • {counts} • FOLDER: {rd}'
    if failed: status+=f' • {failed} FAILED'
    return outs,zp,status,manifest_path

def regenerate_one(look_number,manifest_path,gkey,rtoken):
    if not manifest_path or not Path(manifest_path).exists(): return core.regenerate_one(look_number,manifest_path,gkey,rtoken)
    manifest=core.read_json(manifest_path)
    if manifest.get('mode')!='wear_it_all': return core.regenerate_one(look_number,manifest_path,gkey,rtoken)
    try: idx=int(look_number)
    except Exception: raise gr.Error('LOOK # doit être un nombre.')
    items=manifest.get('items',[])
    if idx<1 or idx>len(items): raise gr.Error(f'LOOK # doit être entre 1 et {len(items)}.')
    cfg=manifest['config']; item=items[idx-1]; key=(gkey or '').strip() or core.secret(core.GEMINI_KEY); temp=final=None
    try:
        temp=run_gemini_multi(manifest['body'],item['cloths'],combo_prompt(item['labels'],cfg['body_lock'],cfg['garment_lock'],cfg['frame_lock'],cfg['variation'],cfg['notes']),key,cfg['frame_lock'])
        final=core.sharpen(temp,cfg.get('detail',.35)); slug='__'.join(f'{lab}-{core.safe_stem(p)}' for lab,p in zip(item['labels'],item['cloths'])); out=Path(manifest['run_dir'])/f'{idx:03d}_{slug}.png'; Image.open(final).convert('RGB').save(out,'PNG'); item['output']=str(out); item['error']=None
    except Exception as e: item['error']=str(e); core.persist_manifest(manifest); raise gr.Error(f'LOOK {idx} failed: {e}')
    finally:
        for q in {temp,final}:
            if q:
                try:
                    if Path(q).exists() and not str(q).startswith(str(manifest['run_dir'])): os.remove(q)
                except Exception: pass
    core.persist_manifest(manifest); zp,outs=build_wear_zip(manifest); return outs,zp,f'LOOK {idx} REGENERATED • {len(outs)}/{len(items)} READY',manifest_path

def restore_last_session():
    if not core.LAST_SESSION.exists(): raise gr.Error('Aucune session sauvegardée.')
    mp=core.read_json(core.LAST_SESSION).get('manifest')
    if not mp or not Path(mp).exists(): raise gr.Error('La dernière session n’existe plus sur ce Mac.')
    manifest=core.read_json(mp)
    if manifest.get('mode')!='wear_it_all': return core.restore_last_session()
    raw_files=[g['raw'] for g in manifest.get('wardrobe',[]) if Path(g.get('raw','')).exists()]
    zp,outs=build_wear_zip(manifest); failed=sum(1 for i in manifest['items'] if i.get('error')); status=f'LAST WEAR IT ALL SESSION • {len(outs)}/{len(manifest["items"])} READY'
    if failed: status+=f' • {failed} FAILED'
    return manifest['body'],raw_files,outs,zp,status,mp

with gr.Blocks(title=APP_NAME) as demo:
    gr.HTML(HEADER); manifest_state=gr.State(value='')
    with gr.Row():
        with gr.Column():
            gr.Markdown('### 01 / BODY MASTER'); person=gr.Image(type='filepath',label='MASTER BODY')
            gr.Markdown('### 02 / GARMENTS'); garments=gr.File(file_count='multiple',file_types=['image'],label='DROP GARMENT PHOTOS')
            clean_mode=gr.Radio(['KEEP ORIGINAL','CLEAN FIRST'],value='KEEP ORIGINAL',label='GARMENT INPUT'); focus=gr.Radio(['AUTO','WIDE','TIGHT'],value='AUTO',label='CLEAN FOCUS'); padding=gr.Slider(20,180,70,step=10,label='CLEAN PADDING'); cb=gr.Button('PREVIEW CLEAN CLOTH'); cg=gr.Gallery(columns=3,label='CLEANED GARMENTS'); cs=gr.Textbox(label='CLEAN STATUS'); cb.click(core.clean_batch,[garments,focus,padding],[cg,cs])
        with gr.Column():
            gr.Markdown('### 03 / ENGINE'); engine=gr.Radio(['NANO BANANA PRO','IDM-VTON LEGACY'],value='NANO BANANA PRO',label='IMAGE ENGINE'); gr.HTML('<div class="note">WEAR IT ALL = Nano Banana Pro + automatic TOP / BOTTOM / JACKET / FULL sorting.</div>'); gkey=gr.Textbox(value=core.secret(core.GEMINI_KEY),type='password',label='GEMINI API KEY'); tg=gr.Button('TEST + SAVE GEMINI KEY'); gs=gr.Textbox(label='GEMINI STATUS'); tg.click(test_gemini,[gkey],[gs]); rtoken=gr.Textbox(value=core.secret(core.REPLICATE_KEY),type='password',label='REPLICATE TOKEN — LEGACY ONLY'); tr=gr.Button('TEST REPLICATE LEGACY'); rs=gr.Textbox(label='LEGACY STATUS'); tr.click(core.test_replicate,[rtoken],[rs])
        with gr.Column():
            gr.Markdown('### 04 / LOCKS'); body_lock=gr.Checkbox(True,label='BODY LOCK — identity / pose / anatomy'); garment_lock=gr.Checkbox(True,label='GARMENT LOCK — exact garment'); frame_lock=gr.Checkbox(True,label='FRAME LOCK — same crop / background'); has_jacket=gr.Checkbox(False,label='BODY already wears a jacket'); category=gr.Radio(['AUTO','TOP','JACKET','BOTTOM','FULL'],value='AUTO',label='GARMENT TYPE'); variation=gr.Radio(['FIDELITY','NATURAL'],value='FIDELITY',label='VARIATION'); notes=gr.Textbox(value='Preserve exact garment color, fabric, cut, seams, pockets, buttons, labels and construction details.',label='GARMENT NOTES'); steps=gr.Slider(10,40,30,step=1,label='IDM-VTON STEPS'); seed=gr.Number(42,precision=0,label='SEED'); detail=gr.Slider(0,2,.35,step=.05,label='FINAL DETAIL / ANTI-BLUR'); go=gr.Button('IRON ALL',variant='primary'); wear_all=gr.Button('WEAR\nIT ALL',elem_id='wear_it_all'); gr.HTML('<div id="wear_label">ALL POSSIBLE LOOKS · ONE BUTTON</div>'); restore=gr.Button('RESTORE LAST SESSION'); status=gr.Textbox(label='STATUS')
    gr.Markdown('### 05 / OUTPUT'); gallery=gr.Gallery(columns=4,label='LOOKS'); zipout=gr.File(label='PNG SEQUENCE / ALL THAT YOU CAN WEAR')
    gr.Markdown('### 06 / RETRY')
    with gr.Row(): look_number=gr.Number(1,precision=0,label='LOOK #'); retry=gr.Button('REGENERATE ONE LOOK',variant='primary')
    go.click(core.generate,[person,garments,clean_mode,focus,padding,engine,category,has_jacket,body_lock,garment_lock,frame_lock,variation,notes,gkey,rtoken,steps,seed,detail],[gallery,zipout,status,manifest_state])
    wear_all.click(wear_it_all,[person,garments,clean_mode,focus,padding,body_lock,garment_lock,frame_lock,variation,notes,gkey,detail],[gallery,zipout,status,manifest_state])
    retry.click(regenerate_one,[look_number,manifest_state,gkey,rtoken],[gallery,zipout,status,manifest_state])
    restore.click(restore_last_session,[],[person,garments,gallery,zipout,status,manifest_state])

if __name__=='__main__': demo.queue().launch(inbrowser=True,show_error=True,css=CSS)
