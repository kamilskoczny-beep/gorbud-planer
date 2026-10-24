import json, sys
src=sys.argv[1]; out=sys.argv[2]
d=json.load(open(src)); data=d.get('data',d); items=data['items']
def match(i,t,v,pts): return i['type']==t and i.get('v')==v and i['pts']==pts
n=0
for i in items:
    if match(i,'wall','P9',[[5880,9080],[5240,9080]]): i['pts']=[[5880,9140],[5180,9140]]; n+=1
    elif match(i,'wall','P9',[[5240,9080],[5240,8420]]): i['pts']=[[5180,9140],[5180,8420]]; n+=1
    elif i['type']=='furn' and i.get('v')=='P9' and i.get('kind')=='pax150' and i['pts']==[[5300,8500],[6800,9080]]: i['pts']=[[5240,8500],[6740,9080]]; n+=1
    elif i['type']=='furn' and i.get('v')=='P10' and i.get('kind')=='shower' and i['pts']==[[5920,9400],[6820,10300]]: i['pts']=[[5880,9620],[6780,10520]]; n+=1
    elif i['type']=='furn' and i.get('v')=='P10' and i.get('kind')=='wc' and i['pts']==[[6400,10500],[6800,11150]]: i['pts']=[[6380,10620],[6780,11270]]; n+=1
    elif i['type']=='furn' and i.get('v')=='P12' and i.get('kind')=='chair' and i['pts'] in ([[3550,7850],[3950,8250]],[[4050,7850],[4450,8250]]): i['pts']=[[i['pts'][0][0],7830],[i['pts'][1][0],8230]]; n+=1
    elif i['type']=='furn' and i.get('v')=='P9' and i['pts']==[[2400,6440],[2800,6840]]: i['pts']=[[2400,6350],[2800,6750]]; n+=1
m=0
for i in items:
    if i['type']=='furn':
        (x0,y0),(x1,y1)=i['pts']
        if x1>6770 and x0>4000:
            lim = 6770 if min(y0,y1)>=9560 else 6790
            if x1>lim: i['pts']=[[x0-(x1-lim),y0],[lim,y1]]; m+=1

# drzwi wewnętrzne w mieszkaniach: światło 80 cm (poza drzwiami wejściowymi do lokali) ---
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
nd=norm_doors(items)
print('targeted',n,'clamped',m,'doors80',nd,'items',len(items))
json.dump({'items':items,'updatedAt':'2026-10-24T13:00:00+02:00','floor':'pietro1'},open(out,'w'),ensure_ascii=False)
