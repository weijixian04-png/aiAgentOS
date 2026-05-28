import requests
import re

s = requests.Session()
r = s.get('http://localhost:1086/auth/login')
m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
xsrf = m.group(1) if m else ''
r = s.post('http://localhost:1086/auth/login', data={'username':'admin','password':'admin888','_xsrf':xsrf})
print('Login:', r.status_code)

r = s.get('http://localhost:1086/api/crawl_task')
print('crawl_task API:', r.status_code, r.text[:500])

r = s.get('http://localhost:1086/api/crawl_log')
print('crawl_log API:', r.status_code, r.text[:300])

r = s.get('http://localhost:1086/admin/crawl')
print('crawl page:', r.status_code)

r = s.get('http://localhost:1086/admin/crawl/logs')
print('crawl logs page:', r.status_code)
