"""Read-only role workflows through nginx HTTPS; credentials/tokens stay in memory."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import requests
import urllib3
from run_regression import ACC

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
base='https://localhost'
rows=[]
for role in ('customer','staff','admin'):
    s=requests.Session(); s.verify=False
    r=s.get(base+'/dashboard/login/',timeout=20)
    token=re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"',r.text)
    if not token:
        rows.append({'role':role,'status':'INCONCLUSIVE','reason':'No CSRF login form'}); continue
    username,password=ACC[role]
    r=s.post(base+'/dashboard/login/',data={'username':username,'password':password,'csrfmiddlewaretoken':token.group(1)},headers={'Referer':base+'/dashboard/login/'},timeout=20)
    authenticated='sessionid' in s.cookies and '/login/' not in r.url
    for path in ('/dashboard/shop/','/dashboard/cart/','/dashboard/profile/','/dashboard/orders/','/dashboard/users/','/admin/users/newslettersubscriber/'):
        r=s.get(base+path,timeout=20,allow_redirects=False)
        rows.append({'role':role,'login_verified':authenticated,'path':path,'http_status':r.status_code,'redirect':r.headers.get('Location',''),'body_sha256':hashlib.sha256(r.content).hexdigest(),'title':re.sub(r'\s+',' ',(re.search(r'<title>(.*?)</title>',r.text,re.S) or ['',''])[1]).strip()})
out=Path(__file__).resolve().parents[1]/'evidence/review/session_checks.json'
out.write_text(json.dumps({'timestamp':datetime.now(timezone.utc).isoformat(),'mode':'HTTP session + CSRF login through nginx; not browser','checks':rows},indent=2))
print(json.dumps(rows,indent=2))
