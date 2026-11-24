import json, urllib.parse, urllib.request, statistics, math
from pathlib import Path
from prepare_data import TOWNS, fetch
root=Path(__file__).parent
results=[]
for town,county,river,lat,lon,*rest in TOWNS:
    # Inspect the surrounding 0.05-degree cells, retaining their distance and flow.
    coords=[(lat+a,lon+b) for a in [-.05,0,.05] for b in [-.05,0,.05]]
    params={'latitude':','.join(str(p[0]) for p in coords),'longitude':','.join(str(p[1]) for p in coords),'daily':'river_discharge','start_date':'2020-01-01','end_date':'2020-12-31'}
    url='https://flood-api.open-meteo.com/v1/flood?'+urllib.parse.urlencode(params)
    data=fetch(url)
    cells=[]
    for p,d in zip(coords,data):
        v=d['daily']['river_discharge']
        distance=111*math.hypot(d['latitude']-lat,(d['longitude']-lon)*math.cos(math.radians(lat)))
        cells.append({'latitude':d['latitude'],'longitude':d['longitude'],'distance_km':round(distance,2),'median_2020':statistics.median(v)})
    results.append({'town':town,'river':river,'cells':cells})
    print(town,cells,flush=True)
(root/'candidate_cells.json').write_text(json.dumps(results,indent=2))
