"""
手势交互控制器
处理手势演示页面的路由
"""

import tornado.web
from app.controllers.base import BaseHandler


class GestureDemoHandler(BaseHandler):
    """
    手势演示页面控制器
    """
    
    def get(self):
        """
        渲染手势演示页面
        """
        self.render('gesture_control/demo.html')
