"""M2 = 106+107 i M3 = 105+103+104 na I piętrze (wariant roboczy P9). Współrzędne mm, układ lokalny I piętra.
Lica z inwentaryzacji:
  107: x 7250–11730, płd. lico skośne y≈537+0,0495·(x−10914) (ok. 360 przy x=7250, 577 przy 11730), płn. 6772; okno płd. x 8178–10896; drzwi 2-skrz. z korytarza x 9520–10720 (ściana y 6772–7192)
  106: x 11940–15840, płd. ≈1160–1350, płn. 6772; okno płd. x 13739–15097; drzwi 2-skrz. x 13100–14300
  105: x 16060–19030, płd. ≈1347–1492, płn. 6772; okno x 16908–18266; drzwi x 17530–18330
  blok 103/104: x 19199–22206(22330), y ≈1000–6762; pokój płd.-wsch. y do 2950 (okno x 20162–21340); część środk. 104 y 2966–5986; 103 x 20500–22330 y 5642–6762; przedsionek x 19459–20360 y 5986–6742
  drzwi z korytarza: 104 → x 19510–20310 (y 6742–7192); 103 → x 20700–21500 (y 6762–7192)
"""
import json, random, string
random.seed(21)
def uid(): return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(7))
V='P9'; T=120; OUT=[]
def add(it): OUT.append(it); return it
def wall(a,b,w=T): return add({'id':uid(),'type':'wall','pts':[a,b],'w':w,'v':V})
def demo(a,b,w,label=''): return add({'id':uid(),'type':'demo','pts':[a,b],'w':w,'v':V,'label':label})
def door(a,b,wallth=120,flip=False,open_=False):
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
def ys107(x): return 537+0.0495*(x-10914)

# ===================== M2 = 106 + 107 (ok. 47 m²) =====================
# Zasady: strefa 0,9 m przed każdymi drzwiami wolna; RTV naprzeciw sofy (2,5–3,5 m), ława 40–45 cm przed sofą; wezgłowie łóżka przy pełnej ścianie,
# dojście do łóżka z obu stron ≥ 0,7 m; PAX z 0,9 m przed frontem; kuchnia: lodówka → blat → zlew → blat roboczy → płyta → blat (trójkąt 4–8 m), płyta ≥ 30 cm od ściany.
wall([13100,6982],[14300,6982],w=420)                                   # zamurowanie otworu 106 (wejście zostaje przez 107)
# 107 = salon z aneksem; kuchnia w narożniku płn.-zach. (wg uwagi inwestora), L: ściana płn. na zachód od wejścia + ściana zach.
furn('fridge',8800,6120,9400,6770)                                      # lodówka przy wejściu (koniec ciągu)
furn('counter',8200,6172,8800,6772,'blat 60'); furn('hob',7600,6172,8200,6772); furn('counter',7300,6172,7600,6772,'blat 30')   # płyta 30 cm od narożnika
furn('counter',7300,5572,7900,6172,'blat narożny'); furn('sink',7300,4972,7900,5572); furn('box',7300,4372,7900,4972,'zmywarka 60'); furn('counter',7300,3772,7900,4372,'blat roboczy')
# strefa dzienna: RTV na ścianie zach. (prostopadle do okna), sofa przy ścianie wsch., ława 45 cm przed sofą, stół przy kuchni
furn('tv',7300,2600,7700,4200); furn('sofa',10830,2400,11730,4600); furn('coffee',9880,3000,10380,4000)
furn('table',8200,3950,9600,4750); furn('chair',8400,3450,8850,3900); furn('chair',9000,3450,9450,3900); furn('chair',8400,4800,8850,5250); furn('chair',9000,4800,9450,5250)
furn('armchair',8400,1300,9200,2100)                                     # fotel przy oknie, w kącie czytelniczym
furn('shoe',10800,6400,11700,6750,'szafka na buty')                     # przy wejściu, poza wymachem drzwi
# 106: sypialnia (płd.) + łazienka i garderoba (płn.), ścianki y=4700 i x=14000
wall([11940,4700],[15840,4700]); wall([14000,4700],[14000,6772])
door([11835,5300],[11835,6100],wallth=210,flip=True)                    # salon → łazienka (otwierane do łazienki)
door([11835,1500],[11835,2300],wallth=210,flip=True)                    # salon → sypialnia (przy oknie, z dala od sofy)
door([14400,4700],[15200,4700],wallth=120,flip=False)                   # sypialnia → garderoba (otwierane do garderoby)
furn('bed',13840,2100,15840,3700); furn('night',15390,3750,15840,4150); furn('night',15390,1650,15840,2050)   # wezgłowie przy pełnej ścianie wsch., dojścia 0,7 m z obu stron
furn('pax175',12000,4060,13750,4640,'PAX 175')                          # front na południe, 0,9 m wolne przed frontem
furn('desk',12900,1300,14100,1900); furn('chair',13250,1950,13700,2400)  # biurko pod oknem, poza strefą drzwi
furn('shower',13000,5820,13900,6720); furn('wc',13540,4760,13940,5410); furn('basin',12050,6300,12550,6700); furn('washer',12900,4760,13500,5360)
furn('pax150',14070,6190,15570,6770,'PAX 150 (garderoba)')
room(rect(7250,500,11730,6772),'salon z aneksem (107)','M2',[9300,2800],'#f4a261')
room(rect(11940,1200,15840,4700),'sypialnia (106)','M2',[13600,3000],'#6d9dc5')
room(rect(11940,4700,14000,6772),'łazienka','M2',[12900,5500],'#2a9d8f')
room(rect(14000,4700,15840,6772),'garderoba','M2',[14900,5500],'#8ab17d')
note([9000,7600],'M2: wejście drzwiami 107 (zwęzić do 90), drzwi 106 zamurowane, nowe piony przy ścianie 106|107')

# ===================== M3 = 105 + 103 + 104 (ok. 34 m²) – kawalerka: pokój z aneksem i miejscem do spania =====================
# wejście: istniejące drzwi 104 z korytarza (19510–20310) → przedsionek → hol; drzwi 105 (1,2 m) i 103 z korytarza zamurowane
wall([17530,6982],[18330,6982],w=420); wall([20700,6977],[21500,6977],w=430); wall([19241,2942],[20041,2942],w=80)   # + zamknięcie starych drzwi wnęka→104
# wyburzenia: ścianki dawnych WC w bloku 104 (x≈20360–20500 do y 5400, y≈4202–4372) + ściana 105|pas płd.-wsch. (wnęka jadalna przy oknie)
demo([19115,1550],[19115,2700],170,'otwarcie wnęki przy oknie (ściana 105|pas płd.-wsch., 170 mm)')
demo([20425,3050],[20425,5350],140,'ścianki dawnych WC'); demo([20430,4287],[22250,4287],170,'')
# podział bloku: łazienka = część środkowa do y 5422 (ściana istniejąca zostaje), hol = pas płn. (x 19199–20360, y 5422–5986) + przedsionek; 103 = schowek z przedsionka
door([19115,5450],[19115,6250],wallth=170,flip=True)                    # hol → pokój 105
door([19500,5452],[20300,5452],wallth=60,flip=False)                    # hol → łazienka (w istniejącej ściance y 5422–5482)
door([20430,5900],[20430,6700],wallth=140,flip=False)                   # przedsionek → schowek (d. 103)
# 105: kuchnia przy ścianie zach. (y 3600–6750), łóżko 140×200 wezgłowiem przy ścianie płn. (po zamurowaniu drzwi), sofa przy ścianie wsch., RTV na ścianie zach.
furn('fridge',16110,6100,16710,6750); furn('counter',16110,4900,16710,6100,'blat 60'); furn('hob',16110,4300,16710,4900); furn('sink',16110,3600,16710,4300)
furn('bed',16720,4770,18120,6770,'łóżko 140×200')
furn('sofa',18130,2900,19030,4600); furn('coffee',17200,3300,18200,3900); furn('tv',16110,1600,16510,3200)
# wnęka przy oknie (dawny pas płd.-wsch., gł. ok. 1,25 m): stolik + 2 krzesła
furn('table4',20400,1650,21600,2450); furn('chair',19920,1850,20370,2300); furn('chair',21630,1850,22080,2300)
# łazienka (x 19199–22150/22330, y 2966–5422): prysznic w narożniku wsch., WC i umywalka przy ścianie zach., pralka
furn('shower',21200,3110,22100,4010); furn('wc',19260,3200,19660,3850); furn('basin',20450,4950,20950,5350); furn('washer',21650,4700,22250,5300)
room(rect(16060,1400,19030,6772),'pokój z aneksem i wnęką jadalną (105)','M3',[17500,2300],'#f28482')
room(rect(19199,2966,22330,5422),'łazienka','M3',[20700,4200],'#2a9d8f')
room(rect(19199,5422,20360,6742),'hol z przedsionkiem','M3',[19800,6000],'#8ab59d')
room(rect(20500,5642,22330,6762),'schowek (d. 103)','M3',[21400,6200],'#b5838d')
note([17000,7600],'M3 (105+103/104): kawalerka ok. 34 m² – wejście drzwiami 104 przez przedsionek; drzwi 105 i 103 z korytarza zamurowane; ścianki dawnych WC do wyburzenia; pas przy oknie płd.-wsch. (gł. 1,25 m) otwarty na 105 jako wnęka jadalna (ściana 170 mm – sprawdzić nośność).')

OUT=[i for i in OUT if i is not None]
json.dump(OUT,open('seed_m2m3.json','w'),ensure_ascii=False)
print(len(OUT))
