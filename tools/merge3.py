import json,sys
base,mine,theirs,out=sys.argv[1:5]
B={i['id']:i for i in json.load(open(base))['items']}; M=json.load(open(mine))['items']; T={i['id']:i for i in json.load(open(theirs))['items']}
res=[]; seen=set(); nT=0
for i in M:
    k=i['id']; seen.add(k)
    if k in B:
        if k not in T: nT+=1; continue            # użytkownik usunął
        if T[k]!=B[k]: res.append(T[k]); nT+=1; continue  # użytkownik zmienił – jego wersja
    res.append(i)
for k,v in T.items():
    if k not in B and k not in seen: res.append(v); nT+=1   # nowe u użytkownika
json.dump({'items':res},open(out,'w'),ensure_ascii=False); print(out,'zmian użytkownika scalonych',nT)
