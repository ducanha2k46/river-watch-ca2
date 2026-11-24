"""Flood Plan calculations. Inputs must already be validated against live sources."""
from datetime import datetime, timedelta
AREAS={'Clonmel':['Clonmel','Fermoy','Enniscorthy'],'Mallow':['Mallow','Fermoy','Bandon'],'Athlone':['Athlone','Carrick-on-Shannon','Ennis']}
LEVELS=['Normal','Standby','Barriers']
def recommend(rows, summaries, peaks, warnings, now):
    result=[]
    for row in rows:
        name=row['town']; h=summaries[name]
        override=str(row.get('flow_override_m3s','')).strip()
        peak=float(override) if override else peaks[name]
        if peak is None or peak<0: raise ValueError('Missing or invalid flow for '+name)
        counties={row['county']}
        if 'Roscommon' in row['notes']: counties.add('Roscommon')
        relevant=[w for w in warnings if w['type'].lower()=='rain' and counties.intersection(w['counties']) and datetime.fromisoformat(w['start'])<now+timedelta(hours=48) and datetime.fromisoformat(w['end'])>now]
        rehearsal=str(row.get('warning_override','')).strip().lower()
        raised=rehearsal in ('orange','red') or any(w['level'].lower() in ('orange','red') for w in relevant)
        base=2 if peak>=h['p99'] else 1 if peak>=h['p95'] else 0
        level=min(2,base+int(raised))
        result.append(dict(town=name,peak=peak,p95=h['p95'],p99=h['p99'],level=LEVELS[level],rehearsal=bool(override or rehearsal),warnings=relevant,warning_raised=raised,barriers_available=int(row['barrier_sets'])>0,exceedance_percent=(peak/h['p99']-1)*100 if h['p99']>0 else float('inf'),crew=None,notes=row['notes'],pumps=int(row['pumps']),sandbags=int(row['sandbags']),staff_on_call=int(row['staff_on_call'])))
    ranked=sorted([r for r in result if r['level']=='Barriers' and r['barriers_available']],key=lambda r:(-r['exceedance_percent'],-r['peak'],r['town']))
    crews={r['town']:r for r in rows if r['town'] in AREAS and r['crew_based_here'].lower()=='yes'}
    # Exhaustive matching preserves priority and avoids wasting Fermoy's shared coverage.
    best=None
    def assign(i,allocation,loads,bits):
        nonlocal best
        if i==len(ranked):
            candidate=(tuple(bits),dict(allocation))
            if best is None or candidate[0]>best[0]: best=candidate
            return
        town=ranked[i]['town']
        for crew,row in crews.items():
            restricted='only tonight' in row['notes'].lower() and 'mallow' in row['notes'].lower()
            if town in AREAS[crew] and loads.get(crew,0)<2 and (not restricted or town==crew):
                allocation[town]=crew; loads[crew]=loads.get(crew,0)+1
                assign(i+1,allocation,loads,bits+[1])
                loads[crew]-=1; del allocation[town]
        assign(i+1,allocation,loads,bits+[0])
    assign(0,{}, {},[])
    for r in result:
        r['crew']=best[1].get(r['town'])
        r['escalate']=r['level']=='Barriers' and not r['crew']
        r['action']='Erect barriers before 18:00' if r['crew'] else 'Confirm staff, check pumps, stage sandbags; flag Area Manager' if r['escalate'] else 'Confirm staff, check pumps, stage sandbags' if r['level']=='Standby' else 'Routine monitoring'
    return result
