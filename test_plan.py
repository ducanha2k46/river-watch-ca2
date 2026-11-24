import csv,json
from pathlib import Path
from datetime import datetime,timezone
from flood_plan import recommend
root=Path(__file__).parent
rows=list(csv.DictReader((root/'towns.csv').open(encoding='utf-8-sig')))
h={r['town']:dict(p95=95,p99=100) for r in rows}
now=datetime(2026,11,24,12,tzinfo=timezone.utc)
def run(peaks,warnings=[]): return {r['town']:r for r in recommend(rows,h,dict.fromkeys(h,peaks),warnings,now)}
assert all(r['level']=='Normal' for r in run(94).values())
assert all(r['level']=='Standby' for r in run(95).values())
a=run(100)
assert a['Bandon']['escalate'] and a['Bandon']['crew'] is None
assert a['Mallow']['crew']=='Mallow'
assert sum(r['crew']=='Athlone' for r in a.values())==2
assert all(r['town']=='Mallow' for r in a.values() if r['crew']=='Mallow')
w=[dict(type='rain',counties=['Roscommon'],level='orange',start='2026-11-24T10:00:00+00:00',end='2026-11-25T10:00:00+00:00')]
a=run(94,w)
assert a['Athlone']['level']==a['Carrick-on-Shannon']['level']=='Standby'
rows[0]['flow_override_m3s']='150'; rows[1]['warning_override']='orange'
a=run(94)
assert a['Clonmel']['level']=='Barriers' and a['Fermoy']['level']=='Standby'
assert a['Clonmel']['rehearsal'] and a['Fermoy']['rehearsal']
print('PASS: boundaries, barrier availability, crew restrictions/capacity, cross-county rain, rehearsals. Synthetic tests only.')
