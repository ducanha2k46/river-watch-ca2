import json, urllib.request, urllib.parse, statistics, csv
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parent
TOWNS=[('Clonmel','Tipperary','Suir',52.355,-7.703,'yes',1,4,2000,6,'Normal service'),('Fermoy','Cork','Blackwater',52.139,-8.275,'no',1,3,1500,4,'Normal service'),('Mallow','Cork','Blackwater',52.132,-8.642,'yes',1,3,1200,4,'Mallow crew van in repair: the Mallow crew can work in Mallow only tonight'),('Bandon','Cork','Bandon',51.747,-8.737,'no',0,2,1800,3,'Barrier set on loan to another council'),('Enniscorthy','Wexford','Slaney',52.502,-6.566,'no',1,2,1000,3,'Normal service'),('Ennis','Clare','Fergus',52.846,-8.982,'no',1,2,900,3,'Normal service'),('Athlone','Westmeath','Shannon',53.423,-7.941,'yes',1,5,2500,6,'Town spans Westmeath and Roscommon'),('Carrick-on-Shannon','Leitrim','Shannon',53.944,-8.095,'no',1,2,800,2,'Town spans Leitrim and Roscommon')]
def fetch(url):
    with urllib.request.urlopen(url,timeout=90) as r: return json.load(r)
def main():
    raw=ROOT/'data'; raw.mkdir(exist_ok=True)
    points=json.loads((ROOT/'river_points.json').read_text())
    summary=[]
    with (ROOT/'towns.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow('town,county,river,crew_based_here,barrier_sets,pumps,sandbags,staff_on_call,flow_override_m3s,warning_override,notes'.split(','))
        for name,county,river,lat,lon,crew,barriers,pumps,bags,staff,notes in TOWNS:
            w.writerow([name,county,river,crew,barriers,pumps,bags,staff,'','',notes])
    for name,county,river,lat,lon,*_ in TOWNS:
        lat=points[name]['model_latitude']; lon=points[name]['model_longitude']
        params=dict(latitude=lat,longitude=lon,daily='river_discharge',start_date='2016-01-01',end_date='2025-12-31')
        url='https://flood-api.open-meteo.com/v1/flood?'+urllib.parse.urlencode(params)
        path=raw/(name+'_'+str(lat)+'_'+str(lon)+'.json')
        if path.exists(): data=json.loads(path.read_text())
        else:
            data=fetch(url); path.write_text(json.dumps(data),encoding='utf-8')
        dates=data['daily']['time']; values=data['daily']['river_discharge']
        if len(values)!=3653 or any(v is None for v in values): raise ValueError(name+' incomplete history')
        ordered=sorted(values)
        def percentile(p):
            index=(len(ordered)-1)*p; lo=int(index)
            return ordered[lo]+(ordered[min(lo+1,len(ordered)-1)]-ordered[lo])*(index-lo)
        p95,p99=percentile(.95),percentile(.99)
        independent=statistics.quantiles(values,n=100,method='inclusive')[98]
        assert abs(independent-p99)<1e-8
        events={}
        for year in range(2016,2025):
            active=False; count=0
            for date,value in zip(dates,values):
                if f'{year}-10-01'<=date<=f'{year+1}-03-31':
                    high=value>=p99
                    count+=high and not active; active=high
            events[str(year)]=count
        summary.append(dict(town=name,county=county,river=river,latitude=lat,longitude=lon,grid_latitude=data['latitude'],grid_longitude=data['longitude'],river_verified=False,validation_note=points[name]['validation'],opw_station=points[name]['station'],p95=p95,p99=p99,median=statistics.median(values),days=len(values),events=events,total_events=sum(events.values()),first_four=sum(list(events.values())[:4]),last_four=sum(list(events.values())[-4:]),source=url,history_period='2016-01-01 to 2025-12-31',retrieved=datetime.now(timezone.utc).isoformat()))
        print(name,round(p95,3),round(p99,3),events,flush=True)
    (ROOT/'history_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
if __name__=='__main__': main()

