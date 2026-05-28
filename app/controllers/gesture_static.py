"""
手势控制静态文件处理器
提供手势控制相关静态文件的访问
"""

import os
import tornado.web


class GestureStaticFileHandler(tornado.web.StaticFileHandler):
    """
    手势控制静态文件处理器
    用于访问gesture_control目录下的静态文件
    """
    
    def initialize(self, path):
        """
        初始化静态文件处理器
        """
        self.root = os.path.join(os.path.dirname(__file__), '..', '..', 'gesture_control')
        super().initialize(self.root)
