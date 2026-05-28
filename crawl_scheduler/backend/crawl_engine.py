import requests
from bs4 import BeautifulSoup
from datetime import datetime
from app.models.crawl_task import CrawlTaskRepository, CrawlLogRepository


def run_crawl_task(task_id):
    task = CrawlTaskRepository.get_by_id(task_id)
    if not task:
        print(f"[CrawlScheduler] Task {task_id} not found")
        return None

    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_id = CrawlLogRepository.create(task_id, start_time, 'running')

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        response = requests.get(task['url'], headers=headers, timeout=30)
        response.encoding = response.apparent_encoding
        status_code = response.status_code

        if status_code != 200:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            CrawlLogRepository.update(log_id, end_time=end_time, status='failed',
                                       error_msg=f'HTTP {status_code}',
                                       result_summary=f'请求失败，状态码: {status_code}')
            CrawlTaskRepository.update(task_id, last_run=end_time)
            return {'success': False, 'error': f'HTTP {status_code}'}

        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        extract_rule = task.get('extract_rule', 'title')
        raw_content = ''

        if extract_rule == 'title':
            title_tag = soup.find('title')
            raw_content = title_tag.get_text(strip=True) if title_tag else '无标题'

        elif extract_rule == 'text':
            body = soup.find('body')
            if body:
                text = body.get_text(separator=' ', strip=True)
                raw_content = text[:500] if len(text) > 500 else text
            else:
                raw_content = soup.get_text(separator=' ', strip=True)[:500]

        elif extract_rule.startswith('css:'):
            selector = extract_rule[4:].strip()
            elements = soup.select(selector)
            if elements:
                texts = [el.get_text(strip=True) for el in elements]
                combined = '\n'.join(texts)
                raw_content = combined[:500] if len(combined) > 500 else combined
            else:
                raw_content = f'未找到匹配选择器 "{selector}" 的元素'
        else:
            raw_content = soup.get_text(separator=' ', strip=True)[:500]

        result_summary = raw_content[:200] if len(raw_content) > 200 else raw_content
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        CrawlLogRepository.update(log_id, end_time=end_time, status='success',
                                   result_summary=result_summary,
                                   raw_content=raw_content)
        CrawlTaskRepository.update(task_id, last_run=end_time)

        return {'success': True, 'summary': result_summary, 'content_length': len(raw_content)}

    except requests.Timeout:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        CrawlLogRepository.update(log_id, end_time=end_time, status='failed',
                                   error_msg='请求超时（30秒）')
        CrawlTaskRepository.update(task_id, last_run=end_time)
        return {'success': False, 'error': '请求超时'}

    except requests.ConnectionError:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        CrawlLogRepository.update(log_id, end_time=end_time, status='failed',
                                   error_msg='连接失败，无法访问目标URL')
        CrawlTaskRepository.update(task_id, last_run=end_time)
        return {'success': False, 'error': '连接失败'}

    except Exception as e:
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        CrawlLogRepository.update(log_id, end_time=end_time, status='failed',
                                   error_msg=str(e))
        CrawlTaskRepository.update(task_id, last_run=end_time)
        return {'success': False, 'error': str(e)}
