import requests, re, json

s = requests.Session()
r = s.get('http://localhost:1086/auth/login')
m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
xsrf = m.group(1) if m else ''
r = s.post('http://localhost:1086/auth/login', data={'username':'admin','password':'admin888','_xsrf':xsrf})
print('Login:', r.status_code)

xsrf2 = s.cookies.get('_xsrf', '')
r = s.post('http://localhost:1086/api/crawl_task', data={'action':'run_now','id':'1','_xsrf':xsrf2})
print('Run now:', r.status_code)
try:
    d = json.loads(r.text)
    print('Code:', d.get('code'))
    print('Msg:', d.get('msg',''))
    if d.get('data'):
        print('Summary:', str(d['data'].get('summary',''))[:300])
except Exception as e:
    print('Parse error:', e)
    print(r.text[:500])

r = s.get('http://localhost:1086/api/crawl_log')
print('\nCrawl logs:', r.status_code)
try:
    d = json.loads(r.text)
    print('Count:', d.get('count', 0))
    if d.get('data'):
        for log in d['data'][:3]:
            print(f"  Log #{log['id']}: status={log['status']}, summary={str(log.get('result_summary',''))[:100]}")
except:
    print(r.text[:300])
