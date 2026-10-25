import json, os
m=json.load(open('model_final.json'))
# uzupełnienia inwentaryzacji z ekspertyzy (COM.xlsx – zestawienie pomieszczeń PPSA): brakujące nazwy/powierzchnie w piwnicy
_fix={'004':('schron nieużytkowany',14.72),'005':('schron nieużytkowany',9.20),'009':('komunikacja',14.55),'013':('przepompownia',6.49)}
for r in m['floors']['piwnica']['rooms']:
    if r['nr'] in _fix:
        if not r.get('name') or r['name'].isdigit(): r['name']=_fix[r['nr']][0]
        if not r.get('area'): r['area']=_fix[r['nr']][1]
units={
 'W':{'name':'Część wspólna','color':'#b7bec7'},
 'O':{'name':'Orange — 109–111, piwnica 007/008 (najem, bez zmian)','color':'#f0c36a'},
 'P':{'name':'Poczta Polska — usługi (najem, bez zmian)','color':'#f2d16b'},
 'T':{'name':'Pomieszczenia techniczne budynku','color':'#cfcfcf'},
 'M1':{'name':'M1 — 108 jako 1 mieszkanie','color':'#e0a04a'},
 'M1a':{'name':'M1a — 108 część płd.','color':'#e07b3a'},
 'M1b':{'name':'M1b — 108 część płn.','color':'#d9b23a'},
 'M3a':{'name':'M3a — 108 kawalerka (płd.)','color':'#e8a6c0'},
 'M3b':{'name':'M3b — 108 trzypokojowe (płn.)','color':'#b58fd6'},
 'M2':{'name':'M2 — 106 + 107','color':'#6aa0d8'},
 'M3':{'name':'M3 — 105 + 103/104','color':'#5bbfae'},
 'M4':{'name':'M4 — poddasze, skrzydło płd.','color':'#79b76a'},
 'M5':{'name':'M5 — poddasze, pokoje 209–211 i 214','color':'#c97bb0'},
 'M6':{'name':'M6 — poddasze, skrzydło zach. 212–219','color':'#8f8fd6'},
 'M7':{'name':'M7 — poddasze, 209 + 210 + 205','color':'#e0a04a'},
 'M8':{'name':'M8 — poddasze, 206 + 207 + 208','color':'#5bbfae'},
}
p1={'101':'W','102':'W','102a':'W','109':'O','110':'O','111':'O','106':'M2','107':'M2','103':'M3','104':'M3','105':'M3'}
pod_common={'201':'W','202':'W','203':'W'}
pod_M4={'204':'M4','205':'M4','206':'M4','207':'M4','208':'M4'}
A={**pod_M4, **{n:'M5' for n in ['209','210','211','212','213','214','215','216','217','218','219']}}
B={**pod_M4, '209':'M5','210':'M5','214':'M5','211':'W', **{n:'M6' for n in ['212','213','215','216','217','218','219']}}
variants={'units':units,'floors':{
 'pietro1':[
  {'id':'P9','name':'Mieszkanie 108 — wariant roboczy (dawny R3-1)','desc':'Wejście wprost do salonu w środkowym paśmie (2 okna), szafa wnękowa PAX 150 przy wejściu. Na północy sypialnia 1 i łazienka z pralką dostępna z salonu. Na południu sypialnie 2 i 3, garderoba PAX, pomieszczenie gospodarcze i przejście. Układ rozwijany na bieżąco – rysuj uwagi, Claude nanosi.','assign':p1,'hide':['108','103','104','105','106','107']}
 ],
 'poddasze':[
  {'id':'W4','name':'Poddasze — wariant roboczy M6 (dawny W4 loft)','desc':'M6 = skrzydło 212–219 z korytarzem; M7 = 209+210+205 z holem w przedsionku; M8 = 206+207+208; hol 211 wspólny, 214 należy do M6; 201 = klatka schodowa (wydzielona ppoż.), 203 = pom. sprzątaczki do obsługi budynku, 204 zostaje jako WC wspólne. Ścianka 215|korytarz usunięta – kuchnia z jadalnią przy wejściu otwarta na hol (zweryfikować konstrukcję więźby). Salon 219 (okno szczytowe), sypialnie 213 i 216 pod skosem zach., łazienka z pralnią w 217 przy kominie, gabinet/pokój gościnny w 218. Układ rozwijany na bieżąco – rysuj uwagi, Claude nanosi.','assign':{**pod_common,'204':'W','211':'W','214':'M6','205':'M7','209':'M7','210':'M7','206':'M8','207':'M8','208':'M8',**{n:'M6' for n in ['212','213','215','216','217','218','219']}},'hide':['212','213','215','216','217','218','219','205','206','207','208','209','210'],'rename':{'201':'kl. schodowa (wydzielona ppoż.)','203':'pom. sprzątaczki (obsługa budynku)','204':'WC wspólne (zostaje)','202':'korytarz (droga ewakuacyjna)','214':'pom. gospodarcze (214)','211':'hol (komunikacja)'}},
 ],
 'parter':[ {'id':'S','name':'Parter — stan istniejący (Poczta Polska, najem)','desc':'Bez zmian funkcjonalnych: placówka Poczty Polskiej (najem) – powierzchnia niemieszkalna; 1 i 2 wózkarnie (pomieszczenia ogólnego użytku części mieszkalnej), 3 klatka schodowa, 4/12/17 komunikacja (wg ekspertyzy PPSA).','assign':{**{str(n):'P' for n in [5,6,7,8,9,10,11,13,14,15,16,18,19,20,21,22,23,24,25]},'4':'P','12':'P','17':'P','1':'W','2':'W','3':'W'},'rename':{'3':'kl. schodowa (wydzielona ppoż.)','4':'korytarz Poczty','5':'łazienka PP','12':'przedsionek ze schodami','17':'przedsionek ze schodami'}} ],
 'piwnica':[ {'id':'S','name':'Piwnica — stan istniejący','desc':'Kotłownia gazowa zostaje (techniczne). 007 kablownia i 008 akumulatornia – Orange; 010 kwasownia – Poczta. Schron 004/004A/005/006 nieużytkowany (techniczne). Spiżarnie i wózkarnie = pomieszczenia pomocnicze części mieszkalnej (wg ekspertyzy PPSA).','assign':{'007':'O','008':'O','010':'P','004':'T','004A':'T','005':'T','006':'T','011':'T','001':'W','002':'W','009':'W','003':'W','010A':'W','012':'W','013':'W','016':'W','014':'W','015':'W'},'rename':{'013':'spiżarnia (d. przepompownia)','016':'spiżarnia','001':'kl. schodowa (wydzielona ppoż.)'},'cls':{'007':'T','008':'T','010':'T','004A':'T'}} ]}}  # kablownia/akumulatornia/kwasownia = pomieszczenia techniczne instalacji (jak w ekspertyzie), nie usługi
# ---- dojścia ewakuacyjne (§ 256 WT: ZL IV, jedno dojście ≤ 60 m, w tym ≤ 20 m po poziomej drodze; punkty: strona korytarza przy drzwiach mieszkania → przed drzwiami EI 30 klatki)
# przesunięcie układu lokalnego każdej kondygnacji do wspólnego układu (I piętro = 0,0); wyliczone korelacją rastrów ścian (20 mm), do podrysu i pionów
# metryka rysunków PAB (tabelka rysunkowa) + stan istniejący wg ekspertyzy PPSA (COM.xlsx) do porównania bilansu
variants['meta']={'investor':'SANDER Sp. z o.o.','object':'Budynek dawnej poczty – ul. Pocztowa 11, 78-500 Drawsko Pomorskie','stage':'PAB – projekt architektoniczno-budowlany: zmiana sposobu użytkowania części usługowej na mieszkalną (cały budynek mieszkalny wielorodzinny z usługami)','drawings':{'piwnica':'A-01','parter':'A-02','pietro1':'A-03','poddasze':'A-04'},'existing':{'M':486.05,'N':376.25,'K':244.43,'T':140.16,'note':'stan istniejący wg ekspertyzy PPSA (COM.xlsx): pow. mieszkalna 486,05 m² (56 %), niemieszkalna 376,25 m² (44 %) z pow. użytkowej 862,30 m²'}}
variants['align']={'piwnica':[20,300],'parter':[180,220],'pietro1':[0,0],'poddasze':[-20,140]}
variants['evac']={
 'pietro1':{'exit':[22250,8150],'limit':20000,'starts':[{'u':'M1 (108)','p':[7500,8000]},{'u':'M2 (107)','p':[10120,7500],'dy':-450},{'u':'M3 (104)','p':[19910,7500],'dy':-450}]},
 'poddasze':{'exit':[21900,7850],'limit':20000,'starts':[{'u':'M6 (212)','p':[5055,8800]},{'u':'M7 (hol)','p':[5815,6450],'dy':-450},{'u':'M8 (206)','p':[14505,7200],'dy':-450}]},
}
# ---- poddasze: płaszczyzny skosów (z inwentaryzacji: linie 'sufit' = załamanie sufitu, linie h<1,90, h_min przy ścianach ~0,9 m)
# line: linia załamania (x0,y0)-(x1,y1); dir: kierunek opadania; h0: wysokość przy linii [mm]; tan: nachylenie (spadek/odległość)
variants['attic']={'floor':'poddasze','hmin':900,'planes':[
 # skrzydło zachodnie – skos od zachodu (opada w stronę -x)
 {'line':[[2328,2250],[2328,3940]],'dir':[-1,0],'h0':2350,'tan':1.04,'room':'209'},
 {'line':[[2405,4220],[2405,4990]],'dir':[-1,0],'h0':2420,'tan':1.04,'room':'210'},
 {'line':[[2405,7350],[2405,9745]],'dir':[-1,0],'h0':2600,'tan':1.04,'room':'214'},
 {'line':[[2535,9870],[2535,19360]],'dir':[-1,0],'h0':2775,'tan':1.04,'room':'213/216'},
 {'line':[[2615,19550],[2615,23300]],'dir':[-1,0],'h0':2820,'tan':1.04,'room':'219'},
 # skrzydło zachodnie – skos od wschodu (opada w stronę +x)
 {'line':[[7405,7350],[7405,9212]],'dir':[1,0],'h0':2600,'tan':1.06,'room':'211'},
 {'line':[[7225,9850],[7225,14490]],'dir':[1,0],'h0':2780,'tan':1.06,'room':'215/212'},
 {'line':[[7225,14650],[7225,15090]],'dir':[1,0],'h0':2780,'tan':1.06,'room':'212'},
 {'line':[[7225,15580],[7225,18260]],'dir':[1,0],'h0':2780,'tan':1.06,'room':'217'},
 {'line':[[7225,18360],[7225,23800]],'dir':[1,0],'h0':2820,'tan':1.06,'room':'218'},
 # skrzydło południowe – skos od północy nad korytarzem 202 (opada w stronę +y)
 {'line':[[7405,7350],[22365,7350]],'dir':[0,1],'h0':2600,'tan':1.09,'room':'202'},
 {'line':[[22515,7350],[23711,7350]],'dir':[0,1],'h0':2600,'tan':1.09,'room':'202/203'},
 # pokój 209 – skos od południa (opada w stronę -y)
 {'line':[[2328,2250],[6925,2250]],'dir':[0,-1],'h0':2350,'tan':1.05,'room':'209'},
]}
html=open('page_template.html',encoding='utf-8').read()
mj=json.dumps(m,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
vj=json.dumps(variants,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
html=html.replace('__MODEL__',mj).replace('__VARIANTS__',vj)
open('Pocztowa11_model.html','w',encoding='utf-8').write(html)
print(os.path.getsize('Pocztowa11_model.html'))
