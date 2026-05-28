import requests, re, json

s = requests.Session()
r = s.get('http://localhost:1086/auth/login')
m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
xsrf = m.group(1) if m else ''
r = s.post('http://localhost:1086/auth/login', data={'username':'admin','password':'admin888','_xsrf':xsrf})
print('=== Login:', r.status_code, '===')

xsrf2 = s.cookies.get('_xsrf', '')

print('\n--- Test 1: Add Task ---')
r = s.post('http://localhost:1086/api/crawl_task', data={
    'action': 'add',
    'task_name': 'Test Task',
    'url': 'https://www.example.com',
    'cron_expr': '0 */3 * * *',
    'extract_rule': 'title',
    'status': '1',
    '_xsrf': xsrf2
})
d = json.loads(r.text)
print('Add:', d.get('code'), d.get('msg'))

r = s.get('http://localhost:1086/api/crawl_task')
d = json.loads(r.text)
print('Task count:', d.get('count'))
new_task = None
for t in d.get('data', []):
    if t['task_name'] == 'Test Task':
        new_task = t
        print('New task ID:', t['id'], 'Name:', t['task_name'])
        break

if new_task:
    print('\n--- Test 2: Edit Task ---')
    r = s.post('http://localhost:1086/api/crawl_task', data={
        'action': 'edit',
        'id': str(new_task['id']),
        'task_name': 'Test Task Edited',
        'url': 'https://www.example.org',
        'cron_expr': '0 */4 * * *',
        'extract_rule': 'text',
        'status': '1',
        '_xsrf': xsrf2
    })
    d = json.loads(r.text)
    print('Edit:', d.get('code'), d.get('msg'))

    print('\n--- Test 3: Toggle Status ---')
    r = s.post('http://localhost:1086/api/crawl_task', data={
        'action': 'toggle',
        'id': str(new_task['id']),
        '_xsrf': xsrf2
    })
    d = json.loads(r.text)
    print('Toggle:', d.get('code'), d.get('msg'))

    r = s.get('http://localhost:1086/api/crawl_task')
    d = json.loads(r.text)
    for t in d.get('data', []):
        if t['id'] == new_task['id']:
            print('Status after toggle:', t['status'])
            break

    print('\n--- Test 4: Toggle Back ---')
    r = s.post('http://localhost:1086/api/crawl_task', data={
        'action': 'toggle',
        'id': str(new_task['id']),
        '_xsrf': xsrf2
    })
    d = json.loads(r.text)
    print('Toggle back:', d.get('code'), d.get('msg'))

    print('\n--- Test 5: Delete Task ---')
    r = s.post('http://localhost:1086/api/crawl_task', data={
        'action': 'delete',
        'id': str(new_task['id']),
        '_xsrf': xsrf2
    })
    d = json.loads(r.text)
    print('Delete:', d.get('code'), d.get('msg'))

    r = s.get('http://localhost:1086/api/crawl_task')
    d = json.loads(r.text)
    print('Task count after delete:', d.get('count'))

print('\n--- Test 6: Invalid Cron ---')
r = s.post('http://localhost:1086/api/crawl_task', data={
    'action': 'add',
    'task_name': 'Bad Cron',
    'url': 'https://example.com',
    'cron_expr': 'invalid',
    'extract_rule': 'title',
    'status': '1',
    '_xsrf': xsrf2
})
d = json.loads(r.text)
print('Invalid cron:', d.get('code'), d.get('msg'))

print('\n=== ALL CRUD TESTS DONE ===')
