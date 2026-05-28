"""
手势配置数据模型
管理手势识别的配置参数
"""

import sqlite3
from app.models.db import get_connection


class GestureConfigRepository:
    """
    手势配置数据访问对象
    """
    
    @staticmethod
    def init_gesture_config_table():
        """
        初始化手势配置表
        """
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gesture_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gesture_name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    action TEXT NOT NULL,
                    sensitivity_threshold INTEGER DEFAULT 50,
                    hold_time INTEGER DEFAULT 500,
                    created_at TEXT NOT NULL DEFAULT(datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT(datetime('now'))
                )
                """
            )
    
    @staticmethod
    def init_default_gesture_configs():
        """
        初始化默认手势配置
        5个手势：点赞手势、张开手掌、胜利手势、食指指向、打电话手势
        """
        GestureConfigRepository.migrate_old_gestures()

        default_configs = [
            ('thumbs_up', '点赞手势', '全局返回/退出当前子页面', 1, 'goBack', 0, 500),
            ('open_palm', '张开手掌', '全局刷新/重新加载当前模块数据', 1, 'refreshPage', 0, 500),
            ('victory', '胜利手势(V)', '打开消息通知中心', 1, 'openNotificationCenter', 0, 500),
            ('pointing', '食指指向', '全屏截图并保存到本地', 1, 'takeScreenshot', 0, 500),
            ('call_me', '打电话手势', '切换语音朗读开关', 1, 'toggleVoiceReading', 0, 500),
        ]
        
        with get_connection() as conn:
            for config in default_configs:
                try:
                    conn.execute(
                        """
                        INSERT INTO gesture_config 
                        (gesture_name, display_name, description, enabled, action, sensitivity_threshold, hold_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        config
                    )
                except sqlite3.IntegrityError:
                    pass
    
    @staticmethod
    def get_all_configs():
        """
        获取所有手势配置
        """
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, gesture_name, display_name, description, enabled, action,
                       sensitivity_threshold, hold_time, created_at, updated_at
                FROM gesture_config
                ORDER BY id
                """
            ).fetchall()
        return rows
    
    @staticmethod
    def get_config_by_name(gesture_name):
        """
        根据手势名称获取配置
        """
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, gesture_name, display_name, description, enabled, action,
                       sensitivity_threshold, hold_time, created_at, updated_at
                FROM gesture_config
                WHERE gesture_name = ?
                """,
                (gesture_name,)
            ).fetchone()
        return row
    
    @staticmethod
    def update_config(gesture_name, **kwargs):
        """
        更新手势配置
        """
        allowed_fields = ['enabled', 'sensitivity_threshold', 'hold_time', 'display_name', 'description']
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = datetime('now')")
        values.append(gesture_name)
        
        with get_connection() as conn:
            conn.execute(
                f"""
                UPDATE gesture_config
                SET {', '.join(updates)}
                WHERE gesture_name = ?
                """,
                values
            )
        return True
    
    @staticmethod
    def toggle_gesture(gesture_name, enabled):
        """
        启用/禁用手势
        """
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE gesture_config
                SET enabled = ?, updated_at = datetime('now')
                WHERE gesture_name = ?
                """,
                (1 if enabled else 0, gesture_name)
            )
        return True

    @staticmethod
    def migrate_old_gestures():
        """
        迁移旧版手势配置到新版
        删除旧手势，更新已有手势的描述和动作
        """
        old_gestures = ['swipe_up', 'swipe_down', 'fist',
                        'swipe_left', 'swipe_right']
        with get_connection() as conn:
            for old_name in old_gestures:
                conn.execute(
                    "DELETE FROM gesture_config WHERE gesture_name = ?",
                    (old_name,)
                )
            conn.execute(
                "DELETE FROM gesture_config WHERE gesture_name = 'pointing'"
            )
            conn.execute(
                "DELETE FROM gesture_config WHERE gesture_name = 'victory'"
            )
            conn.execute(
                "DELETE FROM gesture_config WHERE gesture_name = 'call_me'"
            )
