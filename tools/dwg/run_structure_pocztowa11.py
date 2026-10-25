import json,sys,copy
sys.path.insert(0,'/home/claude/gorbud-planer/tools/dwg'); import structure as st, wall_continuity as wc
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
ALIGN={'piwnica':[20,300],'parter':[180,220],'pietro1':[0,0],'poddasze':[-20,140]}
FL=['piwnica','parter','pietro1','poddasze']
it={f:json.load(open(f'live57/projekt/{f}.json'))['items'] for f in FL}
log=[]
for f in FL:
    rot,rem=st.fix_short_fat(it[f]); log.append(f'{f}: ściany odczytane w poprzek obrócone {len(rot)}, fałszywe (ościeża otworów) usunięte {len(rem)}')
    ch=st.straighten(it[f]); log.append(f'{f}: wyprostowane ściany nośne {len(ch)} (maks. przesunięcie {max([abs(c[1]) for c in ch] or [0])} mm)')
    wc.fix(it[f]); wc.trim_to_faces(it[f])
G={f:st.gap_beams(it[f],f) for f in FL}
S={}
for lo,up in [('piwnica','parter'),('parter','pietro1'),('pietro1','poddasze')]:
    S[lo]=st.support_beams(it[up], it[lo]+G[lo], ALIGN[up], ALIGN[lo], lo)
S['poddasze']=[]
from exterior_walls import footprint_dwg
from shapely.geometry import LineString
m=json.load(open('/home/claude/drawsko/model_final.json'))
_P=m['floors']['piwnica']['geo']
for s_ in list(_P.get('dims',[])):
    if s_.get('k')=='l' and any(tuple(p) in {(3100,20621),(3100,23701),(290,20621),(18710,17607),(9703,17607),(9703,24253)} for p in map(tuple,s_['p'])):
        _P['dims'].remove(s_); _P['walls'].append(s_)
for lo in ['piwnica','parter','pietro1']:
    FPe=footprint_dwg(m['floors'][lo]['geo']).buffer(-400)
    keep=[]
    for b in S[lo]:
        g=LineString(b['pts']).intersection(FPe)
        parts=[g] if g.geom_type=='LineString' else (list(g.geoms) if hasattr(g,'geoms') else [])
        for k_,pp in enumerate(parts):
            if pp.is_empty or pp.length<600: continue
            c=list(pp.coords); nb=dict(b); nb['id']=b['id']+('' if k_==0 else f'-{k_}'); nb['pts']=[[int(round(c[0][0]/10))*10,int(round(c[0][1]/10))*10],[int(round(c[-1][0]/10))*10,int(round(c[-1][1]/10))*10]]
            nb['q']=b['q'].split(' na długości')[0]+f' na długości {round(pp.length/10)} cm'+b['q'].split(' cm',1)[1] if ' na długości' in b['q'] else b['q']
            keep.append(nb)
    S[lo]=keep
fig,ax=plt.subplots(1,4,figsize=(48,13))
for k,f in enumerate(FL):
    a=ax[k]
    for w in it[f]:
        if w['type']=='iwall':
            p=w['pts']; a.plot([p[0][0],p[1][0]],[p[0][1],p[1][1]],color='#1a1a3a' if w.get('inv')!='D' else '#9aa5b8',lw=w['w']/70,solid_capstyle='butt')
        if w['type'] in('idoor','iwin'):
            p=w['pts']; a.plot([p[0][0],p[1][0]],[p[0][1],p[1][1]],color='g' if w['type']=='idoor' else 'c',lw=3)
    for b in G[f]: p=b['pts']; a.plot([p[0][0],p[1][0]],[p[0][1],p[1][1]],'r--',lw=4)
    for b in S[f]: p=b['pts']; a.plot([p[0][0],p[1][0]],[p[0][1],p[1][1]],color='orange',ls='--',lw=4)
    a.set_aspect('equal'); a.set_title(f'{f}: podciągi w przerwach {len(G[f])} (czerw.), pod ścianami wyżej {len(S[f])} (pomar.)',fontsize=20)
    log.append(f'{f}: podciągi w przerwach {len(G[f])}, pod ścianami z góry {len(S[f])}')
plt.savefig('struct.png',dpi=32,bbox_inches='tight')
json.dump({'it':it,'G':G,'S':S},open('struct_out.json','w'),ensure_ascii=False)
print('\n'.join(log))
