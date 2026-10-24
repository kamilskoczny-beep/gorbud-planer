import json, os
m=json.load(open('model_final.json'))
units={
 'W':{'name':'Część wspólna','color':'#b7bec7'},
 'O':{'name':'Orange 109–111 (bez zmian)','color':'#f0c36a'},
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
}
p1={'101':'W','102':'W','102a':'W','109':'O','110':'O','111':'O','106':'M2','107':'M2','103':'M3','104':'M3','105':'M3'}
pod_common={'201':'W','202':'W','203':'W'}
pod_M4={'204':'M4','205':'M4','206':'M4','207':'M4','208':'M4'}
A={**pod_M4, **{n:'M5' for n in ['209','210','211','212','213','214','215','216','217','218','219']}}
B={**pod_M4, '209':'M5','210':'M5','214':'M5','211':'W', **{n:'M6' for n in ['212','213','215','216','217','218','219']}}
variants={'units':units,'floors':{
 'pietro1':[
  {'id':'P9','name':'Mieszkanie 108 — wariant roboczy (dawny R3-1)','desc':'Wejście wprost do salonu w środkowym paśmie (2 okna), szafa wnękowa PAX 150 przy wejściu. Na północy sypialnia 1 i łazienka z pralką dostępna z salonu. Na południu sypialnie 2 i 3, garderoba PAX, pomieszczenie gospodarcze i przejście. Układ rozwijany na bieżąco – rysuj uwagi, Claude nanosi.','assign':p1,'hide':['108']}
 ],
 'poddasze':[
  {'id':'W4','name':'Poddasze — wariant roboczy M6 (dawny W4 loft)','desc':'Mieszkanie M6 = skrzydło 212–219 z korytarzem. Ścianka 215|korytarz usunięta – kuchnia z jadalnią przy wejściu otwarta na hol (zweryfikować konstrukcję więźby). Salon 219 (okno szczytowe), sypialnie 213 i 216 pod skosem zach., łazienka z pralnią w 217 przy kominie, gabinet/pokój gościnny w 218. Układ rozwijany na bieżąco – rysuj uwagi, Claude nanosi.','assign':{**pod_common,**pod_M4,'209':'M5','210':'M5','211':'M5','214':'M5',**{n:'M6' for n in ['212','213','215','216','217','218','219']}},'hide':['212','213','215','216','217','218','219']},
 ],
 'parter':[], 'piwnica':[]}}
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
