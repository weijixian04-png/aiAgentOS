import json
import os
import re
import sqlite3
from datetime import date, datetime

def _project_root():
	return os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))

DEFAULT_SQLITE_PATH = os.path.join("database", "app.db")
DB_PATH = os.path.join(_project_root(),"database","app.db")
DB_CONFIG_PATH = os.path.join(_project_root(),"database","db_config.json")
DEFAULT_DB_CONFIG = {
	"type": "sqlite",
	"sqlite_path": DEFAULT_SQLITE_PATH,
	"mysql": {
		"host": "127.0.0.1",
		"port": 3306,
		"user": "root",
		"password": "",
		"database": "ai_agent_os",
		"charset": "utf8mb4"
	}
}
MYSQL_LONGTEXT_COLUMNS = {
	"headers", "raw_content", "content", "prompt", "welcome_msg", "summary",
	"ai_analyze_msg", "ai_summary", "ai_keywords", "ai_sentiment", "ai_entities",
	"config", "announcement", "images", "tags", "categories", "message", "remark",
	"example", "description", "password_hash", "salt"
}
MYSQL_URL_COLUMNS = {"url", "base_url", "url_pattern", "source_url", "file_path"}

def _default_config_copy():
	config = json.loads(json.dumps(DEFAULT_DB_CONFIG))
	return config

def _env_value(*names):
	for name in names:
		value = os.environ.get(name)
		if value:
			return value
	return None

def _normalize_db_type(db_type):
	db_type = (db_type or "sqlite").strip().lower()
	return db_type if db_type in ("sqlite", "mysql") else "sqlite"

def get_database_config():
	config = _default_config_copy()
	if os.path.exists(DB_CONFIG_PATH):
		try:
			with open(DB_CONFIG_PATH, "r", encoding="utf-8") as file:
				saved_config = json.load(file)
			config.update({k: v for k, v in saved_config.items() if k != "mysql"})
			config["mysql"].update(saved_config.get("mysql", {}))
		except (OSError, json.JSONDecodeError):
			pass

	env_type = _env_value("DATABASE_TYPE", "DB_TYPE", "AIAgentOS_DB_TYPE")
	if env_type:
		config["type"] = env_type
	env_sqlite_path = _env_value("SQLITE_PATH", "DB_SQLITE_PATH")
	if env_sqlite_path:
		config["sqlite_path"] = env_sqlite_path
	mysql_env_map = {
		"host": ("MYSQL_HOST", "DB_MYSQL_HOST"),
		"port": ("MYSQL_PORT", "DB_MYSQL_PORT"),
		"user": ("MYSQL_USER", "DB_MYSQL_USER"),
		"password": ("MYSQL_PASSWORD", "DB_MYSQL_PASSWORD"),
		"database": ("MYSQL_DATABASE", "DB_MYSQL_DATABASE"),
		"charset": ("MYSQL_CHARSET", "DB_MYSQL_CHARSET")
	}
	for key, names in mysql_env_map.items():
		value = _env_value(*names)
		if value is not None:
			config["mysql"][key] = value
	config["type"] = _normalize_db_type(config.get("type"))
	config["mysql"]["port"] = int(config["mysql"].get("port") or 3306)
	if not config.get("sqlite_path"):
		config["sqlite_path"] = DEFAULT_SQLITE_PATH
	return config

def save_database_config(config):
	next_config = _default_config_copy()
	current = get_database_config()
	next_config.update({k: v for k, v in current.items() if k != "mysql"})
	next_config["mysql"].update(current.get("mysql", {}))
	next_config.update({k: v for k, v in config.items() if k != "mysql"})
	next_config["mysql"].update(config.get("mysql", {}))
	next_config["type"] = _normalize_db_type(next_config.get("type"))
	next_config["mysql"]["port"] = int(next_config["mysql"].get("port") or 3306)
	os.makedirs(os.path.dirname(DB_CONFIG_PATH), exist_ok=True)
	with open(DB_CONFIG_PATH, "w", encoding="utf-8") as file:
		json.dump(next_config, file, ensure_ascii=False, indent=2)
	return next_config

def get_database_status():
	config = get_database_config()
	if config["type"] == "mysql":
		mysql_config = config["mysql"]
		return {
			"type": "mysql",
			"detail": f"{mysql_config.get('user')}@{mysql_config.get('host')}:{mysql_config.get('port')}/{mysql_config.get('database')}"
		}
	return {"type": "sqlite", "detail": config.get("sqlite_path") or DEFAULT_SQLITE_PATH}

def _quote_mysql_identifier(identifier):
	identifier = (identifier or "").strip()
	if not re.match(r"^[A-Za-z0-9_]+$", identifier):
		raise ValueError("MySQL数据库名只能包含字母、数字和下划线")
	return f"`{identifier}`"

def _get_mysql_module():
	try:
		import pymysql
		return pymysql
	except ImportError as exc:
		raise RuntimeError("使用MySQL数据库需要先安装PyMySQL依赖") from exc

def _connect_mysql(config):
	pymysql = _get_mysql_module()
	mysql_config = config["mysql"]
	connect_args = {
		"host": mysql_config.get("host") or "127.0.0.1",
		"port": int(mysql_config.get("port") or 3306),
		"user": mysql_config.get("user") or "root",
		"password": mysql_config.get("password") or "",
		"database": mysql_config.get("database") or "ai_agent_os",
		"charset": mysql_config.get("charset") or "utf8mb4",
		"autocommit": False,
		"cursorclass": pymysql.cursors.DictCursor
	}
	try:
		return pymysql.connect(**connect_args)
	except pymysql.err.OperationalError as exc:
		if exc.args and exc.args[0] == 1049:
			database = connect_args.pop("database")
			setup_conn = pymysql.connect(**connect_args)
			try:
				with setup_conn.cursor() as cursor:
					cursor.execute(f"CREATE DATABASE IF NOT EXISTS {_quote_mysql_identifier(database)} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
				setup_conn.commit()
			finally:
				setup_conn.close()
			connect_args["database"] = database
			return pymysql.connect(**connect_args)
		raise

def _mysql_text_type(column, rest):
	upper_rest = rest.upper()
	if "UNIQUE" in upper_rest or "DEFAULT" in upper_rest:
		return "VARCHAR(255)"
	if column in MYSQL_LONGTEXT_COLUMNS:
		return "LONGTEXT"
	if column in MYSQL_URL_COLUMNS:
		return "VARCHAR(1024)"
	return "VARCHAR(255)"

def _adapt_mysql_column_line(line):
	line = re.sub(r"\binteger\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "INT AUTO_INCREMENT PRIMARY KEY", line, flags=re.IGNORECASE)
	text_match = re.match(r"(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s+)TEXT(\b.*)", line, flags=re.IGNORECASE)
	if text_match:
		column = text_match.group(2).lower()
		rest = text_match.group(4)
		if "DEFAULT CURRENT_TIMESTAMP" in rest.upper():
			line = f"{text_match.group(1)}{text_match.group(2)}{text_match.group(3)}DATETIME{rest}"
		else:
			line = f"{text_match.group(1)}{text_match.group(2)}{text_match.group(3)}{_mysql_text_type(column, rest)}{rest}"
	line = re.sub(r"\bINTEGER\b", "INT", line, flags=re.IGNORECASE)
	line = re.sub(r"\bREAL\b", "DOUBLE", line, flags=re.IGNORECASE)
	return line

def _adapt_mysql_create_table(sql):
	if not re.match(r"\s*CREATE\s+TABLE", sql, flags=re.IGNORECASE):
		return sql
	adapted = "\n".join(_adapt_mysql_column_line(line) for line in sql.splitlines())
	if "ENGINE=" not in adapted.upper():
		adapted = re.sub(r")\s*$", ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4", adapted.strip(), flags=re.DOTALL)
	return adapted

def _adapt_mysql_alter_table(sql):
	if not re.match(r"\s*ALTER\s+TABLE", sql, flags=re.IGNORECASE):
		return sql
	sql = re.sub(r"\bADD\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\s+TEXT\b", r"ADD COLUMN \1 VARCHAR(255)", sql, flags=re.IGNORECASE)
	sql = re.sub(r"\bINTEGER\b", "INT", sql, flags=re.IGNORECASE)
	sql = re.sub(r"\bREAL\b", "DOUBLE", sql, flags=re.IGNORECASE)
	return sql

def _adapt_mysql_sql(sql):
	adapted = sql
	adapted = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT IGNORE INTO", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "REPLACE INTO", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"DEFAULT\s*\(\s*datetime\s*\(\s*'now'\s*\)\s*\)", "DEFAULT CURRENT_TIMESTAMP", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"DEFAULT\s*\(\s*'([^']*)'\s*\)", r"DEFAULT '\1'", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"DEFAULT\s*\(\s*([0-9.]+)\s*\)", r"DEFAULT \1", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"datetime\s*\(\s*'now'\s*\)", "NOW()", adapted, flags=re.IGNORECASE)
	adapted = re.sub(r"\binteger\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "INT AUTO_INCREMENT PRIMARY KEY", adapted, flags=re.IGNORECASE)
	adapted = _adapt_mysql_create_table(adapted)
	adapted = _adapt_mysql_alter_table(adapted)
	return adapted.replace("?", "%s")

def _mysql_result_value(value):
	if isinstance(value, datetime):
		return value.strftime("%Y-%m-%d %H:%M:%S")
	if isinstance(value, date):
		return value.strftime("%Y-%m-%d")
	return value

def _mysql_result_row(row):
	if row is None:
		return None
	return {key: _mysql_result_value(value) for key, value in row.items()}

class MySQLCursorAdapter:
	def __init__(self, cursor):
		self._cursor = cursor
		self.lastrowid = cursor.lastrowid
		self.rowcount = cursor.rowcount

	def fetchone(self):
		return _mysql_result_row(self._cursor.fetchone())

	def fetchall(self):
		return [_mysql_result_row(row) for row in self._cursor.fetchall()]

class MySQLConnectionAdapter:
	def __init__(self, raw_connection, pymysql):
		self._connection = raw_connection
		self._pymysql = pymysql

	def execute(self, sql, params=None):
		try:
			cursor = self._connection.cursor()
			cursor.execute(_adapt_mysql_sql(sql), tuple(params or ()))
			return MySQLCursorAdapter(cursor)
		except self._pymysql.err.IntegrityError as exc:
			raise sqlite3.IntegrityError(str(exc)) from exc
		except (self._pymysql.err.OperationalError, self._pymysql.err.ProgrammingError) as exc:
			raise sqlite3.OperationalError(str(exc)) from exc

	def commit(self):
		self._connection.commit()

	def rollback(self):
		self._connection.rollback()

	def close(self):
		self._connection.close()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			self.rollback()
		else:
			self.commit()
		self.close()
		return False

def test_database_connection(config=None):
	try:
		test_config = config or get_database_config()
		if _normalize_db_type(test_config.get("type")) == "mysql":
			conn = _connect_mysql(test_config)
			conn.close()
		else:
			sqlite_path = test_config.get("sqlite_path") or DEFAULT_SQLITE_PATH
			if not os.path.isabs(sqlite_path):
				sqlite_path = os.path.join(_project_root(), sqlite_path)
			os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
			conn = sqlite3.connect(sqlite_path)
			conn.close()
		return True, "数据库连接成功"
	except Exception as exc:
		return False, str(exc)

def get_connection(sqlite_path=None):
	config = get_database_config()
	if config["type"] == "mysql":
		return MySQLConnectionAdapter(_connect_mysql(config), _get_mysql_module())
	db_path = sqlite_path or config.get("sqlite_path") or DEFAULT_SQLITE_PATH
	if not os.path.isabs(db_path):
		db_path = os.path.join(_project_root(), db_path)
	os.makedirs(os.path.dirname(db_path), exist_ok=True)
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	with get_connection() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS user(
				id integer PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL,
				salt TEXT NOT NULL,
				role TEXT NOT NULL DEFAULT('user'),
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
				
			)
			"""
		)
		# 如果表已存在，添加role字段（如果不存在）
		try:
			conn.execute("ALTER TABLE user ADD COLUMN role TEXT NOT NULL DEFAULT('user')")
			conn.commit()
		except sqlite3.OperationalError:
			pass  # 字段已存在
		
		# 创建模型服务表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS model_service(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				model TEXT NOT NULL,
				api_key TEXT NOT NULL,
				base_url TEXT NOT NULL,
				max_tokens INTEGER DEFAULT 4096,
				temperature REAL DEFAULT 0.7,
				is_default INTEGER DEFAULT 0,
				token_usage INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_source(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				url_pattern TEXT NOT NULL,
				request_method TEXT DEFAULT 'GET',
				headers TEXT,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS api_interface(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				url TEXT NOT NULL,
				method TEXT DEFAULT 'GET',
				response_format TEXT DEFAULT 'JSON',
				example TEXT,
				qps_limit TEXT,
				token_required INTEGER DEFAULT 0,
				remark TEXT,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS digital_employee(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				alias TEXT NOT NULL UNIQUE,
				category TEXT NOT NULL DEFAULT 'AI',
				description TEXT,
				prompt TEXT,
				model_id INTEGER,
				api_interface_id INTEGER,
				avatar TEXT,
				welcome_msg TEXT,
				sort_order INTEGER DEFAULT 0,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		# 如果表已存在，添加sort_order字段（如果不存在）
		try:
			conn.execute("ALTER TABLE digital_employee ADD COLUMN sort_order INTEGER DEFAULT 0")
			conn.commit()
		except sqlite3.OperationalError:
			pass  # 字段已存在
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_record(
				id integer PRIMARY KEY AUTOINCREMENT,
				source_id INTEGER NOT NULL,
				source_name TEXT NOT NULL,
				keyword TEXT,
				url TEXT NOT NULL,
				title TEXT,
				summary TEXT,
				raw_content TEXT,
				status TEXT DEFAULT 'pending',
				ai_analyzed INTEGER DEFAULT 0,
				ai_analyze_status TEXT DEFAULT 'pending',
				ai_analyze_msg TEXT,
				ai_analyze_time TEXT,
				collect_time TEXT NOT NULL DEFAULT(datetime('now')),
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_detail(
				id integer PRIMARY KEY AUTOINCREMENT,
				record_id INTEGER NOT NULL,
				source_id INTEGER NOT NULL,
				title TEXT,
				content TEXT,
				author TEXT,
				publish_time TEXT,
				source_url TEXT,
				tags TEXT,
				categories TEXT,
				images TEXT,
				ai_summary TEXT,
				ai_keywords TEXT,
				ai_sentiment TEXT,
				ai_entities TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (record_id) REFERENCES scout_record(id) ON DELETE CASCADE
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_session(
				id integer PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				title TEXT,
				model_id INTEGER,
				employee_id INTEGER,
				session_type TEXT DEFAULT 'chat',
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				session_id INTEGER NOT NULL,
				role TEXT NOT NULL,
				content TEXT NOT NULL,
				tokens INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (session_id) REFERENCES chat_session(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_screen(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				description TEXT,
				config TEXT DEFAULT '{}',
				refresh_interval INTEGER DEFAULT 60,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_location(
				id integer PRIMARY KEY AUTOINCREMENT,
				latitude REAL NOT NULL,
				longitude REAL NOT NULL,
				location_name TEXT,
				location_type TEXT DEFAULT 'default',
				source_id INTEGER,
				source_type TEXT DEFAULT 'scout',
				title TEXT,
				summary TEXT,
				sentiment TEXT DEFAULT 'neutral',
				tags TEXT,
				event_time TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_cache(
				id integer PRIMARY KEY AUTOINCREMENT,
				cache_key TEXT NOT NULL UNIQUE,
				cache_value TEXT NOT NULL,
				expire_at TEXT,
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS sentiment_analysis(
				id integer PRIMARY KEY AUTOINCREMENT,
				source_type TEXT NOT NULL,
				source_id INTEGER,
				source_record_id INTEGER,
				title TEXT,
				content TEXT NOT NULL,
				summary TEXT,
				sentiment TEXT DEFAULT 'neutral',
				sentiment_score REAL DEFAULT 0.5,
				confidence REAL DEFAULT 0.0,
				keywords TEXT,
				topics TEXT,
				hot_score REAL DEFAULT 0.0,
				risk_level TEXT DEFAULT 'low',
				risk_tags TEXT,
				location_lat REAL,
				location_lng REAL,
				location_name TEXT,
				publish_time TEXT,
				analyze_time TEXT NOT NULL DEFAULT(datetime('now')),
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS sentiment_analysis_log(
				id integer PRIMARY KEY AUTOINCREMENT,
				analysis_id INTEGER,
				action TEXT NOT NULL,
				status TEXT DEFAULT 'running',
				total_count INTEGER DEFAULT 0,
				success_count INTEGER DEFAULT 0,
				fail_count INTEGER DEFAULT 0,
				error_msg TEXT,
				duration_ms INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS friendship(
				id integer PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				friend_id INTEGER NOT NULL,
				status TEXT DEFAULT 'pending',
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
				FOREIGN KEY (friend_id) REFERENCES user(id) ON DELETE CASCADE,
				UNIQUE(user_id, friend_id)
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS private_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				from_user_id INTEGER NOT NULL,
				to_user_id INTEGER NOT NULL,
				content TEXT NOT NULL,
				is_read INTEGER DEFAULT 0,
				send_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (from_user_id) REFERENCES user(id) ON DELETE CASCADE,
				FOREIGN KEY (to_user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_chat(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				avatar TEXT DEFAULT '👥',
				description TEXT,
				creator_id INTEGER NOT NULL,
				status TEXT DEFAULT 'active',
				is_public INTEGER DEFAULT 0,
				max_members INTEGER DEFAULT 200,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (creator_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_member(
				id integer PRIMARY KEY AUTOINCREMENT,
				group_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				role TEXT DEFAULT 'member',
				join_time TEXT NOT NULL DEFAULT(datetime('now')),
				last_active TEXT,
				is_muted INTEGER DEFAULT 0,
				is_banned INTEGER DEFAULT 0,
				FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE,
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
				UNIQUE(group_id, user_id)
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				group_id INTEGER NOT NULL,
				from_user_id INTEGER NOT NULL,
				content TEXT NOT NULL,
				message_type TEXT DEFAULT 'text',
				file_path TEXT,
				file_name TEXT,
				is_read INTEGER DEFAULT 0,
				mentioned_users TEXT,
				send_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE,
				FOREIGN KEY (from_user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_file(
				id integer PRIMARY KEY AUTOINCREMENT,
				file_hash TEXT NOT NULL UNIQUE,
				file_name TEXT NOT NULL,
				file_path TEXT NOT NULL,
				file_size INTEGER NOT NULL,
				content_type TEXT,
				uploader_id INTEGER,
				upload_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (uploader_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_server(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				host TEXT NOT NULL,
				port INTEGER DEFAULT 80,
				protocol TEXT DEFAULT 'http',
				is_active INTEGER DEFAULT 1,
				is_default INTEGER DEFAULT 0,
				weight INTEGER DEFAULT 1,
				description TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.commit()

def init_default_users():
	"""初始化默认测试用户"""
	import hashlib
	import secrets
	
	def hash_password(password: str, salt: bytes) -> str:
		dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
		return dk.hex()
	
	default_users = [
		{"username": "Alice", "password": "test123", "role": "user"},
		{"username": "Bob", "password": "test123", "role": "user"},
		{"username": "Charlie", "password": "test123", "role": "user"},
		{"username": "David", "password": "test123", "role": "user"},
		{"username": "Eve", "password": "test123", "role": "user"},
	]
	
	with get_connection() as conn:
		for user in default_users:
			existing = conn.execute("SELECT id FROM user WHERE username = ?", (user["username"],)).fetchone()
			if not existing:
				salt = secrets.token_bytes(16)
				password_hash = hash_password(user["password"], salt)
				try:
					conn.execute(
						"INSERT INTO user(username, password_hash, salt, role) VALUES(?, ?, ?, ?)",
						(user["username"], password_hash, salt.hex(), user["role"])
					)
				except sqlite3.IntegrityError:
					pass
		conn.commit()

def init_scout_sources():
	"""初始化瞭望数据源示例数据"""
	BAIDU_NEWS_HEADERS = """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Referer: https://news.baidu.com/
sec-ch-ua: "Chromium";v="141", "Not?A_Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-site
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1"""
	
	sample_sources = [
		{
			"name": "百度新闻搜索",
			"url_pattern": "https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&rsv_dl=ns_pc&word={关键字}",
			"request_method": "GET",
			"headers": BAIDU_NEWS_HEADERS,
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for source in sample_sources:
			try:
				existing = conn.execute("SELECT id FROM scout_source WHERE name = ?", (source["name"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO scout_source(name, url_pattern, request_method, headers, enabled) VALUES(?, ?, ?, ?, ?)",
						(source["name"], source["url_pattern"], source["request_method"], source["headers"], source["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_digital_employees():
	"""初始化数字员工示例数据"""
	sample_employees = [
		{
			"name": "川小农",
			"alias": "川小农",
			"category": "AI",
			"description": "智能农业助手，基于大模型提供农业相关的智能问答服务",
			"prompt": "你是川小农，一个专业的智能农业助手。你精通农业种植、养殖、农产品加工、农业政策等领域的知识。请用专业、友好、简洁的方式回答用户关于农业的问题。如果问题超出农业领域，请礼貌地告知用户你的专业范围。",
			"model_id": None,
			"api_interface_id": None,
			"avatar": "🌾",
			"welcome_msg": "你好！我是川小农，你的智能农业助手。有什么农业方面的问题可以问我哦！",
			"enabled": 1
		},
		{
			"name": "天气助手",
			"alias": "天气",
			"category": "普通",
			"description": "天气查询助手，提供城市天气信息查询服务。使用方式：@天气 城市名称",
			"prompt": None,
			"model_id": None,
			"api_interface_id": 2,
			"avatar": "🌤️",
			"welcome_msg": "你好！我是天气助手，输入城市名称即可查询天气信息。例如：北京",
			"enabled": 1
		},
		{
			"name": "音乐助手",
			"alias": "音乐",
			"category": "普通",
			"description": "随机音乐推荐助手，提供网易云音乐随机歌曲推荐服务。使用方式：@音乐",
			"prompt": None,
			"model_id": None,
			"api_interface_id": 1,
			"avatar": "🎵",
			"welcome_msg": "你好！我是音乐助手，随时为你推荐好听的音乐！",
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for employee in sample_employees:
			try:
				existing = conn.execute("SELECT id FROM digital_employee WHERE alias = ?", (employee["alias"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO digital_employee(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
						(employee["name"], employee["alias"], employee["category"], employee["description"], employee["prompt"], employee["model_id"], employee["api_interface_id"], employee["avatar"], employee["welcome_msg"], employee["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_api_interfaces():
	"""初始化接口管理示例数据"""
	sample_interfaces = [
		{
			"name": "网易云随机音乐",
			"url": "https://api.52vmy.cn/api/music/wy/rand",
			"method": "GET",
			"response_format": "JSON",
			"example": "https://api.52vmy.cn/api/music/wy/rand",
			"qps_limit": "每2秒最多4次，携带Token可无限制",
			"token_required": 0,
			"remark": "获取网易云音乐随机歌曲",
			"enabled": 1
		},
		{
			"name": "天气查询",
			"url": "https://api.52vmy.cn/api/query/tian",
			"method": "GET",
			"response_format": "JSON",
			"example": "https://api.52vmy.cn/api/query/tian?city=北京市",
			"qps_limit": "每2秒最多4次，携带Token可无限制",
			"token_required": 0,
			"remark": "查询城市天气信息，参数city为城市名称",
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for interface in sample_interfaces:
			try:
				existing = conn.execute("SELECT id FROM api_interface WHERE url = ?", (interface["url"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO api_interface(name, url, method, response_format, example, qps_limit, token_required, remark, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
						(interface["name"], interface["url"], interface["method"], interface["response_format"], interface["example"], interface["qps_limit"], interface["token_required"], interface["remark"], interface["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_sentiment_samples():
	"""初始化舆情分析示例数据"""
	from datetime import datetime, timedelta
	
	sample_sentiments = [
		{
			"source_type": "scout",
			"title": "农业科技创新助力乡村振兴",
			"content": "近年来，我国农业科技创新取得显著进展，人工智能、大数据、物联网等新技术正在深刻改变传统农业生产方式。智慧农业、精准农业等新模式不断涌现，为乡村振兴注入了新动能。",
			"summary": "农业科技创新推动乡村振兴发展",
			"sentiment": "positive",
			"sentiment_score": 0.85,
			"confidence": 0.92,
			"keywords": "农业科技,乡村振兴,智慧农业,精准农业",
			"risk_level": "low",
			"hot_score": 85.5,
			"location_name": "北京市",
			"location_lat": 39.9042,
			"location_lng": 116.4074,
			"publish_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农产品价格波动引发市场关注",
			"content": "近期部分农产品价格出现较大波动，引起市场广泛关注。专家指出，气候异常、物流成本上升等因素是导致价格波动的主要原因，建议农户做好风险管理。",
			"summary": "农产品价格波动受多种因素影响",
			"sentiment": "neutral",
			"sentiment_score": 0.52,
			"confidence": 0.88,
			"keywords": "农产品,价格波动,市场,风险管理",
			"risk_level": "medium",
			"hot_score": 72.3,
			"location_name": "上海市",
			"location_lat": 31.2304,
			"location_lng": 121.4737,
			"publish_time": (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "极端天气对农作物造成严重影响",
			"content": "今年夏季多地遭遇极端高温天气，部分地区农作物受损严重。农业部门已启动应急预案，指导农户采取抗旱措施，尽量减少损失。",
			"summary": "极端高温天气影响农作物生长",
			"sentiment": "negative",
			"sentiment_score": 0.28,
			"confidence": 0.95,
			"keywords": "极端天气,高温,农作物,抗旱",
			"risk_level": "high",
			"risk_tags": "自然灾害",
			"hot_score": 92.8,
			"location_name": "河南省",
			"location_lat": 34.7466,
			"location_lng": 113.6253,
			"publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "chat",
			"title": "用户咨询农业贷款政策",
			"content": "用户询问农业贷款的申请条件和利率政策，客服详细解释了相关政策，并提供了申请流程指引。",
			"summary": "用户咨询农业贷款政策",
			"sentiment": "neutral",
			"sentiment_score": 0.55,
			"confidence": 0.85,
			"keywords": "农业贷款,政策,利率,申请",
			"risk_level": "low",
			"hot_score": 45.2,
			"publish_time": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "新型农药研发取得突破",
			"content": "国内某农业科技公司宣布在新型生物农药研发方面取得重大突破，该农药对环境友好，杀虫效果显著，有望在明年大面积推广应用。",
			"summary": "新型生物农药研发成功",
			"sentiment": "positive",
			"sentiment_score": 0.91,
			"confidence": 0.94,
			"keywords": "农药,生物农药,研发,环保",
			"risk_level": "low",
			"hot_score": 88.6,
			"location_name": "广东省",
			"location_lat": 23.1291,
			"location_lng": 113.2644,
			"publish_time": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "chat",
			"title": "用户投诉农产品质量问题",
			"content": "用户反映购买的农产品存在质量问题，要求退换货。客服已受理投诉，并承诺在24小时内给出处理结果。",
			"summary": "用户投诉农产品质量问题",
			"sentiment": "negative",
			"sentiment_score": 0.22,
			"confidence": 0.89,
			"keywords": "质量问题,投诉,退换货",
			"risk_level": "medium",
			"risk_tags": "质量投诉",
			"hot_score": 67.5,
			"publish_time": (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农村电商助力农产品上行",
			"content": "农村电商平台发展迅速，越来越多的农产品通过网络销售到全国各地。直播带货、短视频推广等新模式让优质农产品走进千家万户。",
			"summary": "农村电商促进农产品销售",
			"sentiment": "positive",
			"sentiment_score": 0.82,
			"confidence": 0.90,
			"keywords": "农村电商,直播带货,农产品,销售",
			"risk_level": "low",
			"hot_score": 78.9,
			"location_name": "浙江省",
			"location_lat": 30.2741,
			"location_lng": 120.1552,
			"publish_time": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农业保险政策进一步完善",
			"content": "国家出台新政策，进一步完善农业保险体系，扩大保险覆盖范围，提高赔付比例，为农户提供更全面的风险保障。",
			"summary": "农业保险政策完善",
			"sentiment": "positive",
			"sentiment_score": 0.88,
			"confidence": 0.93,
			"keywords": "农业保险,政策,风险保障",
			"risk_level": "low",
			"hot_score": 71.2,
			"location_name": "四川省",
			"location_lat": 30.5728,
			"location_lng": 104.0668,
			"publish_time": (datetime.now() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
		}
	]
	
	with get_connection() as conn:
		count = conn.execute("SELECT COUNT(*) as total FROM sentiment_analysis").fetchone()["total"]
		if count == 0:
			for item in sample_sentiments:
				conn.execute(
					"""INSERT INTO sentiment_analysis(source_type, title, content, summary, sentiment,
					   sentiment_score, confidence, keywords, risk_level, risk_tags, hot_score,
					   location_name, location_lat, location_lng, publish_time)
					   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
					(item["source_type"], item["title"], item["content"], item["summary"],
					 item["sentiment"], item["sentiment_score"], item["confidence"],
					 item["keywords"], item["risk_level"], item.get("risk_tags"),
					 item["hot_score"], item.get("location_name"), item.get("location_lat"),
					 item.get("location_lng"), item["publish_time"])
				)
			conn.commit()