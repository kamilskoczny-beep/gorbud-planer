"""Koncepcja podziału sali 108 (I piętro) — dwa warianty. Współrzędne lokalne mm (jak w modelu)."""
import json, random, string

def uid(): return ''.join(random.choice(string.ascii_lowercase+string.digits) for _ in range(7))

# interior faces of 108
XW = 680      # west face (między filarami 550–700)
XE = 6820     # east face
YN = 15182    # north face
def ys(x):    # south face (skośna): (670,644) -> (6820,942)
    return round(644 + (x-670)*(942-644)/(6820-670))
STUB = (5880, 6780, 9080, 9560)  # występ/komin przy ścianie wsch.
T = 120       # grubość nowych ścian
H = T/2

def wall(pts, v): return {'id':uid(),'type':'wall','pts':pts,'w':T,'v':v}
def door(a, b, v, w=900): return {'id':uid(),'type':'door','pts':[a,b],'w':300,'v':v}
def room(pts, label, unit, v): return {'id':uid(),'type':'room','pts':pts,'label':label,'unit':unit,'v':v}
def note(p, txt, v): return {'id':uid(),'type':'note','pts':[p],'label':txt,'v':v}

items = []

# ============ WARIANT P1: 108 = jedno mieszkanie (M1) ============
v='P1'
# ściany (osie): hall/korytarz/łazienka/sypialnie
# 1) ściana y=6900 od x=680 do 6820 (salon | hall + gabinet) z otworem do salonu x 4400-6700 (szerokie wejście) i drzwiami do gabinetu? gabinet x 680-4300 y 6900-9080
items.append(wall([[XW,6900],[4300,6900]], v))                      # gabinet | salon
items.append(wall([[4300,6900],[XE,6900]], v))                      # hall | salon (z otworem 2-skrzydłowym)
items.append(wall([[4300,6900],[4300,12400]], v))                   # oś x=4300: gabinet/sypialnia1 | hall/korytarz
items.append(wall([[XW,9080],[4300,9080]], v))                      # gabinet | sypialnia 1
items.append(wall([[4300,9080],[5500,9080]], v))                    # hall | korytarz (nie; hall otwarty) -> usuń? zostawiamy jako otwarty: brak
items.pop()
items.append(wall([[5500,9080],[5500,12400]], v))                   # korytarz | łazienka(+występ)
items.append(wall([[XW,12400],[XE,12400]], v))                      # sypialnia 2 (płn.)
items.append(wall([[5500,9560],[XE,9560]], v))                      # zamknięcie występu od strony łazienki? łazienka y 9560-12400 -> ściana przy występie
# drzwi
items.append({**door([4700,6900],[6500,6900], v),'open':True})   # salon – otwór 1,8 m bez drzwi
items.append(door([4300,7400],[4300,8300], v))   # gabinet
items.append(door([4300,9700],[4300,10600], v))  # sypialnia 1
items.append(door([5500,10200],[5500,11000], v)) # łazienka (80 cm)
items.append(door([4500,12400],[5400,12400], v)) # sypialnia 2
# pomieszczenia (netto, wewnątrz ścian)
items.append(room([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,6900-H],[XW,6900-H]], 'salon z aneksem kuchennym', 'M1', v))
items.append(room([[XW,6900+H],[4300-H,6900+H],[4300-H,9080-H],[XW,9080-H]], 'gabinet / pokój 3', 'M1', v))
items.append(room([[4300+H,6900+H],[XE,6900+H],[XE,9080],[5880,9080],[5880,9560],[5500+H,9560],[5500+H,12400-H],[4300+H,12400-H]], 'przedpokój + korytarz', 'M1', v))
items.append(room([[5500+H,9560+H],[XE,9560+H],[XE,12400-H],[5500+H,12400-H]], 'łazienka', 'M1', v))
items.append(room([[XW,9080+H],[4300-H,9080+H],[4300-H,12400-H],[XW,12400-H]], 'sypialnia 1', 'M1', v))
items.append(room([[XW,12400+H],[XE,12400+H],[XE,YN],[XW,YN]], 'sypialnia 2', 'M1', v))
items.append(note([6300,9300], 'występ/komin – sprawdzić (wentylacja łazienki?)', v))
items.append(note([2500,5200], 'aneks kuchenny przy ścianie y=6,9 m; okap – kanał w górę przez poddasze', v))

# meble P1
v='P1'
def furnP1(kind,x0,y0,x1,y1,label=None):
    d={'id':uid(),'type':'furn','kind':kind,'pts':[[x0,y0],[x1,y1]],'v':v}
    if label: d['label']=label
    return d
# salon z aneksem: ciąg kuchenny przy ścianie gabinetu/holu (y=6,84)
items += [furnP1('fridge',3640,6130,4240,6780), furnP1('counter',3040,6180,3640,6780,'blat'), furnP1('hob',2440,6180,3040,6780), furnP1('counter',1840,6180,2440,6780,'blat'), furnP1('sink',1240,6180,1840,6780), furnP1('counter',740,6180,1240,6780,'blat')]
items += [furnP1('table',1500,4800,2900,5600,'stół 140×80'), furnP1('chair',1750,4300,2200,4750), furnP1('chair',2200,4300,2650,4750), furnP1('chair',1750,5650,2200,6100), furnP1('chair',2200,5650,2650,6100)]
items += [furnP1('tv',6420,2200,6820,3800,'RTV'), furnP1('sofa',4100,2000,5000,4200,'sofa 220'), furnP1('coffee',5200,2600,5800,3600,'ława'), furnP1('armchair',4300,4500,5100,5300)]
# gabinet / pokój 3
items += [furnP1('desk',1500,8360,2700,8960,'biurko'), furnP1('chair',1875,7850,2325,8300), furnP1('shoe',3640,7000,4240,9020,'regał'), furnP1('sofa',740,6960,2740,7860,'kanapa 200')]
# sypialnia 1
items += [furnP1('bed',1400,10340,3000,12340), furnP1('night',950,11940,1350,12340), furnP1('night',3050,11940,3450,12340), furnP1('wardrobe',1500,9200,3500,9800,'szafa 200')]
# sypialnia 2
items += [furnP1('bed',2200,13120,3800,15120), furnP1('night',1750,14720,2150,15120), furnP1('night',3850,14720,4250,15120), furnP1('desk',740,13500,1340,14700,'biurko'), furnP1('chair',1400,13880,1850,14330), furnP1('wardrobe',6160,12460,6760,14460,'szafa 200')]
# łazienka (1,26 × 2,72)
items += [furnP1('shower',5920,11440,6820,12340), furnP1('wc',6400,10500,6800,11150), furnP1('basin',6360,9700,6760,10200), furnP1('washer',5600,9680,6200,10280)]
# korytarz
items += [furnP1('pax150s',4420,10800,4770,12300,'PAX 150×35')]

# ============ WARIANT P2: 108 = dwa mieszkania (M1a płd., M1b płn.) — wersja umeblowana ============
v='P2'
YS = 6840   # oś ściany dzielącej (lica 6780 / 6900)
def furn(kind, x0, y0, x1, y1, label=None, v=v):
    d={'id':uid(),'type':'furn','kind':kind,'pts':[[x0,y0],[x1,y1]],'v':v}
    if label: d['label']=label
    return d
def doorO(a,b,v,flip=False,open_=False):
    d={'id':uid(),'type':'door','pts':[a,b],'w':300,'v':v}
    if flip: d['flip']=True
    if open_: d['open']=True
    return d
# --- ściany wspólne / wiatrołap ---
items.append(wall([[XW,YS],[XE,YS]], v))                            # podział płd./płn. na całej szerokości
items.append(wall([[5600,YS],[5600,9080]], v))                      # wiatrołap | przedpokój M1b
items.append(wall([[5600,9080],[5880,9080]], v))                    # wiatrołap | szacht (do występu)
items.append(doorO([5700,YS],[6600,YS], v, flip=True))              # drzwi M1a (otwierane do M1a, na płd.)
items.append(doorO([5600,7300],[5600,8200], v))                     # drzwi M1b (do przedpokoju, na zach.)
items.append(room([[5600+H,YS+H],[XE,YS+H],[XE,9080-H],[5600+H,9080-H]], 'wiatrołap wspólny', 'W', v))
items.append(note([6200,8300], 'istn. drzwi 2-skrz. 1,2 m z korytarza 102 zostają; 2 drzwi EI 30 do mieszkań', v))
items.append(note([5750,9320], 'wnęka przy występie 0,28×0,48 m = szacht wentylacyjny/instalacyjny', v))
# --- M1a (płd., ok. 35,5 m²) ---
items.append(wall([[XW,3400],[3800,3400]], v))                      # sypialnia | salon
items.append(wall([[3800,3400],[3800,6780]], v))                    # sypialnia | aneks kuchenny
items.append(wall([[5450,3400],[XE,3400]], v))                      # łazienka | salon
items.append(wall([[5450,3400],[5450,5500]], v))                    # łazienka | aneks
items.append(wall([[5450,5500],[XE,5500]], v))                      # łazienka | przedpokój
items.append(doorO([2850,3400],[3650,3400], v))                     # sypialnia (80) z salonu
items.append(doorO([5900,5500],[6700,5500], v))                     # łazienka (80), otwierane na zewnątrz do przedpokoju
items.append(room([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,3400-H],[XW,3400-H]], 'pokój dzienny', 'M1a', v))
items.append(room([[XW,3400+H],[3800-H,3400+H],[3800-H,6780],[XW,6780]], 'sypialnia', 'M1a', v))
items.append(room([[3800+H,3400+H],[5450-H,3400+H],[5450-H,6780],[3800+H,6780]], 'aneks kuchenny', 'M1a', v))
items.append(room([[5450+H,3400+H],[XE,3400+H],[XE,5500-H],[5450+H,5500-H]], 'łazienka', 'M1a', v))
items.append(room([[5450+H,5500+H],[XE,5500+H],[XE,6780],[5450+H,6780]], 'przedpokój', 'M1a', v))
# meble M1a — pokój dzienny
items.append(furn('sofa', 700, 2440, 2700, 3340, 'sofa 200'))        # sofa pod ścianą sypialni, tyłem do niej
items.append(furn('coffee', 1300, 1600, 2300, 2200))
items.append(furn('tv', 760, 760, 2360, 1160, 'RTV (ściana płd., obok okna)'))
items.append(furn('table', 3000, 1500, 4400, 2300))                  # stół przy oknie płd.
for cx in (3250, 4150):
    items.append(furn('chair', cx-225, 1000, cx+225, 1450)); items.append(furn('chair', cx-225, 2350, cx+225, 2800))
# meble M1a — sypialnia (3,06 × 3,32)
items.append(furn('bed', 1500, 4780, 3100, 6780))
items.append(furn('night', 1020, 6380, 1470, 6780)); items.append(furn('night', 3130, 6380, 3580, 6780))
items.append(furn('wardrobe', 740, 3460, 2740, 4060))
# meble M1a — aneks kuchenny (galeria 1,53 szer.): ciąg wzdłuż ściany sypialni x=3800
items.append(furn('fridge', 3860, 6170, 4460, 6770))
items.append(furn('washer', 3860, 5570, 4460, 6170))
items.append(furn('counter', 3860, 5270, 4460, 5570, 'blat'))
items.append(furn('hob', 3860, 4670, 4460, 5270))
items.append(furn('counter', 3860, 4370, 4460, 4670, 'blat'))
items.append(furn('sink', 3860, 3770, 4460, 4370))
items.append(furn('counter', 3860, 3460, 4460, 3770, 'blat'))
# meble M1a — łazienka (1,31 × 2,04)
items.append(furn('shower', 5920, 3460, 6820, 4360))
items.append(furn('wc', 6400, 4500, 6800, 5150))
items.append(furn('basin', 5510, 5040, 5910, 5440))
# meble M1a — przedpokój
# --- M1b (płn., ok. 45 m²) ---
items.append(wall([[4300,YS],[4300,9200]], v))                      # przedpokój | kuchnia (część płd.)
items.append(wall([[4300,10200],[4300,12400]], v))                  # przedpokój | salon (część płn.); między 9200–10200 otwór
items.append(doorO([4300,9200],[4300,10200], v, open_=True))        # otwór 1,0 m do salonu
items.append(wall([[5600,9560],[5600,12400]], v))                   # przedpokój | łazienka
items.append(wall([[5600,9560],[5880,9560]], v))                    # łazienka | szacht
items.append(wall([[XW,12400],[XE,12400]], v))                      # sypialnia
items.append(doorO([5600,10200],[5600,11000], v))                   # łazienka (80), do środka
items.append(doorO([4500,12400],[5400,12400], v))                   # sypialnia (90), do sypialni
items.append(room([[4300+H,YS+H],[5600-H,YS+H],[5600-H,12400-H],[4300+H,12400-H]], 'przedpokój', 'M1b', v))
items.append(room([[XW,YS+H],[4300-H,YS+H],[4300-H,12400-H],[XW,12400-H]], 'pokój dzienny + aneks', 'M1b', v))
items.append(room([[5600+H,9560+H],[XE,9560+H],[XE,12400-H],[5600+H,12400-H]], 'łazienka', 'M1b', v))
items.append(room([[XW,12400+H],[XE,12400+H],[XE,YN],[XW,YN]], 'sypialnia', 'M1b', v))
# meble M1b — aneks kuchenny wzdłuż ściany działowej (y=6900), zlew plecami do zlewu M1a
items.append(furn('fridge', 3640, 6960, 4240, 7610))
items.append(furn('counter', 3040, 6960, 3640, 7560, 'blat'))
items.append(furn('hob', 2440, 6960, 3040, 7560))
items.append(furn('counter', 1840, 6960, 2440, 7560, 'blat'))
items.append(furn('sink', 1240, 6960, 1840, 7560))
items.append(furn('counter', 740, 6960, 1240, 7560, 'blat'))
items.append(furn('table4', 1500, 8300, 2700, 9100))
for cy in (7850, 9150): items.append(furn('chair', 1875, cy-225, 2325, cy+225)); items.append(furn('chair', 2325-225+450, cy-225, 2325+450, cy+225))
# meble M1b — część dzienna
items.append(furn('sofa', 900, 9900, 3100, 10800))                   # sofa tyłem do jadalni, przodem na północ
items.append(furn('coffee', 1500, 11000, 2500, 11600))
items.append(furn('tv', 1200, 11940, 2800, 12340, 'RTV'))
items.append(furn('armchair', 3340, 11400, 4140, 12200))
# meble M1b — łazienka (1,16 × 2,78), ciąg przy ścianie wsch.
items.append(furn('shower', 5920, 11440, 6820, 12340))
items.append(furn('wc', 6400, 10500, 6800, 11150))
items.append(furn('basin', 6360, 9700, 6760, 10200))
items.append(furn('washer', 5660, 9620, 6260, 10220))
# meble M1b — sypialnia (6,14 × 2,72)
items.append(furn('bed', 2000, 13120, 3600, 15120))
items.append(furn('night', 1500, 14720, 1950, 15120)); items.append(furn('night', 3650, 14720, 4100, 15120))
items.append(furn('wardrobe', 6160, 12460, 6760, 14460, 'szafa 200'))
items.append(furn('desk', 740, 13500, 1340, 14700, 'biurko'))
items.append(furn('chair', 1400, 13880, 1850, 14330))
# meble M1b — przedpokój (1,18 szer.): szafa 40 gł. przy ścianie zach.
items.append(furn('pax150s', 4360, 10800, 4710, 12300, 'PAX 150×35'))


# ============ WARIANT P3: kawalerka (płd.) + 3 pokoje (płn.) ============
v='P3'
F=lambda kind,x0,y0,x1,y1,label=None: furn(kind,x0,y0,x1,y1,label,v=v)
D=lambda a,b,flip=False,open_=False: doorO(a,b,v,flip=flip,open_=open_)
YD=5700  # oś ściany dzielącej (okno zach. 4252–5622 zostaje w kawalerce)
# wspólne
items.append(wall([[XW,YD],[XE,YD]], v))                            # podział
items.append(wall([[5600,YD],[5600,9080]], v))                      # wiatrołap (korytarzyk wspólny 1,22 × 3,38)
items.append(wall([[5600,9080],[5880,9080]], v))
items.append(D([5700,YD],[6600,YD], flip=True))                     # drzwi kawalerki (na płd.)
items.append(D([5600,8000],[5600,8900]))                            # drzwi M3b – wprost do pokoju dziennego
items.append(room([[5600+H,YD+H],[XE,YD+H],[XE,9080-H],[5600+H,9080-H]], 'wiatrołap wspólny', 'W', v))
items.append(note([6200,8300], 'istn. drzwi 1,2 m z korytarza 102; wiatrołap 4,1 m² – dłuższy niż w P2', v))
# --- S: kawalerka M3a ---
items.append(wall([[5450,2700],[5450,4700]], v)); items.append(wall([[5450,2700],[XE,2700]], v)); items.append(wall([[5450,4700],[XE,4700]], v))
items.append(D([5600,4700],[6400,4700]))                            # łazienka, na zewnątrz
items.append(room([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,2700-H],[5450-H,2700-H],[5450-H,4700+H],[XE,4700+H],[XE,YD-H],[XW,YD-H]], 'pokój z aneksem kuchennym', 'M3a', v))
items.append(room([[5450+H,2700+H],[XE,2700+H],[XE,4700-H],[5450+H,4700-H]], 'łazienka', 'M3a', v))
# aneks wzdłuż ściany działowej (y=5640)
items.append(F('fridge',740,4990,1340,5640)); items.append(F('washer',1340,5040,1940,5640)); items.append(F('counter',1940,5040,2540,5640,'blat'))
items.append(F('sink',2540,5040,3140,5640)); items.append(F('counter',3140,5040,3740,5640,'blat')); items.append(F('hob',3740,5040,4340,5640)); items.append(F('counter',4340,5040,4740,5640,'blat'))
items.append(F('bed',740,2900,2740,4300,'łóżko 140×200')); items.append(F('night',740,4320,1140,4720))
items.append(F('pax150',740,760,2240,1340,'PAX 150×58'))
items.append(F('sofa',3400,2600,4300,4800,'sofa 220')); items.append(F('coffee',4450,3300,4950,4000,'stolik'))
items.append(F('tv',4990,3000,5390,4400,'RTV'))
items.append(F('table4',3100,1250,4300,2050)); items.append(F('chair',2600,1425,3050,1875)); items.append(F('chair',4350,1425,4800,1875))
items.append(F('shower',5920,2760,6820,3660)); items.append(F('wc',6400,3800,6800,4450)); items.append(F('basin',5510,4240,5910,4640))
# --- N: M3b 3 pokoje ---
items.append(wall([[XW,9300],[4300,9300]], v))                      # pokój dzienny | sypialnia 1
items.append(wall([[4300,9300],[4300,12400]], v))                   # korytarz zach.
items.append(wall([[5600,9560],[5600,12400]], v)); items.append(wall([[5600,9560],[5880,9560]], v))  # łazienka
items.append(wall([[XW,12400],[XE,12400]], v))                      # sypialnia 2 + garderoba
items.append(wall([[5600,12400],[5600,YN]], v))                     # garderoba
items.append(D([4300,9300],[5600,9300], open_=True))                # otwór 1,3 m z pokoju dziennego do korytarza
items.append(D([4300,11400],[4300,12300]))                          # sypialnia 1 (90)
items.append(D([5600,10200],[5600,11000]))                          # łazienka (80), na zewnątrz
items.append(D([4500,12400],[5400,12400]))                          # sypialnia 2 (90)
items.append(D([5600,13000],[5600,13800], flip=True))               # garderoba (80)
items.append(room([[XW,YD+H],[5600-H,YD+H],[5600-H,9300-H],[XW,9300-H]], 'pokój dzienny z aneksem', 'M3b', v))
items.append(room([[4300+H,9300+H],[5600-H,9300+H],[5600-H,12400-H],[4300+H,12400-H]], 'korytarz', 'M3b', v))
items.append(room([[XW,9300+H],[4300-H,9300+H],[4300-H,12400-H],[XW,12400-H]], 'sypialnia 1', 'M3b', v))
items.append(room([[5600+H,9560+H],[XE,9560+H],[XE,12400-H],[5600+H,12400-H]], 'łazienka', 'M3b', v))
items.append(room([[XW,12400+H],[5600-H,12400+H],[5600-H,YN],[XW,YN]], 'sypialnia 2', 'M3b', v))
items.append(room([[5600+H,12400+H],[XE,12400+H],[XE,YN],[5600+H,YN]], 'garderoba', 'M3b', v))
# meble pokój dzienny: kuchnia w L przy ścianie wiatrołapu i działowej
items.append(F('fridge',4940,7300,5540,7950)); items.append(F('counter',4940,6700,5540,7300,'blat')); items.append(F('sink',4940,6100,5540,6700)); items.append(F('counter',4940,5760,5540,6100,'blat'))
items.append(F('hob',4340,5760,4940,6360)); items.append(F('counter',3740,5760,4340,6360,'blat')); items.append(F('counter',3140,5760,3740,6360,'blat'))
items.append(F('sofa',740,5760,2940,6660,'sofa 220')); items.append(F('coffee',1300,6900,2300,7500))
items.append(F('tv',1000,8840,2600,9240,'RTV')); items.append(F('table4',3100,7500,4300,8300))
items.append(F('chair',3375,7000,3825,7450)); items.append(F('chair',3375,8350,3825,8800)); items.append(F('chair',3900,7000,4350,7450)); items.append(F('chair',3900,8350,4350,8800))
# sypialnia 1 (3,56 × 2,98)
items.append(F('bed',1400,10340,3000,12340)); items.append(F('night',950,11940,1350,12340)); items.append(F('night',3050,11940,3450,12340))
items.append(F('wardrobe',1500,9400,3500,10000,'szafa 200'))
# sypialnia 2 (4,86 × 2,72) + garderoba
items.append(F('bed',2200,13120,3800,15120)); items.append(F('night',1750,14720,2150,15120)); items.append(F('night',3850,14720,4250,15120))
items.append(F('desk',740,13500,1340,14700,'biurko')); items.append(F('chair',1400,13880,1850,14330))
items.append(F('wardrobe',6220,12460,6820,14460,'szafa 200')); items.append(F('shoe',5660,14600,6060,15120,'regał'))
# łazienka N (1,16 × 2,72)
items.append(F('shower',5920,11440,6820,12340)); items.append(F('wc',6400,10500,6800,11150)); items.append(F('basin',6360,9700,6760,10200)); items.append(F('washer',5660,9620,6260,10220))
items.append(F('pax150s',4360,10800,4710,12300,'PAX 150×35'))

# ============ WARIANT P4: 1 mieszkanie, 4 sypialnie + kuchnia-jadalnia + 2 łazienki + WC (najem pokojowy) ============
v='P4'
F=lambda kind,x0,y0,x1,y1,label=None: furn(kind,x0,y0,x1,y1,label,v=v)
D=lambda a,b,flip=False,open_=False: doorO(a,b,v,flip=flip,open_=open_)
XR=4100; XC=5300   # oś ściany pokoje|korytarz, korytarz|pas wschodni
items.append(wall([[XW,3400],[XE,3400]], v))                        # kuchnia | reszta
items.append(wall([[XR,3400],[XR,YN]], v))                          # pokoje | korytarz
items.append(wall([[XC,3400],[XC,6900]], v)); items.append(wall([[XC,9560],[XC,YN]], v))  # korytarz | pas wsch. (hol 6,9–9,56 otwarty)
for yy in (6280, 9300, 12350): items.append(wall([[XW,yy],[XR,yy]], v))   # podziały pokoi
for yy in (5500, 6900, 11800, 13200): items.append(wall([[XC,yy],[XE,yy]], v))  # podziały pasa wsch.
items.append(wall([[XC,9560],[5880,9560]], v))                      # Ł2 od wnęki/występu
items.append(D([4250,3400],[5150,3400], flip=True))                 # kuchnia (90) z końca korytarza
for y0 in (3550, 6430, 9450, 12500): items.append(D([XR,y0],[XR,y0+800]))   # pokoje (80), do środka
items.append(D([XC,3600],[XC,4400], flip=True))                     # Ł1 do środka
items.append(D([XC,5700],[XC,6500]))                                # WC na zewnątrz
items.append(D([XC,9700],[XC,10500]))                               # Ł2 na zewnątrz
items.append(D([XC,11950],[XC,12750])); items.append(D([XC,13400],[XC,14200]))
items.append(room([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,3400-H],[XW,3400-H]], 'kuchnia z jadalnią', 'M1', v))
rooms_y=[(3400,6280,'pokój 1'),(6280,9300,'pokój 2'),(9300,12350,'pokój 3'),(12350,YN,'pokój 4')]
for y0,y1,nm in rooms_y:
    items.append(room([[XW,y0+H],[XR-H,y0+H],[XR-H,y1-(H if y1!=YN else 0)],[XW,y1-(H if y1!=YN else 0)]], nm, 'M1', v))
items.append(room([[XR+H,3400+H],[XC-H,3400+H],[XC-H,6900+H],[XE,6900+H],[XE,9080],[5880,9080],[5880,9560-H],[XC-H,9560-H],[XC-H,YN],[XR+H,YN]], 'korytarz + hol wejściowy', 'M1', v))
items.append(room([[XC+H,3400+H],[XE,3400+H],[XE,5500-H],[XC+H,5500-H]], 'łazienka 1', 'M1', v))
items.append(room([[XC+H,5500+H],[XE,5500+H],[XE,6900-H],[XC+H,6900-H]], 'WC', 'M1', v))
items.append(room([[XC+H,9560+H],[XE,9560+H],[XE,11800-H],[XC+H,11800-H]], 'łazienka 2', 'M1', v))
items.append(room([[XC+H,11800+H],[XE,11800+H],[XE,13200-H],[XC+H,13200-H]], 'pralnia', 'M1', v))
items.append(room([[XC+H,13200+H],[XE,13200+H],[XE,YN],[XC+H,YN]], 'schowek', 'M1', v))
items.append(note([4700,8000], 'układ pod najem pokojowy: 4 pokoje 9–10 m², wspólna kuchnia 15,5 m², 2 łazienki + WC; korytarz 1,2 m', v))
# kuchnia-jadalnia: ciąg L przy ścianie wsch. i płn.
items.append(F('fridge',6220,1000,6820,1650)); items.append(F('counter',6220,1650,6820,2150,'blat')); items.append(F('sink',6220,2150,6820,2750)); items.append(F('counter',6220,2750,6820,3340,'blat'))
items.append(F('hob',5620,2740,6220,3340)); items.append(F('counter',5160,2740,5620,3340,'blat'))
items.append(F('table',2200,1500,3600,2300,'stół 140×80'))
for cx in (2500,3300): items.append(F('chair',cx-225,1000,cx+225,1450)); items.append(F('chair',cx-225,2350,cx+225,2800))
items.append(F('chair',1700,1675,2150,2125)); items.append(F('chair',3650,1675,4100,2125))
items.append(F('sofa',4400,1000,5200,2400,'sofa/ławka'))
# pokoje: łóżko 90×200 przy ścianie płn., szafa przy płd., biurko przy wsch. nad drzwiami
for y0,y1,nm in rooms_y:
    top = y1-(H if y1!=YN else 0)
    items.append(F('bed1',740,top-900,2740,top,'łóżko 90×200'))
    items.append(F('pax150',740,y0+H,2240,y0+H+580,'PAX 150×58'))
    items.append(F('desk',XR-H-600,y0+1200,XR-H,y0+2400,'biurko'))
    items.append(F('chair',XR-H-1100,y0+1575,XR-H-650,y0+2025))
# Ł1 (1,46 × 1,98)
items.append(F('shower',5920,4540,6820,5440)); items.append(F('basin',5400,5040,5900,5440)); items.append(F('wc',6400,3500,6800,4150))
# WC (1,46 × 1,28)
items.append(F('wc',6400,5700,6800,6350)); items.append(F('basin',5420,6440,5820,6840))
# Ł2 (1,46 × 2,12)
items.append(F('shower',5920,10840,6820,11740)); items.append(F('washer',5360,9620,5960,10220)); items.append(F('wc',6400,9700,6800,10350)); items.append(F('basin',5400,10500,5900,10900))
# pralnia, schowek
items.append(F('washer',6220,11860,6820,12460)); items.append(F('washer',6220,12520,6820,13120,'suszarka')); items.append(F('shoe',5360,11860,5760,13140,'regał'))
items.append(F('shoe',6220,13260,6820,15182,'regał')); items.append(F('shoe',5360,14400,5760,15182,'regał'))


# ======================= WARIANTY JEDNEGO MIESZKANIA P5–P8 =======================
def mk(v):
    W=lambda a,b: items.append(wall([a,b],v))
    D=lambda a,b,flip=False,open_=False: items.append(doorO(a,b,v,flip=flip,open_=open_))
    R=lambda pts,label: items.append(room(pts,label,'M1',v))
    F=lambda kind,x0,y0,x1,y1,label=None: items.append(furn(kind,x0,y0,x1,y1,label,v=v))
    N=lambda p,txt: items.append(note(p,txt,v))
    return W,D,R,F,N
def south_face_poly(y_top, x_left=XW, x_right=XE):
    """obrys od lica płd. do y_top"""
    pts=[[x_left,ys(x_left)]]
    for q in ([2475,732],[2480,760],[5100,880]):
        if x_left<q[0]<x_right: pts.append(q)
    pts += [[x_right,ys(x_right)],[x_right,y_top],[x_left,y_top]]
    return pts
# standardowe zestawy mebli
def bed_north_full(F, extra=True):   # sypialnia y 12460–15182 pełna szerokość
    F('bed',2200,13120,3800,15120); F('night',1750,14720,2150,15120); F('night',3850,14720,4250,15120)
    if extra: F('desk',740,13500,1340,14700,'biurko'); F('chair',1400,13880,1850,14330); F('wardrobe',6160,12460,6760,14460,'szafa 200')
def bed_west(F, x1=4300, y0=9300, y1=12400):  # sypialnia zach. x 680–x1
    F('bed',1400,y1-2060,3000,y1-60); F('night',950,y1-460,1350,y1-60); F('night',3050,y1-460,3450,y1-60); F('wardrobe',1500,y0+100,3500,y0+700,'szafa 200')
def bed_south_full(F, door_x=(5700,6600)):   # sypialnia płd. pełna szer., y do 3400
    F('bed',740,1500,2740,3100,'łóżko 160×200'); F('night',2800,2700,3200,3100); F('wardrobe',3000,2740,5000,3340,'szafa 200'); F('desk',4400,950,5600,1550,'biurko'); F('chair',4775,1600,5225,2050)
def bath_east(F, x0=5600, y0=9560, y1=12400, washer=True):  # łazienka przy ścianie wsch.
    F('shower',5920,y1-960,6820,y1-60); F('wc',6400,y0+940,6800,y0+1590); F('basin',6360,y0+140,6760,y0+640)
    if washer: F('washer',x0+60,y0+60,x0+660,y0+660)
def living_south(F, y_top, kitchen_y=None, wc_block=False):
    """salon w paśmie płd. do y_top; kuchnia przy ścianie płn. (y_top) jeśli kitchen_y, inaczej bez"""
    if kitchen_y:
        y=kitchen_y
        F('fridge',3640,y-650,4240,y); F('counter',3040,y-600,3640,y,'blat'); F('hob',2440,y-600,3040,y); F('counter',1840,y-600,2440,y,'blat'); F('sink',1240,y-600,1840,y); F('counter',740,y-600,1240,y,'blat')
    F('tv',6420,1300,6820,2900,'RTV'); F('sofa',4100,1100,5000,3300,'sofa 220'); F('coffee',5200,1700,5800,2700,'ława')
    F('table',1500,2900,2900,3700,'stół 140×80'); F('chair',1750,2400,2200,2850); F('chair',2200,2400,2650,2850); F('chair',1750,3750,2200,4200); F('chair',2200,3750,2650,4200)

# ---------- P5: salon od północy, 2 łazienki, strefa dzieci od południa ----------
v='P5'; W,D,R,F,N=mk(v)
W([XW,3400],[XE,3400]); W([3900,3400],[3900,6900]); W([3900,5600],[5600,5600]); W([5600,3400],[5600,5600])
W([XW,6900],[XE,6900]); W([4300,6900],[4300,9300]); W([XW,9300],[4300,9300])
W([5300,9560],[5300,12400]); W([5300,9560],[5880,9560]); W([5300,12400],[XE,12400])
D([5700,3400],[6600,3400],flip=True)      # sypialnia 1 (z korytarza)
D([3900,5700],[3900,6600])                # sypialnia 2
D([4600,5600],[5400,5600])                # łazienka 2 (na zewnątrz, do korytarza)
D([5700,6900],[6700,6900],open_=True)     # hol → korytarz płd.
D([4300,7300],[4300,8200])                # gabinet
D([4300,9300],[5300,9300],open_=True)     # hol → salon
D([5300,10200],[5300,11000])              # łazienka 1
R(south_face_poly(3340),'sypialnia 1'); R([[XW,3460],[3840,3460],[3840,6840],[XW,6840]],'sypialnia 2')
R([[3960,3460],[5540,3460],[5540,5540],[3960,5540]],'łazienka 2 (dzieci)')
R([[3960,5660],[5540,5660],[5540,3460],[6820,3460],[6820,6840],[3960,6840]],'korytarz')
R([[XW,6960],[4240,6960],[4240,9240],[XW,9240]],'gabinet'); R([[4360,6960],[6820,6960],[6820,9080],[5880,9080],[5880,9240],[4360,9240]],'hol')
R([[5360,9620],[6820,9620],[6820,12340],[5360,12340]],'łazienka 1')
R([[XW,9360],[5240,9360],[5240,12460],[6820,12460],[6820,YN],[XW,YN]],'salon z aneksem kuchennym')
N([5700,4600],'korytarz 1,2 m: dojście do syp. 1 i łazienki 2')
bed_south_full(F); bed_west(F,x1=3900,y0=3400,y1=6900)
F('shower',4620,3460,5520,4360); F('wc',3980,4500,4380,5150); F('basin',4700,5140,5200,5540)
F('desk',2200,8640,3400,9240,'biurko'); F('chair',2575,8150,3025,8600); F('sofa',740,6960,2740,7860,'kanapa 200'); F('shoe',3640,8400,4240,9240,'regał')
F('pax150s',4420,7000,4770,8500,'PAX 150×35')
bath_east(F,x0=5300)
F('fridge',6160,14580,6760,15180); F('counter',5560,14580,6160,15180,'blat'); F('hob',4960,14580,5560,15180); F('counter',4360,14580,4960,15180,'blat'); F('sink',3760,14580,4360,15180); F('counter',3200,14580,3760,15180,'blat')
F('table4',4000,12800,5200,13600); F('chair',4275,12300,4725,12750); F('chair',4275,13650,4725,14100); F('chair',4800,12300,5250,12750); F('chair',4800,13650,5250,14100)
F('tv',740,11800,1140,12900,'RTV'); F('sofa',2500,11200,3400,13400,'sofa 220'); F('coffee',1700,11900,2300,12700,'ława')

# ---------- P6: 3 sypialnie + salon 23, garderoba, WC, pralnia ----------
v='P6'; W,D,R,F,N=mk(v)
W([3900,3400],[5600,3400]); W([3900,3400],[3900,9300]); W([5600,3400],[5600,6900]); W([3900,5400],[5600,5400]); W([XW,5600],[3900,5600])
W([3900,6900],[XE,6900]); W([XW,9300],[4300,9300]); W([4300,9300],[4300,12400]); W([5600,9560],[5600,12400]); W([5600,9560],[5880,9560])
W([XW,12400],[XE,12400]); W([5500,12400],[5500,YN])
D([5600,4500],[5600,5300])                # pralnia/schowek (z przejścia)
D([4500,6900],[5300,6900])                # WC (do holu)
D([5700,6900],[6700,6900],open_=True)     # hol → przejście do salonu
D([3900,7300],[3900,8200])                # sypialnia 1
D([4300,9700],[4300,10600])               # sypialnia 2
D([5600,10200],[5600,11000])              # łazienka
D([4400,12400],[5300,12400])              # sypialnia 3
D([5500,13000],[5500,13800],flip=True)    # garderoba (z sypialni 3)
R([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,3340],[3840,3340],[3840,5540],[XW,5540]],'salon z aneksem kuchennym')
R([[5660,3400],[6820,3400],[6820,6840],[5660,6840]],'przejście do salonu')
R([[3960,3460],[5540,3460],[5540,5340],[3960,5340]],'pralnia / schowek'); R([[3960,5460],[5540,5460],[5540,6840],[3960,6840]],'WC')
R([[XW,5660],[3840,5660],[3840,9240],[XW,9240]],'sypialnia 1'); R([[3960,6960],[6820,6960],[6820,9080],[5880,9080],[5880,9240],[3960,9240]],'hol')
R([[XW,9360],[4240,9360],[4240,12340],[XW,12340]],'sypialnia 2'); R([[4360,9360],[5540,9360],[5540,12340],[4360,12340]],'korytarz')
R([[5660,9620],[6820,9620],[6820,12340],[5660,12340]],'łazienka'); R([[XW,12460],[5440,12460],[5440,YN],[XW,YN]],'sypialnia 3'); R([[5560,12460],[6820,12460],[6820,YN],[5560,YN]],'garderoba')
# salon: kuchnia przy ścianie schowka (x=3,9) i pod ścianą syp.1 (y=5,6)
F('fridge',3240,4940,3840,5540); F('counter',2640,4940,3240,5540,'blat'); F('sink',2040,4940,2640,5540); F('counter',1440,4940,2040,5540,'blat'); F('hob',840,4940,1440,5540)
F('table',3000,1500,4400,2300,'stół 140×80'); F('chair',3250,1000,3700,1450); F('chair',4150,1000,4600,1450); F('chair',3250,2350,3700,2800); F('chair',4150,2350,4600,2800)
F('sofa',740,2000,1640,4200,'sofa 220'); F('tv',2000,3900,3600,4300,'RTV'); F('coffee',1800,2600,2400,3600,'ława')
F('washer',3980,3480,4580,4080); F('washer',4700,3480,5300,4080,'suszarka'); F('shoe',3980,4700,4700,5100,'regał')
F('wc',4400,6400,4800,7050 if False else 6840); F('basin',5040,5500,5440,5900)
F('bed',1300,7180,2900,9180); F('night',850,8780,1250,9180); F('night',2950,8780,3350,9180); F('wardrobe',740,5720,2740,6320,'szafa 200')
F('pax150s',4020,7000,4370,8500,'PAX 150×35')
bed_west(F); bath_east(F,washer=False)
F('bed',2000,13120,3600,15120); F('night',1550,14720,1950,15120); F('night',3650,14720,4050,15120); F('desk',740,13500,1340,14700,'biurko'); F('chair',1400,13880,1850,14330)
F('wardrobe',5640,12520,6220,14520,'PAX 200×58'); F('shoe',6300,12520,6760,15120,'regał')
N([5000,2600],'strefa dzienna 23 m² z aneksem; 3 sypialnie 12 / 10,6 / 13 m²')

# ---------- P7: kuchnia osobna z oknem, 3 sypialnie ----------
v='P7'; W,D,R,F,N=mk(v)
W([XW,3400],[XE,3400]); W([5600,3400],[5600,6900]); W([XW,6900],[XE,6900]); W([4300,6900],[4300,12400]); W([XW,9300],[4300,9300])
W([5600,9560],[5600,12400]); W([5600,9560],[5880,9560]); W([XW,12400],[XE,12400])
D([5700,3400],[6600,3400],flip=True)      # sypialnia 1
D([5600,5000],[5600,6000])                # salon (drzwi 1,0 m)
D([5700,6900],[6700,6900],open_=True)     # hol → przejście
D([4300,7300],[4300,8200])                # kuchnia
D([4300,9700],[4300,10600])               # sypialnia 2
D([5600,10200],[5600,11000])              # łazienka
D([4500,12400],[5400,12400])              # sypialnia 3
R(south_face_poly(3340),'sypialnia 1'); R([[XW,3460],[5540,3460],[5540,6840],[XW,6840]],'salon'); R([[5660,3460],[6820,3460],[6820,6840],[5660,6840]],'przejście')
R([[XW,6960],[4240,6960],[4240,9240],[XW,9240]],'kuchnia z jadalnią'); R([[4360,6960],[6820,6960],[6820,9080],[5880,9080],[5880,9240],[4360,9240]],'hol')
R([[XW,9360],[4240,9360],[4240,12340],[XW,12340]],'sypialnia 2'); R([[4360,9360],[5540,9360],[5540,12340],[4360,12340]],'korytarz')
R([[5660,9620],[6820,9620],[6820,12340],[5660,12340]],'łazienka'); R([[XW,12460],[XE,12460],[XE,YN],[XW,YN]],'sypialnia 3')
bed_south_full(F)
F('sofa',740,5940,2940,6840,'sofa 220'); F('coffee',1300,4900,2300,5500,'ława'); F('tv',1000,3460,2600,3860,'RTV'); F('armchair',3300,5900,4100,6700); F('desk',4300,3460,5500,4060,'biurko / komoda')
F('fridge',3640,6960,4240,7610); F('counter',3040,6960,3640,7560,'blat'); F('hob',2440,6960,3040,7560); F('counter',1840,6960,2440,7560,'blat'); F('sink',1240,6960,1840,7560); F('counter',740,6960,1240,7560,'blat')
F('table4',1500,8200,2700,9000); F('chair',1775,7700,2225,8150); F('chair',2250,7700,2700,8150); F('chair',1775,9050 if False else 8600,2225,9050) if False else None
F('chair',1000,8375,1450,8825); F('chair',2750,8375,3200,8825)
F('pax150s',4420,7000,4770,8500,'PAX 150×35')
bed_west(F); bath_east(F); bed_north_full(F)
N([2500,5300],'kuchnia zamknięta 8 m² z oknem; salon 17 m²; sypialnie 15,6 / 10,6 / 17 m²')

# ---------- P8: kuchnia-jadalnia w sercu mieszkania, salon 34, 2 sypialnie ----------
v='P8'; W,D,R,F,N=mk(v)
W([XW,6900],[XE,6900]); W([5000,5400],[5000,6900]); W([5000,5400],[XE,5400])
W([XW,9300],[4300,9300]); W([4300,9300],[4300,12400]); W([5600,9560],[5600,12400]); W([5600,9560],[5880,9560]); W([XW,12400],[XE,12400])
D([1000,6900],[4000,6900],open_=True)     # salon ↔ kuchnia-jadalnia (otwór 3 m)
D([5300,6900],[6100,6900])                # WC/pralnia (do jadalni)
D([4300,9300],[5600,9300],open_=True)     # jadalnia → korytarz
D([4300,9700],[4300,10600])               # sypialnia 1
D([5600,10200],[5600,11000])              # łazienka
D([4500,12400],[5400,12400])              # sypialnia 2
R([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,5340],[4940,5340],[4940,6840],[XW,6840]],'salon')
R([[5060,5460],[6820,5460],[6820,6840],[5060,6840]],'WC + pralnia')
R([[XW,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9240],[4300,9240],[4300,9240],[XW,9240]],'kuchnia z jadalnią / hol')
R([[XW,9360],[4240,9360],[4240,12340],[XW,12340]],'sypialnia 1'); R([[4360,9360],[5540,9360],[5540,12340],[4360,12340]],'korytarz')
R([[5660,9620],[6820,9620],[6820,12340],[5660,12340]],'łazienka'); R([[XW,12460],[XE,12460],[XE,YN],[XW,YN]],'sypialnia 2')
F('tv',6420,1300,6820,2900,'RTV'); F('sofa',4100,1100,5000,3300,'sofa 220'); F('coffee',5200,1700,5800,2700,'ława'); F('armchair',4200,3600,5000,4400)
F('desk',740,3500,1340,4700,'biurko'); F('chair',1400,3880,1850,4330); F('shoe',740,5900,2740,6300,'komoda'); F('sofa',2000,1000,4000,1900,'sofa 200')
F('wc',6400,5520,6800,6170); F('basin',5120,6400,5520,6800); F('washer',5120,5500,5720,6100)
F('fridge',3640,8640,4240,9240); F('counter',3040,8640,3640,9240,'blat'); F('hob',2440,8640,3040,9240); F('counter',1840,8640,2440,9240,'blat'); F('sink',1240,8640,1840,9240); F('counter',740,8640,1240,9240,'blat')
F('table',1600,7400,3000,8200,'stół 140×80'); F('chair',1850,6960,2300,7350); F('chair',2300,6960,2750,7350); F('chair',1000,7575,1450,8025); F('chair',3050,7575,3500,8025)
F('shoe',6420,7000,6820,7300,'szafka')
bed_west(F); bath_east(F,washer=False); bed_north_full(F)
N([2500,8000],'kuchnia-jadalnia 15 m² z oknem jako hol wejściowy; salon 34 m² przez otwór 3 m')


# ======================= RUNDA 3: P9–P13 — inne szkielety =======================
def bed_west_safe(F, x1, y0, y1):   # łóżko przy ścianie zach. (wolny narożnik płd.-wsch. na drzwi)
    F('bed',740,y1-2060,2340,y1-60); F('night',2400,y1-460,2800,y1-60); F('wardrobe',1500,y0+100,3500,y0+700,'szafa 200')

# ---------- P9: salon w sercu z kominkiem przy występie, wejście wprost do salonu ----------
v='P9'; W,D,R,F,N=mk(v)
W([XW,6900],[XE,6900]); W([XW,12400],[XE,12400]); W([4300,12400],[4300,YN])
W([XW,3400],[XE,3400]); W([3900,3400],[3900,6900]); W([5600,3400],[5600,6900]); W([3900,5400],[5600,5400])
D([3900,12400],[3000,12400],flip=True)    # sypialnia 1 – drzwi prawe (zawias od wsch.), do sypialni
D([4500,12400],[5300,12400])              # łazienka 1 – z salonu (po zmianie łazienki 2 na garderobę)
D([3850,6900],[2950,6900])                # sypialnia 3 – drzwi prawe (zawias od wsch.), do sypialni
D([5700,6900],[6700,6900],open_=True)     # salon → przejście płd.
D([6600,3400],[5700,3400])                # sypialnia 2 – drzwi prawe (zawias od wsch.), do sypialni
D([5600,4000],[5600,4800])                # garderoba – wejście po środku ściany wsch.
D([5600,5600],[5600,6400],flip=True)      # pom. gospodarcze (na zewnątrz)
R([[XW,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9560],[XE,9560],[XE,12340],[XW,12340]],'salon z aneksem (środek)')
R([[XW,12460],[4240,12460],[4240,YN],[XW,YN]],'sypialnia 1'); R([[4360,12460],[XE,12460],[XE,YN],[4360,YN]],'łazienka')
R(south_face_poly(3340),'sypialnia 2'); R([[XW,3460],[3840,3460],[3840,6840],[XW,6840]],'sypialnia 3')
R([[3960,3460],[5540,3460],[5540,5340],[3960,5340]],'garderoba'); R([[3960,5460],[5540,5460],[5540,6840],[3960,6840]],'pom. gospodarcze')
R([[5660,3460],[XE,3460],[XE,6840],[5660,6840]],'przejście')
N([6300,8400],'szafa wnękowa PAX 150 przy wejściu, ścianka w L od występu')
W([5880,9140],[5180,9140]); W([5180,9140],[5180,8420])
F('pax150',5240,8500,6740,9080,'PAX 150×58 (wnęka)')
N([6000,7300],'żeby zmieścić PAX 150 przy wejściu: drzwi z korytarza jako jednoskrzydłowe 90 cm (zawias płd., y 7,40–8,30), górna część otworu zamurowana')
N([4700,4300],'garderoba: PAX 150×58 po lewej, PAX 150×35 po prawej, przejście 0,95 m; łazienka na płn. z salonu, z pralką')
F('tv',740,11940,2340,12340,'RTV'); F('sofa',740,7000,2940,7900,'sofa 220'); F('coffee',1300,8300,2300,8900,'ława'); F('armchair',3200,7900,4000,8700)
F('fridge',6220,11740,6820,12340); F('counter',6220,11140,6820,11740,'blat'); F('sink',6220,10540,6820,11140); F('counter',6220,10040,6820,10540,'blat'); F('hob',6220,9640,6820,10240); F('counter',5340,11740,6220,12340,'blat')
F('table',3200,10000,4600,10800,'stół 140×80'); F('chair',3450,9500,3900,9950); F('chair',3900,9500,4350,9950); F('chair',3450,10850,3900,11300); F('chair',3900,10850,4350,11300)
F('bed',1400,13120,3000,15120); F('night',950,14720,1350,15120); F('night',3050,14720,3450,15120); F('pax175',3660,13350,4240,15100,'PAX 175×58')
F('bath',4420,14370,6120,15120); F('shower',5920,12520,6820,13420); F('wc',6400,13600,6800,14250); F('basin',4420,13900,4920,14300); F('washer',5500,12520,6100,13120,'pralka+suszarka (kolumna)')
bed_south_full(F); bed_west_safe(F,3900,3400,6900)
F('pax150',4000,3460,5500,4040,'PAX 150×58 (lewa)'); F('pax150s',4000,4990,5500,5340,'PAX 150×35 (prawa)')


# ---------- P10: loft – 49 m² otwartej przestrzeni + apartament sypialny bez korytarza ----------
v='P10'; W,D,R,F,N=mk(v)
W([5000,5400],[5000,6900]); W([5000,5400],[XE,5400])            # WC gościnne przy wejściu
W([XW,9300],[XE,9300]); W([4300,9300],[4300,YN]); W([4300,12400],[XE,12400])
D([5300,6900],[6100,6900])                 # WC (drzwi od strony wejścia)
W([5000,6900],[XE,6900])
D([3000,9300],[3900,9300])                 # sypialnia (z części dziennej)
D([4300,10000],[4300,10800],flip=True)     # łazienka en suite
D([4300,13000],[4300,13800],flip=True)     # garderoba / pralnia (z sypialni)
R([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,5340],[4940,5340],[4940,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9240],[XW,9240]],'część dzienna – loft')
R([[5060,5460],[XE,5460],[XE,6840],[5060,6840]],'WC gościnne')
R([[XW,9360],[4240,9360],[4240,YN],[XW,YN]],'sypialnia z garderobą otwartą'); R([[4360,9360],[XE,9360],[XE,12340],[4360,12340]],'łazienka')
R([[4360,12460],[XE,12460],[XE,YN],[4360,YN]],'garderoba + pralnia')
N([3000,8000],'brak korytarzy: 49 m² dziennej + apartament 21 m² z łazienką 7 m² i garderobą 7 m²')
F('fridge',3640,8640,4240,9240); F('counter',3040,8640,3640,9240,'blat'); F('hob',2440,8640,3040,9240); F('counter',1840,8640,2440,9240,'blat'); F('sink',1240,8640,1840,9240); F('counter',740,8640,1240,9240,'blat')
F('box',1500,6600,3300,7500,'wyspa 180×90'); F('chair',1700,6100,2150,6550); F('chair',2300,6100,2750,6550)
F('table',1200,4300,3200,5200,'stół 200×90'); F('chair',1450,3800,1900,4250); F('chair',2100,3800,2550,4250); F('chair',2700,3800,3150,4250); F('chair',1450,5250,1900,5700); F('chair',2100,5250,2550,5700); F('chair',2700,5250,3150,5700)
F('tv',6420,1300,6820,2900,'RTV'); F('sofa',4100,1100,5000,3300,'sofa 220'); F('coffee',5200,1700,5800,2700,'ława'); F('armchair',4200,3600,5000,4400); F('pax150s',5060,7700,5410,9200,'PAX 150×35')
F('wc',6400,5520,6800,6170); F('basin',5120,6400,5520,6800)
F('bed',1400,13120,3000,15120); F('night',950,14720,1350,15120); F('night',3050,14720,3450,15120); F('wardrobe',740,9400,2740,10000,'szafa 200'); F('desk',3640,10400,4240,11600,'biurko'); F('chair',3150,10780,3600,11230)
F('bath',4420,11540,6120,12290); F('shower',5880,9620,6780,10520); F('wc',6380,10620,6780,11270); F('basin',4420,9400,4920,9800); F('basin',5000,9400,5500,9800)
F('washer',6220,12520,6820,13120); F('washer',6220,13180,6820,13780,'suszarka'); F('wardrobe',4700,14540,6700,15120,'PAX 200×58'); F('shoe',5500,12520,5900,14400,'regał')

# ---------- P11: dwie sypialnie z własnymi łazienkami, hol-jadalnia z oknem, salon na północy ----------
v='P11'; W,D,R,F,N=mk(v)
W([XW,3400],[XE,3400]); W([3900,3400],[3900,6900]); W([5600,3400],[5600,6900]); W([3900,5000],[5600,5000]); W([XW,6900],[XE,6900])
W([4600,9560],[5880,9560]); W([4600,9560],[4600,11000]); W([4600,11000],[XE,11000])
D([5700,3400],[6600,3400],flip=True)       # sypialnia A
D([4500,3400],[5300,3400],flip=True)       # łazienka A (en suite, drzwi do sypialni)
D([2950,6900],[3850,6900],flip=True)       # sypialnia B
D([3900,5200],[3900,6000])                 # łazienka B (en suite, do sypialni)
D([5700,6900],[6700,6900],open_=True)      # hol → korytarz
D([4700,9560],[5500,9560])                 # WC gościnne (z holu)
R(south_face_poly(3340),'sypialnia A'); R([[3960,3460],[5540,3460],[5540,4940],[3960,4940]],'łazienka A')
R([[XW,3460],[3840,3460],[3840,6840],[XW,6840]],'sypialnia B'); R([[3960,5060],[5540,5060],[5540,6840],[3960,6840]],'łazienka B')
R([[5660,3460],[XE,3460],[XE,6840],[5660,6840]],'korytarz'); R([[XW,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9500],[4660,9500],[4660,9300],[XW,9300]],'hol z jadalnią')
R([[4660,9620],[XE,9620],[XE,10940],[4660,10940]],'WC gościnne'); R([[XW,9300],[4540,9300],[4540,11060],[XE,11060],[XE,YN],[XW,YN]],'salon z aneksem')
N([2000,8800],'układ „hotelowy”: każda sypialnia z własną łazienką; jadalnia w holu pod oknem')
F('bed',740,1500,2740,3100,'łóżko 160×200'); F('night',2800,2700,3200,3100); F('pax150',2900,2760,4400,3340,'PAX 150×58'); F('desk',4400,950,5600,1550,'biurko'); F('chair',4775,1600,5225,2050)
F('shower',4620,3460,5520,4360); F('wc',3980,3500,4380,4150); F('basin',3980,4500,4480,4900)
bed_west_safe(F,3900,3400,6900)
F('shower',3980,5940,4880,6840); F('wc',5100,5100,5500,5750); F('basin',4000,5100,4500,5500)
F('table',1500,7700,2900,8500,'stół 140×80'); F('chair',1750,7200,2200,7650); F('chair',2200,7200,2650,7650); F('chair',1750,8550,2200,9000); F('chair',2200,8550,2650,9000); F('pax150s',3900,6960,5400,7310,'PAX 150×35')
F('wc',6400,9700,6800,10350); F('basin',4760,10500,5160,10900)
F('fridge',3640,14580,4240,15180); F('counter',3040,14580,3640,15180,'blat'); F('hob',2440,14580,3040,15180); F('counter',1840,14580,2440,15180,'blat'); F('sink',1240,14580,1840,15180); F('counter',740,14580,1240,15180,'blat')
F('tv',4800,11060,6400,11460,'RTV'); F('sofa',4400,13200,6600,14100,'sofa 220'); F('coffee',5000,12300,6000,12900,'ława'); F('armchair',740,12000,1540,12800); F('box',1800,11800,2800,13000,'stolik / fotel')

# ---------- P12: łazienka na ścianie zachodniej między oknami, hol-jadalnia z oknem, salon 30 m² na płn. ----------
v='P12'; W,D,R,F,N=mk(v)
W([XW,3400],[XE,3400]); W([3900,3400],[3900,6900]); W([5600,3400],[5600,6900]); W([3900,5000],[5600,5000]); W([XW,6900],[XE,6900])
W([XW,8300],[3900,8300]); W([2700,8300],[2700,10300]); W([3900,8300],[3900,10300]); W([XW,10300],[XE,10300])
D([5700,3400],[6600,3400],flip=True)       # sypialnia 1
D([2950,6900],[3850,6900],flip=True)       # sypialnia 2
D([5600,3600],[5600,4400],flip=True)       # WC (na zewnątrz)
D([5600,5600],[5600,6400],flip=True)       # schowek
D([5700,6900],[6700,6900],open_=True)      # hol → korytarz płd.
D([1000,8300],[1900,8300],flip=True)       # łazienka (otwierane do holu)
D([2900,8300],[3700,8300])                 # pralnia (do środka)
D([4000,10300],[5600,10300],open_=True)    # hol → salon (otwór 1,6 m)
R(south_face_poly(3340),'sypialnia 1'); R([[XW,3460],[3840,3460],[3840,6840],[XW,6840]],'sypialnia 2')
R([[3960,3460],[5540,3460],[5540,4940],[3960,4940]],'WC'); R([[3960,5060],[5540,5060],[5540,6840],[3960,6840]],'schowek'); R([[5660,3460],[XE,3460],[XE,6840],[5660,6840]],'korytarz')
R([[XW,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9560],[XE,9560],[XE,10240],[3960,10240],[3960,8240],[XW,8240]],'hol z jadalnią')
R([[XW,8360],[2640,8360],[2640,10240],[XW,10240]],'łazienka'); R([[2760,8360],[3840,8360],[3840,10240],[2760,10240]],'pralnia')
R([[XW,10360],[XE,10360],[XE,YN],[XW,YN]],'salon z aneksem')
N([1500,9300],'łazienka w ślepym polu między oknami (y 8,3–10,3) – zwalnia ścianę wschodnią')
bed_south_full(F); bed_west_safe(F,3900,3400,6900)
F('wc',5100,3500,5500,4150); F('basin',4000,4450,4500,4850); F('shoe',3980,5100,4580,6800,'regał')
F('table',3300,7000,4700,7800,'stół 140×80'); F('chair',2850,7175,3250,7625); F('chair',4750,7175,5150,7625); F('chair',3550,7830,3950,8230); F('chair',4050,7830,4450,8230); F('shoe',6220,8700,6820,9080,'szafka'); F('shoe',740,6960,2340,7360,'komoda')
F('shower',740,9340,1640,10240); F('wc',2240,8500,2640,9150); F('basin',1800,9800,2300,10200)
F('washer',2800,9640,3400,10240,'pralka+suszarka (kolumna)'); F('shoe',3440,9200,3840,10200,'regał')
F('fridge',6220,12800,6820,13400); F('counter',6220,12200,6820,12800,'blat'); F('sink',6220,11600,6820,12200); F('counter',6220,11000,6820,11600,'blat'); F('hob',6220,10400,6820,11000)
F('counter',4400,14580,6220,15180,'blat')
F('table',3800,12600,5200,13400,'stół 140×80'); F('chair',4050,12100,4500,12550); F('chair',4500,12100,4950,12550); F('chair',4050,13450,4500,13900); F('chair',4500,13450,4950,13900)
F('sofa',740,10400,2940,11300,'sofa 220'); F('tv',1200,14780,2800,15180,'RTV'); F('coffee',1300,11600,2300,12200,'ława'); F('armchair',3200,11000,4000,11800)

# ---------- P13: pracownia / biuro na 2 okna przy wejściu + mieszkanie 2-pokojowe ----------
v='P13'; W,D,R,F,N=mk(v)
W([3900,6900],[3900,12400]); W([XW,6900],[XE,6900]); W([5000,5400],[5000,6900]); W([5000,5400],[XE,5400])
W([5600,9560],[5600,12400]); W([5600,9560],[5880,9560]); W([XW,12400],[XE,12400])
D([3900,7300],[3900,8200])                 # pracownia (z holu)
D([4000,6900],[5000,6900],open_=True)      # hol → salon (otwór 1,0 m)
D([5300,6900],[6100,6900])                 # WC (z holu)
D([5600,10200],[5600,11000])               # łazienka
D([4400,12400],[5300,12400])               # sypialnia
R([[XW,6960],[3840,6960],[3840,12340],[XW,12340]],'pracownia / biuro (2 okna)')
R([[3960,6960],[XE,6960],[XE,9080],[5880,9080],[5880,9560],[5540,9560],[5540,12340],[3960,12340]],'hol + korytarz')
R([[5660,9620],[XE,9620],[XE,12340],[5660,12340]],'łazienka'); R([[XW,12460],[XE,12460],[XE,YN],[XW,YN]],'sypialnia')
R([[5060,5460],[XE,5460],[XE,6840],[5060,6840]],'WC + pralnia')
R([[XW,ys(XW)],[2475,732],[2480,760],[5100,880],[XE,ys(XE)],[XE,5340],[4940,5340],[4940,6840],[XW,6840]],'salon z aneksem')
N([2200,9300],'praca z domu: klienci wchodzą z holu wprost do pracowni, nie przechodząc przez mieszkanie; WC przy holu')
F('desk',1500,9800,3100,10600,'biurko 160×80'); F('chair',2075,10650,2525,11100); F('chair',1700,9250,2150,9700); F('chair',2450,9250,2900,9700)
F('shoe',3240,7000,3840,9000,'regał'); F('desk',740,7400,1340,8600,'biurko 2'); F('chair',1400,7775,1850,8225); F('sofa',1500,11440,3500,12340,'kanapa 200')
F('pax150s',4020,7000,4370,8500,'PAX 150×35'); F('pax275',4020,9450,4600,12200,'PAX 275×58')
bath_east(F); bed_north_full(F)
F('wc',6400,5520,6800,6170); F('basin',5120,6400,5520,6800); F('washer',5120,5500,5720,6100)
F('fridge',3640,6240,4240,6840); F('counter',3040,6240,3640,6840,'blat'); F('hob',2440,6240,3040,6840); F('counter',1840,6240,2440,6840,'blat'); F('sink',1240,6240,1840,6840); F('counter',740,6240,1240,6840,'blat')
F('tv',6420,1300,6820,2900,'RTV'); F('sofa',4100,1100,5000,3300,'sofa 220'); F('coffee',5200,1700,5800,2700,'ława')
F('table',1500,3600,2900,4400,'stół 140×80'); F('chair',1750,3100,2200,3550); F('chair',2200,3100,2650,3550); F('chair',1750,4450,2200,4900); F('chair',2200,4450,2650,4900)



# --- drzwi wewnętrzne w mieszkaniach: światło 80 cm (poza drzwiami wejściowymi do lokali) ---
ENTRANCE_DOORS=[[[5700,6840],[6600,6840]],[[5600,7300],[5600,8200]],[[5700,5700],[6600,5700]],[[5600,8000],[5600,8900]]]
def norm_doors(items):
    n=0
    for it in items:
        if it['type']!='door' or it.get('open'): continue
        a,b=it['pts']
        if [a,b] in ENTRANCE_DOORS or [b,a] in ENTRANCE_DOORS: continue
        L=((b[0]-a[0])**2+(b[1]-a[1])**2)**0.5
        if abs(L-800)>1 and L<=1200:
            d=((b[0]-a[0])/L,(b[1]-a[1])/L); it['pts']=[a,[round(a[0]+d[0]*800),round(a[1]+d[1]*800)]]; n+=1
    return n
norm_doors(items)
# --- lico ściany wschodniej sali 108: 6800 (płd., y<9080) / 6780 (płn., y>9560) – meble nie mogą go przekraczać
for it in items:
    if it['type']=='furn':
        (x0,y0),(x1,y1)=it['pts']
        if x1>6770 and x0>4000:
            lim = 6770 if min(y0,y1)>=9560 else 6790
            if x1>lim: it['pts']=[[x0-(x1-lim),y0],[lim,y1]]
# --- normalizacja szaf do modułów PAX (50/75/100 cm): szerokości 150/175/200/250/275/300, głębokość 58 (lub 35) ---
PAX_W=[1500,1750,2000,2500,2750,3000]
for it in items:
    if it['type']=='furn' and (it.get('kind')=='wardrobe' or str(it.get('kind','')).startswith('pax')):
        (x0,y0),(x1,y1)=it['pts']; w=abs(x1-x0); h=abs(y1-y0)
        long_,short_=(w,h) if w>=h else (h,w)
        depth = 350 if short_<=400 else 580
        width = min(PAX_W, key=lambda p: abs(p-long_))
        if width>long_+1: width=max([p for p in PAX_W if p<=long_+1] or [1500])
        if w>=h:  # poziomo: zachowaj krawędź przy ścianie (ta bliżej granicy) -> zachowaj y0 jeśli y0<y1 środek? zostaw y0 jako stronę ściany gdy h==600 zmiana na 580 od strony frontu
            cx=(x0+x1)/2; nx0=round(cx-width/2); nx1=nx0+width
            if y0<y1: ny0,ny1=(y0,y0+depth)
            it['pts']=[[nx0,ny0],[nx1,ny1]]
        else:
            cy=(y0+y1)/2; ny0=round(cy-width/2); ny1=ny0+width
            it['pts']=[[x0,ny0],[x0+depth,ny1]]
        it['kind']='pax150s' if depth==350 and width==1500 else ('pax200s' if depth==350 else {1500:'pax150',1750:'pax175',2000:'wardrobe',2500:'pax250',2750:'pax275',3000:'pax300'}[width])
        it['label']='PAX %d×%d'%(width//10, depth//10)

def polyarea(p):
    a=0
    for i in range(len(p)):
        j=(i+1)%len(p); a+=p[i][0]*p[j][1]-p[j][0]*p[i][1]
    return abs(a)/2e6
for it in items:
    if it['type']=='room': print(it['v'], it['unit'], it['label'], round(polyarea(it['pts']),2))
json.dump({'items':items,'updatedAt':'2026-10-23T22:00:00+02:00','floor':'pietro1'}, open('seed_pietro1.json','w'), ensure_ascii=False)
tot={}
for it in items:
    if it['type']=='room': tot[(it['v'],it['unit'])]=tot.get((it['v'],it['unit']),0)+polyarea(it['pts'])
print({k:round(v,1) for k,v in tot.items()})
