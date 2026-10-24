"""Poddasze, wariant roboczy W4: M7 = 210 + 209 + 205 (+ przedsionek S jako hol), M8 = 206 + 207 + 208.
Lica (mm, układ lokalny poddasza):
  209: x 715–6925, płd. lico skośne (715,710)→(6925,890), płn. 3940; okno połaciowe x 4551–5281 (y 927–2087); otwór 209↔S x 4935–5815 (ściana y 3940–4220)
  210: x 455–4465, y 4220–8120; lukarna zach. y 5280–7080; drzwi 210↔211 x 4465 y 6120–6920
  S (przedsionek): x 4565–6925, y 4220–5910; drzwi S↔211 w ściance y 5910–6072, x 5415–6215
  205: x 7235–12345, y ≈800–6660 (strop płaski 2,71); okno płd. x 8633–10451; drzwi: z 202 x 10735–11535 (y 6660–6940), z holu 211 x 7235 y 6660–6940, do 206 x 12345 y 3810–4610
  206: x 12495–16135, y ≈1050–6660; okno płd. x 13431–15240; drzwi z 202 x 14105–14905; do 207 x 16135–16305 y 3910–4710
  207: x 16305–20395, y ≈1200–6660; okno płd. x 16662–18491; drzwi z 202 x 18005–18805; do 208 x 20395 y 1660–2360
  208: x 20545–22136, y 1340–2660 (2,1 m²)
Skosy: zach. x<2328/2405 (h 1,9 przy ~1700); płd. w 209 y<2250 (h 1,9 przy ~1700). 205–208 strop płaski.
"""
import json, random, string
random.seed(51)
def uid(): return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(7))
V='W4'; T=100; OUT=[]
def add(it): OUT.append(it); return it
def wall(a,b,w=T): return add({'id':uid(),'type':'wall','pts':[a,b],'w':w,'v':V})
def demo(a,b,w,label=''): return add({'id':uid(),'type':'demo','pts':[a,b],'w':w,'v':V,'label':label})
def door(a,b,wallth=100,flip=False,open_=False):
    it={'id':uid(),'type':'door','pts':[a,b],'w':wallth+40,'v':V,'flip':flip}
    if open_: it['open']=True
    return add(it)
def room(pts,label,unit,anchor,color): return add({'id':uid(),'type':'room','pts':pts,'label':label,'unit':unit,'v':V,'anchor':anchor,'color':color})
def furn(kind,x0,y0,x1,y1,label=None):
    it={'id':uid(),'type':'furn','kind':kind,'pts':[[x0,y0],[x1,y1]],'v':V,'rot':1 if (x1-x0)<(y1-y0) and kind not in ('shower','night','armchair','chair','box') else 0}
    if label: it['label']=label
    return add(it)
def note(p,txt): return add({'id':uid(),'type':'note','pts':[p],'label':txt,'v':V})
def rect(x0,y0,x1,y1): return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]

# ===================== M7 = 210 + 209 + 205, hol = przedsionek S (ok. 65 m² podłogi) =====================
# wejście: istniejące drzwi S↔211 (x 5415–6215). Zamurowania: 210↔211 (x 4465, y 6120–6920), 205↔hol 211 (x 7235, y 6660–6940), 205↔202 (y 6660–6940, x 10735–11535), 205↔206 (x 12345, y 3810–4610)
wall([4515,6120],[4515,6920],w=100); wall([7235,6660],[7235,6940],w=300); wall([11135,6800],[10735,6800],w=280); wall([11135,6800],[11535,6800],w=280); wall([12420,3810],[12420,4610],w=150)
# nowe drzwi z holu S: do 210 (ściana x 4465–4565), do 205 (ściana x 6925–7235); otwór 209↔S dostaje drzwi 80
door([4515,4900],[4515,5700],wallth=100,flip=True)                       # hol → 210 (otwierane do 210)
door([7080,4700],[7080,5500],wallth=310,flip=False)                      # hol → 205 (otwierane do 205)
door([4975,4080],[5775,4080],wallth=280,flip=True)                       # hol → 209 (w istniejącym otworze 0,88, otwierane do 209)
# --- 205: salon z aneksem (5,1 × 5,8, strop 2,71). Kuchnia przy ścianie płn. (zamurowane drzwi z 202 → ciąg 4 m), lodówka przy wejściu z holu,
#     RTV na ścianie zach. (prostopadłej do okna), sofa przy ścianie wsch. 3,9 m od RTV, ława 45 cm przed sofą, stół przy kuchni (≤ 3 m od zlewu)
furn('fridge',7450,6000,8050,6650); furn('counter',8050,6060,8650,6660,'blat 60'); furn('sink',8650,6060,9250,6660); furn('box',9250,6060,9850,6660,'zmywarka 60'); furn('counter',9850,6060,10450,6660,'blat roboczy'); furn('hob',10450,6060,11050,6660); furn('counter',11050,6060,11350,6660,'blat 30')
furn('tv',7300,2600,7700,4200); furn('sofa',11445,2300,12345,4500); furn('coffee',10500,2900,11000,3900)
furn('table',8700,4500,10100,5300); furn('chair',8900,4000,9350,4450); furn('chair',9500,4000,9950,4450); furn('chair',8900,5350,9350,5800); furn('chair',9500,5350,9950,5800)
furn('armchair',8300,1500,9100,2300)
# --- 209: sypialnia 1 (6,2 × 3,1; skos zach. i płd., okno połaciowe x 4551–5281). Łóżko wezgłowiem pod skos płd. w strefie pełnej wysokości x>2,4;
#     PAX 200 przy ścianie wsch. (h 2,35 → PAX 2,36: ściana wsch. x 6925 jest poza skosem zach., h=2,35 – dobrać PAX niski? h_sufitu 235 → PAX 236 nie wejdzie → PAX 200×58 w wersji 201 cm)
furn('bed',2700,1000,4300,3000); furn('night',2250,2550,2700,2950); furn('night',4300,2550,4750,2950)
w=furn('pax175',6345,2150,6925,3900,'PAX 175×58 niski (201 cm)'); w['hgt']=2010   # h sufitu 2,35 (skos płd. od y 2250) → wersja PAX 201 cm, poza skosem
furn('desk',4500,1300,5700,1900); furn('chair',4900,1950,5350,2400)      # biurko pod oknem połaciowym (siedząc h ≈ 1,4–2,0)
# --- 210: sypialnia 2 / pokój (4,0 × 3,9; lukarna zach. y 5280–7080). Łóżko wezgłowiem przy ścianie wsch. (po zamurowaniu drzwi), PAX 175 przy ścianie płd. poza strefą drzwi, biurko przy lukarnie
furn('bed',2465,6200,4465,7800); furn('night',4000,7850,4450,8100); furn('night',4000,5750,4450,6150)
furn('pax175',2400,4220,4150,4800,'PAX 175'); furn('desk',1100,5600,2300,6200); furn('chair',1500,6250,1950,6700)
# --- hol S (2,36 × 1,69): szafa płytka na okrycia przy ścianie płn. poza wymachem drzwi wejściowych (5415–6215)
furn('pax150s',4615,5500,6115,5850,'PAX 150×35 (okrycia)') if False else None
furn('shoe',4615,4280,4965,4880,'szafka na buty')   # w narożniku płd.-zach. holu, poza strefami drzwi
room(rect(7235,800,12345,6660),'salon z aneksem (205)','M7',[9800,3300],'#f4a261')
room(rect(715,750,6925,3940),'sypialnia 1 (209)','M7',[3500,2200],'#6d9dc5')
room(rect(455,4220,4465,8120),'sypialnia 2 (210)','M7',[2400,7000],'#8ab17d')
room(rect(4565,4220,6925,5910),'hol','M7',[5745,5000],'#cfd6dd')
note([5745,6600],'M7 (209+210+205): wejście z holu 211 istniejącymi drzwiami do przedsionka; drzwi 210→211, 205→211, 205→202 i 205→206 zamurowane; nowe drzwi hol→210 i hol→205 (ściana 31 cm – sprawdzić). Piony kuchni: wzdłuż ściany płn. 205 do pionu łazienek 204/208.')

# ===================== M8 = 206 + 207 + 208 (ok. 45 m² podłogi) =====================
# wejście: istniejące drzwi 206 z 202 (x 14105–14905); drzwi 207 z 202 zamurowane; 207 dostępne z 206 istniejącymi drzwiami (x 16135–16305, y 3910–4710); 208 = garderoba z 207
wall([18405,6800],[18005,6800],w=280); wall([18405,6800],[18805,6800],w=280)
# łazienka w narożniku płn.-zach. 206 (1,6 × 2,0) przy wejściu; ścianki y=4660 (x 12495–14105) i x=14105 (y 4660–6660); drzwi z pokoju w ściance wsch.
wall([12495,4660],[14105,4660]); wall([14105,4660],[14105,6660])
door([14105,4760],[14105,5560],wallth=100,flip=True)                     # pokój → łazienka (otwierane do łazienki, drzwi 80)
furn('shower',12555,5760,13455,6660); furn('wc',12555,4760,12955,5410); furn('basin',13500,6260,14000,6660)
# kuchnia przy ścianie zach. 206 (wspólna ściana instalacyjna z łazienką): lodówka przy łazience → blat → zlew → zmywarka → blat/pralka → płyta → blat 30
furn('fridge',12555,3950,13155,4600); furn('counter',12495,3350,13095,3950,'blat 60'); furn('sink',12495,2750,13095,3350); furn('box',12495,2150,13095,2750,'zmywarka 60'); furn('hob',12495,1550,13095,2150); furn('counter',12495,1250,13095,1550,'blat 30')
# strefa dzienna 206: sofa pod oknem płd. frontem na północ, RTV na ściance łazienki (y 4660) w osi sofy, ława; stół 120×80 przy kuchni; buty przy wejściu
furn('sofa',13200,1250,15200,2150); furn('coffee',13700,2600,14700,3200); furn('tv',13100,4200,14000,4600,'RTV (na ściance łazienki)')
furn('table4',15000,2500,15800,3700); furn('chair',14550,2900,15000,3350); furn('chair',15250,2050,15700,2500)
furn('shoe',15000,5600,15350,6600,'szafka na buty')
# 207: sypialnia (4,1 × 5,4): wezgłowie przy ścianie wsch. (x 20395) poza drzwiami do 208; PAX 250 przy ścianie płn. (zamurowane drzwi); biurko pod oknem
furn('bed',18395,3000,20395,4600); furn('night',19950,4650,20395,5050); furn('night',19950,2550,20395,2950)
furn('pax250',16500,6080,19000,6660,'PAX 250'); furn('desk',16500,1300,17700,1900); furn('chair',16850,1950,17300,2400)
furn('armchair',16400,4600,17200,5400)
# 208 → garderoba: PAX 150 (płytki 35) przy ścianie wsch.
furn('pax150s',21786,1400,22136,2900,'PAX 150×35') if False else None
furn('pax150s',20600,2250,22100,2600,'PAX 150×35 (garderoba)')
room(rect(12495,1050,16135,4660),'pokój dzienny z aneksem (206)','M8',[14300,2700],'#f28482')
room(rect(12495,4660,14105,6660),'łazienka','M8',[13300,5700],'#2a9d8f')
room(rect(16305,1200,20395,6660),'sypialnia (207)','M8',[18300,2300],'#6d9dc5')
room(rect(20545,1340,22136,2660),'garderoba (208)','M8',[21300,2000],'#c77dff')
note([17000,7300],'M8 (206+207+208): wejście drzwiami 206; drzwi 207 z korytarza zamurowane; łazienka przy wejściu, kuchnia na wspólnej ścianie instalacyjnej; 208 jako garderoba.')

OUT=[i for i in OUT if i is not None]
json.dump(OUT,open('seed_m7m8.json','w'),ensure_ascii=False)
print(len(OUT))
