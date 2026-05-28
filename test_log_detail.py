import requests, re, json

s = requests.Session()
r = s.get('http://localhost:1086/auth/login')
m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
xsrf = m.group(1) if m else ''
r = s.post('http://localhost:1086/auth/login', data={'username':'admin','password':'admin888','_xsrf':xsrf})

r = s.get('http://localhost:1086/api/crawl_log/1')
print('Log detail:', r.status_code)
try:
    d = json.loads(r.text)
    if d.get('code') == 0 and d.get('data'):
        log = d['data']
        print('ID:', log.get('id'))
        print('Task:', log.get('task_name'))
        print('Status:', log.get('status'))
        print('URL:', log.get('url'))
        print('Start:', log.get('start_time'))
        print('End:', log.get('end_time'))
        summary = log.get('result_summary', '')
        print('Summary length:', len(summary))
        print('Summary (first 200):', summary[:200])
        raw = log.get('raw_content', '')
        print('Raw content length:', len(raw) if raw else 0)
    else:
        print('Error:', d.get('msg'))
except Exception as e:
    print('Parse error:', e)
    print(r.text[:500])
