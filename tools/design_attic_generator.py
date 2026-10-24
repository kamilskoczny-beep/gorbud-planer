"""Warianty W1–W5 mieszkania M6 na poddaszu: skrzydło 212–219 (213, 216, 219 zach.; 215, 217, 218 wsch.; korytarz 212).
Współrzędne mm, układ lokalny poddasza (y w górę). Lica z inwentaryzacji:
  pokoje zach.: x 645–4215; korytarz 212: x 4315–5805 (y 9250–19330); pokoje wsch.: x 5905–9175
  213: y 9870–14490 | 216: y 14650–19360 | 219: x 675–6425, y 19550–23300 (okno płn. x 4495–5365, drzwi z korytarza x 4615–5475)
  215: y 9850–14490 | 217: y 14650–18260 (komin x 7115–9177, y 15090–15580) | 218: x 6635–9175, y 19330–23590 + przedsionek x 5905–9035, y 18360–19330
  skosy: zach. załamanie x=2535/2615 (h 1,9 przy x≈1700, 2,2 przy x≈1990); wsch. załamanie x=7225 (h 1,9 przy x≈8055, 2,2 przy x≈7770)
  wejście do korytarza z holu 211: otwór x 4585–5525 w ścianie y 9150–9250
"""
import json, random, string
random.seed(7)
def uid(): return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(7))
T=100  # ścianki działowe GK/bloczki 10 cm
ITEMS=[]
def add(it): ITEMS.append(it); return it
def wall(a,b,v,w=T): return add({'id':uid(),'type':'wall','pts':[a,b],'w':w,'v':v})
def demo(a,b,v,w,label=''): return add({'id':uid(),'type':'demo','pts':[a,b],'w':w,'v':v,'label':label})
def door(a,b,v,wallth=100,flip=False,open_=False): # a->b = światło; flip = strona otwierania (lewa normalna gdy False)
    it={'id':uid(),'type':'door','pts':[a,b],'w':wallth+40,'v':v,'flip':flip}
    if open_: it['open']=True
    return add(it)
def room(pts,label,v,anchor=None,color=None):
    it={'id':uid(),'type':'room','pts':pts,'label':label,'unit':'M6','v':v}
    cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts); it['anchor']=anchor or [round(cx),round(cy)]
    if color: it['color']=color
    return add(it)
def furn(kind,x0,y0,x1,y1,v,label=None):
    it={'id':uid(),'type':'furn','kind':kind,'pts':[[x0,y0],[x1,y1]],'v':v,'rot':1 if (x1-x0)<(y1-y0) and kind not in ('shower','night','armchair','chair','box') else 0}
    if label: it['label']=label
    return add(it)
def note(p,txt,v): return add({'id':uid(),'type':'note','pts':[p],'label':txt,'v':v})
def rect(x0,y0,x1,y1): return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]

# --- stałe geometrii
XW,XWC=645,4215; XC0,XC1=4315,5805; XEC,XE=5905,9175
R213=(9870,14490); R216=(14650,19360); R219=(675,6425,19550,23300); R215=(9850,14490); R217=(14650,18260)
# ---------------- bloki wielokrotnego użytku ----------------
def bed_west(v,y0,y1,pax='pax175',pax_y=None,desk=False,door_y=None):
    """sypialnia zach.: łóżko wezgłowiem przy ściance kolankowej (pod skosem), PAX na pełnej wysokości przy ścianie korytarza."""
    yc=(y0+y1)/2
    furn('bed',950,yc-800,2950,yc+800,v)              # 200 długie wzdłuż x, wezgłowie x=950 (za wnęką lukarny; h≈1,2 m)
    furn('night',3000,yc+850,3450,yc+1250,v); furn('night',3000,yc-1250,3450,yc-850,v)
    pw={'pax150':1500,'pax175':1750,'wardrobe':2000,'pax250':2500}[pax]
    py=pax_y if pax_y is not None else y1-60-pw
    furn(pax,XWC-25-580,py,XWC-25,py+pw,v)             # 58 głębokości przy ścianie korytarza (lico 4205–4215; h 2,78)
    if desk: furn('desk',2900,y0+60,4100,y0+660,v); furn('chair',3300,y0+700,3750,y0+1150,v)
def room217_single(v):
    """217 jako pokój 1-os.: łóżko 90 przy ścianie pełnej wysokości, biurko pod skosem (h≈1,4–2,2), PAX 150 przy ścianie płn."""
    furn('bed1',XEC+60,R217[0]+100,XEC+960,R217[0]+2100,v)
    furn('desk',7300,15700,8500,16300,v); furn('chair',7700,16350,8150,16800,v)
    furn('pax150',XEC+60,R217[1]-640,XEC+1560,R217[1]-60,v)
def bath_215(v,washer=True,tub=True):
    """łazienka w 215 (x 5905–9175, y 9850–14490): armatura przy ścianie pełnej wysokości x=5905, wanna pod skosem."""
    furn('shower',XEC+60,R215[1]-960,XEC+960,R215[1]-60,v)
    furn('wc',XEC+60,R215[1]-1900,XEC+460,R215[1]-1250,v)
    furn('basin',XEC+60,R215[0]+1500,XEC+560,R215[0]+1900,v)
    if washer: furn('washer',XEC+60,R215[0]+60,XEC+660,R215[0]+660,v)
    if tub: furn('bath',7300,R215[0]+60,9000,R215[0]+810,v)   # wanna pod skosem (h 1,9→0,9) – nad wanną nie trzeba stać
def kitchen_218(v):
    """kuchnia w 218 (x 6635–9175, y 19330–23590): ciąg przy ścianie zach. x=6635 (pełna wysokość), stół pod oknem połaciowym."""
    x0=6635; y=19400
    furn('fridge',x0+60,y,x0+660,y+650,v); y+=650
    furn('counter',x0+60,y,x0+660,y+1200,v,'blat 60'); y+=1200
    furn('sink',x0+60,y,x0+660,y+600,v); y+=600
    furn('counter',x0+60,y,x0+660,y+600,v,'blat'); y+=600
    furn('hob',x0+60,y,x0+660,y+600,v); y+=600
    furn('counter',x0+60,y,x0+660,y+500,v,'blat');
    furn('table4',7400,21800,8200,23000,v); furn('chair',7500,21300,7950,21750,v); furn('chair',7500,23050,7950,23500,v)
def living_219(v,kitchen_south=False,tv_east=True):
    """salon w 219 (x 675–6425, y 19550–23300; okno płn. x 4495–5365, drzwi płd. x 4615–5475, otwór do 218 w ścianie wsch. y 21000–22500)."""
    if not kitchen_south:
        # sofa pod oknem płn., RTV przy ścianie płd. (między skosem a drzwiami), fotel pod skosem zach., stół przy oknie/otworze do kuchni
        furn('sofa',1400,22300,3600,23200,v); furn('coffee',2000,21200,3000,21800,v)
        furn('tv',2300,19620,3900,20020,v)
        furn('armchair',1000,20500,1800,21300,v)
        furn('table',4700,22300,6100,23100,v); furn('chair',4900,21800,5350,22250,v); furn('chair',5500,21800,5950,22250,v)
    else:
        # aneks: ciąg przy ścianie płd. (x 2700–4600, pełna wysokość) + ściana wsch. (x 5825–6425)
        furn('fridge',2700,19620,3300,20270,v); furn('counter',3300,19620,3900,20220,v,'blat'); furn('sink',3900,19620,4500,20220,v)
        furn('hob',5825,19700,6425,20300,v); furn('counter',5825,20300,6425,21500,v,'blat 60')
        furn('table',4700,22300,6100,23100,v); furn('chair',4900,21800,5350,22250,v); furn('chair',5500,21800,5950,22250,v)
        furn('tv',1300,20900,1700,22500,v)                 # RTV pod skosem (h≈1,4 m przy x=1,3)
        furn('sofa',3600,20700,4500,22900,v); furn('coffee',2400,21300,3400,21900,v)

def common_rooms(v,names):
    """obrysy (przeliczane automatycznie ze ścian) + etykiety; names: dict nr->label"""
    cols={'213':'#6d9dc5','216':'#8ab17d','219':'#f4a261','215':'#2a9d8f','217':'#c77dff','218':'#e9c46a','212':'#cfd6dd'}
    R={'213':rect(XW,R213[0],XWC,R213[1]),'216':rect(XW,R216[0],XWC,R216[1]),'219':rect(R219[0],R219[2],R219[1],R219[3]),
       '215':rect(XEC,R215[0],XE,R215[1]),'217':rect(XEC,R217[0],XE,R217[1]),'218':rect(6635,19330,XE,23590),'212':rect(XC0,9250,XC1,19330)}
    anch={'213':[2400,12200],'216':[2400,17000],'219':[3500,21400],'215':[6900,12200],'217':[6600,16500],'218':[7700,21500],'212':[5060,14300]}
    for nr,lab in names.items(): room(R[nr],lab,v,anchor=anch[nr],color=cols[nr])

# ================= W1 – Klasyczny: 3 sypialnie, kuchnia w 218 otwarta na salon =================
v='W1'
door([6530,21000],[6530,22500],v,wallth=210,open_=True)                       # otwór 1,5 m salon 219 ↔ kuchnia 218 (ściana x 6425–6635, do weryfikacji konstr.)
bed_west(v,*R213,pax='pax150',pax_y=12900,desk=True)                          # 213: sypialnia 1 (lukarna zach.)
bed_west(v,*R216,pax='pax175',pax_y=17450)                                    # 216: sypialnia 2
room217_single(v)  # 217: pokój 3 / gabinet
bath_215(v)
kitchen_218(v); living_219(v)
common_rooms(v,{'213':'sypialnia 1','216':'sypialnia 2','219':'salon','215':'łazienka + pralnia','217':'pokój 3 / gabinet','218':'kuchnia z jadalnią','212':'korytarz'})
note([5100,10000],'W1: wejście z holu 211; łazienka przy wejściu (piony w korytarzu). Otwór 219↔218 – sprawdzić, czy ściana x≈6,5 m nie jest nośna.',v)

# ================= W2 – Salon z otwartą kuchnią w 219, 3 sypialnie, garderoba =================
v='W2'
door([4315,19440],[5805,19440],v,wallth=220,open_=True)   # otwór 1,49 m (cała szerokość korytarza) salon↔hol, nadproże zostaje
bed_west(v,*R213,pax='pax150',pax_y=12900)
bed_west(v,*R216,pax='pax175',pax_y=17450,desk=True)
furn('bed',7000,15650,8600,17650,v)   # 217: sypialnia 3 – łóżko pod skosem (bok przy skosie h≈1,3), za kominem
furn('pax175',XEC+60,R217[0]+100,XEC+640,R217[0]+1850,v)
furn('pax250',6700,19400,7280,21900,v); furn('pax200s',6700,22000,7050,24000,v) if False else None  # 218: garderoba + gabinet
furn('pax250',6700,19400,7280,21900,v) if False else None
furn('desk',7600,22400,8800,23000,v); furn('chair',8000,21900,8450,22350,v)
bath_215(v)
living_219(v,kitchen_south=True)
common_rooms(v,{'213':'sypialnia 1','216':'sypialnia 2','219':'salon z kuchnią','215':'łazienka + pralnia','217':'sypialnia 3','218':'garderoba + gabinet','212':'korytarz'})
note([5100,10000],'W2: kuchnia w salonie 219 przy ścianie płd. i wsch. (piony do poprowadzenia wzdłuż korytarza).',v)

# ================= W3 – Master suite: 216 sypialnia + 213 łazienka z lukarną; 2. łazienka w 215 =================
v='W3'
wall([XWC-580-100,R213[0]],[XWC-580-100,R213[1]],v) if False else None
# 213 → łazienka główna (światło z lukarny), 216 → sypialnia master z garderobą PAX 300
furn('bath',700,13300,2400,14050,v)                       # wanna pod skosem przy ścianie płn. 213
furn('shower',XWC-960,R213[1]-960,XWC-60,R213[1]-60,v)
furn('basin',XWC-560,11200,XWC-60,11600,v); furn('basin',XWC-560,10600,XWC-60,11000,v)
furn('wc',XWC-460,R213[0]+100,XWC-60,R213[0]+750,v)
furn('washer',1000,R213[0]+100,1600,R213[0]+700,v)
bed_west(v,*R216,pax='pax150',pax_y=14750); furn('wardrobe',2150,R216[1]-640,4150,R216[1]-60,v)   # 216 master: PAX 150 przy korytarzu (płd.) + PAX 200 przy ścianie płn. (x≥2,15 → h≥2,36)                # 216 master (PAX 250 x 4215 ściana)
furn('pax150',XWC-580,R216[0]+60,XWC,R216[0]+1560,v) if False else None
door([4265,12000],[4265,12800],v,wallth=100,flip=True) if False else None
bed_west(v,*R217,pax='pax175') if False else None
# 217 → sypialnia 2 (gościnna/dziecko)
furn('bed',7000,15650,8600,17650,v); furn('pax175',XEC+60,R217[0]+100,XEC+640,R217[0]+1850,v); furn('desk',XEC+60,17200,XEC+1260,17800,v)
bath_215(v,washer=False,tub=False); furn('box',7300,R215[0]+60,8800,R215[0]+410,v,'szafki niskie 90 (pod skosem)')
kitchen_218(v); door([6530,21000],[6530,22500],v,wallth=210,open_=True)
living_219(v)
common_rooms(v,{'213':'łazienka główna','216':'sypialnia master','219':'salon','215':'łazienka gościnna','217':'sypialnia 2','218':'kuchnia z jadalnią','212':'korytarz'})
note([5100,10000],'W3: dwie łazienki – 213 (lukarna, wanna pod skosem) i 215 przy wejściu. Piony: 213/215 po obu stronach korytarza.',v)

# ================= W4 – Loft: korytarz + 215 otwarte na kuchnię/jadalnię =================
v='W4'
demo([5855,10200],[5855,14300],v,100,'usunięcie ścianki 215|korytarz (sprawdzić – słupy więźby?)')
# kuchnia wzdłuż ściany płd. 215 (y=9850) i wsch. pod skosem (blaty OK, bez szafek górnych)
furn('fridge',XEC+60,R215[0]+60,XEC+660,R215[0]+710,v)
furn('sink',XEC+660,R215[0]+60,XEC+1260,R215[0]+660,v); furn('counter',XEC+1260,R215[0]+60,7800,R215[0]+660,v,'blat 60'); furn('hob',7800,R215[0]+60,8400,R215[0]+660,v); furn('counter',8400,R215[0]+60,8850,R215[0]+660,v,'blat (h≈1,0 m przy skosie)')
furn('table',6200,12300,7600,13100,v); furn('chair',6400,11800,6850,12250,v); furn('chair',7000,11800,7450,12250,v); furn('chair',6400,13150,6850,13600,v); furn('chair',7000,13150,7450,13600,v)
bed_west(v,*R213,pax='pax150',pax_y=12900,desk=True)
bed_west(v,*R216,pax='pax175',pax_y=17450)
# 217 → łazienka (przy kominie – piony), 218 → gabinet/pokój gościnny
furn('shower',XEC+60,R217[0]+60,XEC+960,R217[0]+960,v); furn('wc',XEC+60,R217[0]+1100,XEC+460,R217[0]+1750,v); furn('basin',XEC+60,R217[1]-500,XEC+560,R217[1]-100,v); furn('washer',6600,R217[1]-700,7200,R217[1]-100,v); furn('bath',7300,R217[1]-850,9000,R217[1]-100,v)
furn('bed1',6700,19400,7600,21400,v); furn('desk',6700,22900,7900,23500,v); furn('pax150',7700,19400,9200,19980,v) if False else None; furn('pax150',6700,21500,7280,23000,v) if False else None
furn('pax175',8500,19400,9080,21150,v) if False else None
living_219(v)
common_rooms(v,{'213':'sypialnia 1','216':'sypialnia 2','219':'salon','215':'kuchnia z jadalnią + hol (otwarte)','217':'łazienka + pralnia','218':'gabinet / pokój gościnny'})
note([5100,10000],'W4: loft – ścianka 215|korytarz do usunięcia (zweryfikować konstrukcję więźby), kuchnia tuż przy wejściu.',v)

# ================= W5 – Rodzinny: 216 podzielone na 2 pokoje (nowe okna połaciowe), 4 pokoje =================
v='W5'
YS=17000  # oś nowej ścianki w 216 (pokoje 2,30 i 2,31 m w świetle)
wall([XW,YS],[XWC,YS],v)
# drzwi: dolny pokój z korytarza istniejącymi (y 16520–17370 → zostaje część 16520–16950?) – prościej: zamurować stary otwór i dać dwoje drzwi 80 z korytarza
wall([4265,16520],[4265,17370],v,w=100)                                  # zamknięcie starego otworu 216
door([4265,15700],[4265,16500],v,wallth=100,flip=True)                  # pokój 2a (płd.)
door([4265,17500],[4265,18300],v,wallth=100,flip=True)                  # pokój 2b (płn.)
for (y0,y1,py) in ((R216[0],YS-50,14750),(YS+50,R216[1],17500)):
    furn('bed1',950,y0+150,2950,y0+1050,v); furn('desk',2900,y1-700,4100,y1-100,v); furn('pax150',XWC-25-580,py,XWC-25,py+1500,v)
note([1500,16800],'W5: nowe okna połaciowe w połaci zach. nad pokojami 2a/2b (po jednym, ok. 78×118) – doświetlenie 1:8',v)
bed_west(v,*R213,pax='pax150',pax_y=12900)
bath_215(v)
# 217 → pokój 4 / gościnny, 218 → kuchnia otwarta na salon
room217_single(v)
kitchen_218(v); door([6530,21000],[6530,22500],v,wallth=210,open_=True)
living_219(v)
common_rooms(v,{'213':'sypialnia rodziców','216':'pokoje 2a / 2b','219':'salon','215':'łazienka + pralnia','217':'pokój 4','218':'kuchnia z jadalnią','212':'korytarz'})
# osobne etykiety dla 2a/2b
room(rect(XW,R216[0],XWC,YS-50),'pokój 2a',v,anchor=[2400,15800],color='#8ab17d'); room(rect(XW,YS+50,XWC,R216[1]),'pokój 2b',v,anchor=[2400,18200],color='#84a59d')
ITEMS=[i for i in ITEMS if not (i.get('type')=='room' and i.get('label')=='pokoje 2a / 2b')]

ITEMS=[i for i in ITEMS if i is not None]
json.dump({'items':ITEMS,'updatedAt':'2026-10-24T15:00:00.000Z','floor':'poddasze'},open('seed_poddasze.json','w'),ensure_ascii=False)
from collections import Counter
print(len(ITEMS), Counter(i['v'] for i in ITEMS))
