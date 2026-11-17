import datetime,json,urllib.request
BASE='https://api.unidadeditorial.es/sports/v1/'
HEAD={'Origin':'https://www.marca.com','Referer':'https://www.marca.com/resultados/futbol.html','User-Agent':'Mozilla/5.0 DMF-Sports'}
LEAGUES={'laliga':'0101','segunda':'0102','premier':'0106','seriea':'0107','bundesliga':'0108','ligue1':'0109','champions':'0103','europa':'0104','conference':'01105'}
def get(url):
 req=urllib.request.Request(url,headers=HEAD)
 with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
def main():
 now=datetime.datetime.now(datetime.timezone.utc); today=now.date(); season=today.year if today.month>=7 else today.year-1
 out={'source':'MARCA / Unidad Editorial sports API','sourceUrl':'https://www.marca.com/resultados/futbol.html','fetchedAt':now.isoformat(),'rankings':{},'events':[],'errors':[]}
 for name,tournament in LEAGUES.items():
  try:
   d=get(f'{BASE}classifications/current/?site=2&type=10&tournament={tournament}&season={season}')
   root=(d.get('data') or [None])[0]
   if not root or not root.get('rank'):raise ValueError('classification empty')
   out['rankings'][name]={'matchDay':root.get('classificationHead',{}).get('matchDay'),'lastUpdate':root.get('lastUpdate'),'teams':[{'position':x.get('standing',{}).get('position'),'name':x.get('fullName') or x.get('name'),'played':x.get('standing',{}).get('played'),'won':x.get('standing',{}).get('won'),'drawn':x.get('standing',{}).get('drawn'),'lost':x.get('standing',{}).get('lost'),'goalsFor':x.get('standing',{}).get('for'),'goalsAgainst':x.get('standing',{}).get('against'),'difference':x.get('standing',{}).get('difference'),'points':x.get('standing',{}).get('points'),'logo':x.get('imageUrl')} for x in root['rank']]}
  except Exception as e:out['errors'].append('Tabla '+name+': '+str(e))
 # Pull the published Marca daily football schedule across a rolling week, so match days in any supported tournament are covered.
 seen=set()
 for offset in range(-2,9):
  date=(today+datetime.timedelta(days=offset)).isoformat()
  try:
   d=get(f'{BASE}events/preset/4_d141603f?date={date}')
   for e in d.get('data',[]):
    se=e.get('sportEvent',{}); c=se.get('competitors',{}); home=c.get('homeTeam',{}); away=c.get('awayTeam',{}); t=e.get('tournament',{}); tid=str(t.get('id',''))
    league=next((k for k,v in LEAGUES.items() if v==tid),None)
    if not league or e.get('id') in seen:continue
    seen.add(e.get('id')); score=e.get('score',{}); st=se.get('status',{}); period=score.get('period',{})
    out['events'].append({'id':e.get('id'),'league':league,'competition':t.get('name'),'date':e.get('startDate'),'home':home.get('fullName'),'away':away.get('fullName'),'homeLogo':home.get('imageUrl'),'awayLogo':away.get('imageUrl'),'homeScore':score.get('homeTeam',{}).get('totalScore'),'awayScore':score.get('awayTeam',{}).get('totalScore'),'status':period.get('alternateNames',{}).get('esES') or period.get('name') or st.get('name'),'lastUpdate':e.get('lastUpdate'),'round':se.get('matchDay')})
  except Exception as e:out['errors'].append('Partidos '+date+': '+str(e))
 out['events'].sort(key=lambda x:x.get('date') or '')
 with open('marca-data.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,separators=(',',':'))
 print('rankings',len(out['rankings']),'events',len(out['events']),'errors',out['errors'])
 if not out['rankings']:raise SystemExit('No usable MARCA classifications; refusing to publish empty data')
if __name__=='__main__':main()
