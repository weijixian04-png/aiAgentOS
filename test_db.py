import sqlite3

conn = sqlite3.connect('database/app.db')
cur = conn.cursor()

cur.execute("PRAGMA table_info(crawl_task)")
print('crawl_task columns:')
for r in cur.fetchall():
    print(f'  {r}')

cur.execute("PRAGMA table_info(crawl_log)")
print('\ncrawl_log columns:')
for r in cur.fetchall():
    print(f'  {r}')

cur.execute("SELECT * FROM crawl_task")
print('\ncrawl_task data:')
for r in cur.fetchall():
    print(f'  {r}')

cur.execute("SELECT id, task_id, start_time, end_time, status FROM crawl_log")
print('\ncrawl_log data:')
for r in cur.fetchall():
    print(f'  {r}')

conn.close()
