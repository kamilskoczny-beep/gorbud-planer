import json,sys,math
sys.path.insert(0,'/home/claude/gorbud-planer/tools/dwg'); import structure as st, wall_continuity as wc
from exterior_walls import footprint_dwg
from shapely.geometry import LineString
ALIGN={'piwnica':[20,300],'parter':[180,220],'pietro1':[0,0],'poddasze':[-20,140]}
FL=list(ALIGN)
it={f:[i for i in json.load(open(f'live59/projekt/{f}.json'))['items'] if i['type']!='beam'] for f in FL}
m=json.load(open('/home/claude/drawsko/model_final.json'))
_P=m['floors']['piwnica']['geo']
for s_ in list(_P.get('dims',[])):
    if s_.get('k')=='l' and any(tuple(p) in {(3100,20621),(3100,23701),(290,20621),(18710,17607),(9703,17607),(9703,24253)} for p in map(tuple,s_['p'])):
        _P['dims'].remove(s_); _P['walls'].append(s_)
R10=lambda v:int(round(v/10.0))*10
log={f:[] for f in FL}
# 0) „to nie okno” → ściana
for f in FL:
    for w in it[f]:
        if w['type']=='iwin' and w.get('qAns') and 'nie okno' in w['qAns'].get('c',''):
            w['type']='iwall'; w['inv']='D'; w['q']='wg Twojej odpowiedzi „to nie okno” – zamieniłem na ścianę (skośny odcinek ściany działowej); potwierdź albo popraw grubość'; w.pop('qAns',None)
            log[f].append(f"okno {w['id']} → ściana (Twoja odpowiedź)")
G={f:st.gap_beams(it[f],f) for f in FL}
S={'poddasze':[]}
for lo,up in [('piwnica','parter'),('parter','pietro1'),('pietro1','poddasze')]:
    raw=st.support_beams(it[up], it[lo]+G[lo], ALIGN[up], ALIGN[lo], lo)
    FPe=footprint_dwg(m['floors'][lo]['geo']).buffer(-400); keep=[]
    for b in raw:
        g=LineString(b['pts']).intersection(FPe)
        parts=[g] if g.geom_type=='LineString' else (list(g.geoms) if hasattr(g,'geoms') else [])
        for k,pp in enumerate(parts):
            if pp.is_empty or pp.length<600: continue
            c=list(pp.coords); nb=dict(b); nb['id']=b['id']+('' if k==0 else f'-{k}'); nb['pts']=[[R10(c[0][0]),R10(c[0][1])],[R10(c[-1][0]),R10(c[-1][1])]]; nb['L']=pp.length; keep.append(nb)
    S[lo]=keep
def par_walls(items, b, maxoff=750, minov=0.5):
    (ax,ay),(bx,by)=b['pts']; L=math.hypot(bx-ax,by-ay) or 1; u=((bx-ax)/L,(by-ay)/L); n=(-u[1],u[0]); out=[]
    for w in items:
        if w['type']!='iwall': continue
        (wa,wb)=w['pts']; wL=math.dist(wa,wb) or 1; wu=((wb[0]-wa[0])/wL,(wb[1]-wa[1])/wL)
        if abs(wu[0]*u[1]-wu[1]*u[0])>0.1: continue
        off=((wa[0]+wb[0])/2-ax)*n[0]+((wa[1]+wb[1])/2-ay)*n[1]
        t0,t1=sorted([(wa[0]-ax)*u[0]+(wa[1]-ay)*u[1],(wb[0]-ax)*u[0]+(wb[1]-ay)*u[1]])
        ov=min(L,t1)-max(0,t0)
        if ov>=minov*L and abs(off)<=maxoff: out.append((abs(off),w,ov))
    return sorted(out,key=lambda x:x[0])
cm=lambda v: f"{round(v/10)} cm"
# ściany usunięte przez użytkownika – w ich miejscu nie stawiamy podciągów ani nie domykamy (to była jego decyzja)
DEL={}
for f in FL:
    old={i['id']:i for i in json.load(open(f'dbF_{f}.json'))['items'] if i['type']=='iwall'}
    cur={i['id'] for i in json.load(open(f'live59/projekt/{f}.json'))['items']}
    DEL[f]=[old[k] for k in old if k not in cur]
from shapely.geometry import LineString as LS
def deleted_here(f,b):
    g=LS(b['pts'])
    return any(LS(w['pts']).buffer(max(w['w'],300)/2+150).intersection(g).length>0.5*g.length for w in DEL[f])
def dup(f,b,acc):
    g=LS(b['pts']).buffer(250)
    return any(g.intersection(LS(o['pts'])).length>0.5*min(LS(o['pts']).length,LS(b['pts']).length) for o in acc)
CH={f:[i for i in it[f] if i['type']=='chimney'] for f in FL}
def on_chimney(f,w):
    xs=[p[0] for p in w['pts']]; ys=[p[1] for p in w['pts']]
    for c in CH[f]:
        (x0,y0),(x1,y1)=c['pts']
        if min(xs)<max(x0,x1)+300 and max(xs)>min(x0,x1)-300 and min(ys)<max(y0,y1)+300 and max(ys)>min(y0,y1)-300: return c
    return None
final={f:[] for f in FL}; nz=0
for f in FL:
    for b in G[f]:
        L=math.dist(*b['pts'])
        if deleted_here(f,b): log[f].append(f"przerwa {cm(L)} tam, gdzie usunąłeś ścianę – zostawiam bez podciągu"); continue
        if L<=450:
            nz+=1; it[f].append({'id':f'inw-s-{f}-z{nz:02d}','type':'iwall','inv':'N','w':b['w'],'pts':b['pts'],'q':f'przerwa {cm(L)} w ścianie nośnej bez drzwi – to wnęka/bruzda albo błąd pomiaru; ściana nośna jest ciągła, więc ją domknąłem. Potwierdź albo napisz, co tu jest.'})
            log[f].append(f'przerwa {cm(L)} w ścianie nośnej – domknięta (wnęka?)'); continue
        if L<=2000:
            b['kind']='nadproze'; b['q']=f'otwór {cm(L)} w ścianie nośnej bez drzwi (przejście) – nad nim musi być nadproże. Potwierdź albo napisz, co tu jest (np. drzwi, ściana).'
        final[f].append(b)
    for b in S[f]:
        up_floor=FL[FL.index(f)+1]; upw=[w for w in it[up_floor] if w['id']==b['above']][0]; upL=math.dist(*upw['pts'])
        if upw['w']>=650 and upL<=3200:
            msg=f"blok {cm(upw['w'])}×{cm(upL)} – to raczej trzon komina niż ściana; na kondygnacji niżej nie ma pod nim ani ściany, ani komina. Komin czy ściana? Jak schodzi niżej?"
            if 'trzon komina' not in (upw.get('q') or ''): upw['q']=(upw['q']+' · ' if upw.get('q') else '')+msg
            log[up_floor].append(f"{upw['id']}: blok {cm(upw['w'])} bez podparcia – pytanie (komin?), bez podciągu"); continue
        pw=par_walls(it[f],b)
        if pw:
            off,lw,ov=pw[0]
            if lw.get('inv')=='D' or lw['w']<upw['w']-100:
                lw['q']=(lw['q']+' · ' if lw.get('q') else '')+f"nad tą ścianą ({cm(lw['w'])}) stoi ściana nośna {cm(upw['w'])} z kondygnacji wyżej (przesunięcie {cm(off)} – błąd pomiaru/tynki) – to ta ściana ją niesie, więc jest nośna i pewnie grubsza. Proponuję nośna {cm(upw['w'])} (potwierdzam = wprowadź)."
                lw['qFix']={'inv':'N','w':upw['w']}
                log[f].append(f"{lw['id']}: pod ścianą nośną z góry – propozycja: nośna {cm(upw['w'])}")
            else:
                log[f].append(f"ściana wyżej przesunięta o {cm(off)} względem {lw['id']} – stoi na niej, bez podciągu")
            continue
        if dup(f,b,final[f]): continue
        chm=on_chimney(up_floor,upw)
        if chm:
            b['q']=f"nad tym miejscem na kondygnacji wyżej stoi komin ({chm.get('label','')}) z obudową {cm(upw['w'])}, a tu nie ma pod nim ściany ani komina – komin stoi na stropie, więc musi być podparty (belki stalowe / wymian, podciąg). Potwierdź albo napisz, jak jest."
            b.pop('L',None); final[f].append(b); continue
        b['q']=f"nad tym miejscem stoi ściana nośna kondygnacji wyżej ({cm(upw['w'])}), a tu nie ma pod nią ściany na długości {cm(b['L'])} – musi być podciąg (albo ściana, której brak w inwentaryzacji). Potwierdź albo napisz, co jest."
        b.pop('L',None); final[f].append(b)
for f in FL:
    it[f]+=final[f]
    _,un=wc.fix(it[f])
    json.dump({'items':it[f]},open(f'db59_{f}.json','w'),ensure_ascii=False)
    nb=sum(1 for b in final[f] if b.get('kind')!='nadproze'); nn=sum(1 for b in final[f] if b.get('kind')=='nadproze')
    print(f,'podciągi',nb,'nadproża',nn,'| końce bez styku',len(un))
    for l in log[f]: print('   ',l)
