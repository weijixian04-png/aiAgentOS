/**
 * 手势配置文件
 * 定义手势与系统动作的映射关系
 */

const GestureConfig = {
    enabled: false,
    
    gestures: {
        swipe_up: {
            name: '上划',
            description: '全局返回/退出当前子页面',
            enabled: true,
            action: 'navigateBack',
            sensitivity: {
                threshold: 50,
                holdTime: 300
            }
        },
        swipe_down: {
            name: '下划',
            description: '全局刷新/重新加载当前模块数据',
            enabled: true,
            action: 'refreshCurrentPage',
            sensitivity: {
                threshold: 50,
                holdTime: 300
            }
        },
        open_palm: {
            name: '张开手掌',
            description: '打开全局侧边栏快捷工具',
            enabled: true,
            action: 'openQuickPanel',
            sensitivity: {
                holdTime: 500
            }
        },
        thumbs_up: {
            name: '竖起大拇指',
            description: '快速跳转到智能问数子系统',
            enabled: true,
            action: 'navigateToChat',
            sensitivity: {
                holdTime: 500
            }
        },
        fist: {
            name: '握拳',
            description: '全屏截图并保存（仅本地）',
            enabled: true,
            action: 'takeScreenshot',
            sensitivity: {
                holdTime: 500
            }
        }
    },

    globalSettings: {
        defaultEnabled: false,
        showIndicator: true,
        indicatorPosition: 'bottom-right',
        cameraFacing: 'user',
        recognitionInterval: 100
    }
};

function getGestureConfig() {
    const stored = localStorage.getItem('gesture_config');
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            console.error('手势配置解析失败:', e);
        }
    }
    return GestureConfig;
}

function saveGestureConfig(config) {
    localStorage.setItem('gesture_config', JSON.stringify(config));
}

function updateGestureEnabled(gestureName, enabled) {
    const config = getGestureConfig();
    if (config.gestures[gestureName]) {
        config.gestures[gestureName].enabled = enabled;
        saveGestureConfig(config);
    }
}

function updateGlobalEnabled(enabled) {
    const config = getGestureConfig();
    config.enabled = enabled;
    saveGestureConfig(config);
}

window.GestureConfig = GestureConfig;
window.getGestureConfig = getGestureConfig;
window.saveGestureConfig = saveGestureConfig;
window.updateGestureEnabled = updateGestureEnabled;
window.updateGlobalEnabled = updateGlobalEnabled;
