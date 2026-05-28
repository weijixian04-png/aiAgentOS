const GestureConfig = {
    enabled: false,

    gestures: {
        thumbs_up: {
            name: '点赞手势',
            description: '全局返回/退出当前子页面',
            enabled: true,
            action: 'goBack',
            sensitivity: {
                holdTime: 500
            }
        },
        open_palm: {
            name: '张开手掌',
            description: '全局刷新/重新加载当前模块数据',
            enabled: true,
            action: 'refreshPage',
            sensitivity: {
                holdTime: 500
            }
        },
        victory: {
            name: '胜利手势(V)',
            description: '打开消息通知中心',
            enabled: true,
            action: 'openNotificationCenter',
            sensitivity: {
                holdTime: 500
            }
        },
        pointing: {
            name: '食指指向',
            description: '全屏截图并保存到本地',
            enabled: true,
            action: 'takeScreenshot',
            sensitivity: {
                holdTime: 500
            }
        },
        call_me: {
            name: '打电话手势',
            description: '切换语音朗读开关',
            enabled: true,
            action: 'toggleVoiceReading',
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
            console.error('Gesture config parse error:', e);
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
