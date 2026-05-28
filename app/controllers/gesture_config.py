"""
手势配置管理控制器
提供手势配置的后台管理界面和API接口
"""

import json
import tornado.web
from app.controllers.base import BaseHandler
from app.models.gesture_config import GestureConfigRepository


class GestureConfigListHandler(BaseHandler):
    """
    手势配置列表页面控制器
    """
    
    def get(self):
        """
        渲染手势配置列表页面
        """
        configs = GestureConfigRepository.get_all_configs()
        xsrf_token = self.xsrf_token
        self.render('gesture_config_list.html', configs=configs, xsrf_token=xsrf_token)


class GestureConfigApiHandler(BaseHandler):
    """
    手势配置API控制器
    """
    
    def get(self):
        """
        获取所有手势配置
        """
        configs = GestureConfigRepository.get_all_configs()
        result = []
        for config in configs:
            result.append({
                'id': config['id'],
                'gesture_name': config['gesture_name'],
                'display_name': config['display_name'],
                'description': config['description'],
                'enabled': bool(config['enabled']),
                'action': config['action'],
                'sensitivity_threshold': config['sensitivity_threshold'],
                'hold_time': config['hold_time'],
                'created_at': config['created_at'],
                'updated_at': config['updated_at']
            })
        self.write(json.dumps(result))
    
    def put(self):
        """
        更新手势配置
        """
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            gesture_name = data.get('gesture_name')
            
            if not gesture_name:
                self.set_status(400)
                self.write({'error': '手势名称不能为空'})
                return
            
            update_fields = {}
            if 'enabled' in data:
                update_fields['enabled'] = data['enabled']
            if 'sensitivity_threshold' in data:
                update_fields['sensitivity_threshold'] = data['sensitivity_threshold']
            if 'hold_time' in data:
                update_fields['hold_time'] = data['hold_time']
            if 'display_name' in data:
                update_fields['display_name'] = data['display_name']
            if 'description' in data:
                update_fields['description'] = data['description']
            
            if not update_fields:
                self.set_status(400)
                self.write({'error': '没有提供要更新的字段'})
                return
            
            success = GestureConfigRepository.update_config(gesture_name, **update_fields)
            
            if success:
                self.write({'success': True, 'message': '配置更新成功'})
            else:
                self.set_status(400)
                self.write({'error': '配置更新失败'})
                
        except Exception as e:
            self.set_status(500)
            self.write({'error': str(e)})


class GestureToggleApiHandler(BaseHandler):
    """
    手势启用/禁用API控制器
    """
    
    def post(self):
        """
        启用/禁用手势
        """
        try:
            data = json.loads(self.request.body.decode('utf-8'))
            gesture_name = data.get('gesture_name')
            enabled = data.get('enabled')
            
            if not gesture_name or enabled is None:
                self.set_status(400)
                self.write({'error': '参数不完整'})
                return
            
            success = GestureConfigRepository.toggle_gesture(gesture_name, enabled)
            
            if success:
                status = '启用' if enabled else '禁用'
                self.write({'success': True, 'message': f'手势已{status}'})
            else:
                self.set_status(400)
                self.write({'error': '操作失败'})
                
        except Exception as e:
            self.set_status(500)
            self.write({'error': str(e)})
