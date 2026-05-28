import requests, re

s = requests.Session()
r = s.get('http://localhost:1086/auth/login')
m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
xsrf = m.group(1) if m else ''
r = s.post('http://localhost:1086/auth/login', data={'username':'admin','password':'admin888','_xsrf':xsrf})

print('=== Original System Health Check ===')

pages = [
    ('Admin Home', '/admin'),
    ('Login Page', '/auth/login'),
    ('Crawl Task Page', '/admin/crawl'),
    ('Crawl Log Page', '/admin/crawl/logs'),
]

apis = [
    ('Crawl Task API', '/api/crawl_task'),
    ('Crawl Log API', '/api/crawl_log'),
]

print('\n--- Page Access ---')
for name, path in pages:
    r = s.get(f'http://localhost:1086{path}', allow_redirects=False)
    status = r.status_code
    ok = 'OK' if status == 200 else 'FAIL'
    print(f'  {name}: {status} [{ok}]')

print('\n--- API Access ---')
for name, path in apis:
    r = s.get(f'http://localhost:1086{path}')
    status = r.status_code
    ok = 'OK' if status == 200 else 'FAIL'
    print(f'  {name}: {status} [{ok}]')

print('\n=== Health Check Complete ===')
