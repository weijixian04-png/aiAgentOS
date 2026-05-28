/**
 * 手势控制UI组件
 * 提供全局手势开关按钮和状态指示器
 */

class GestureUI {
    constructor() {
        this.container = null;
        this.toggleButton = null;
        this.statusIndicator = null;
        this.gestureRecognition = null;
        this.isInitialized = false;
    }

    init() {
        if (this.isInitialized) return;
        
        this.createContainer();
        this.createToggleButton();
        this.createStatusIndicator();
        this.loadState();
        this.isInitialized = true;
        
        console.log('手势UI已初始化');
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'gesture-control-container';
        this.container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9998;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        `;
        document.body.appendChild(this.container);
    }

    createToggleButton() {
        this.toggleButton = document.createElement('div');
        this.toggleButton.id = 'gesture-toggle-button';
        this.toggleButton.style.cssText = `
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            position: relative;
        `;
        
        this.toggleButton.innerHTML = `
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"></path>
                <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"></path>
                <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"></path>
                <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"></path>
            </svg>
        `;
        
        this.toggleButton.addEventListener('mouseenter', () => {
            this.toggleButton.style.transform = 'scale(1.1)';
        });
        
        this.toggleButton.addEventListener('mouseleave', () => {
            this.toggleButton.style.transform = 'scale(1)';
        });
        
        this.toggleButton.addEventListener('click', () => {
            this.toggleGestureRecognition();
        });
        
        this.container.appendChild(this.toggleButton);
    }

    createStatusIndicator() {
        this.statusIndicator = document.createElement('div');
        this.statusIndicator.id = 'gesture-status-indicator';
        this.statusIndicator.style.cssText = `
            position: absolute;
            top: -8px;
            right: -8px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ff4444;
            border: 2px solid white;
            transition: background 0.3s;
        `;
        this.toggleButton.appendChild(this.statusIndicator);
    }

    async toggleGestureRecognition() {
        const config = getGestureConfig();
        const newState = !config.enabled;
        
        if (newState) {
            try {
                if (!this.gestureRecognition) {
                    this.gestureRecognition = new GestureRecognition();
                    await this.gestureRecognition.init();
                    
                    this.gestureRecognition.onGesture((gesture) => {
                        this.handleGesture(gesture);
                    });
                }
                
                this.gestureRecognition.start();
                this.statusIndicator.style.background = '#44ff44';
                this.showNotification('手势识别已启用', 'success');
                updateGlobalEnabled(true);
                
            } catch (error) {
                console.error('启用手势识别失败:', error);
                this.showNotification('启用手势识别失败，请检查摄像头权限', 'error');
            }
        } else {
            if (this.gestureRecognition) {
                this.gestureRecognition.stop();
            }
            this.statusIndicator.style.background = '#ff4444';
            this.showNotification('手势识别已禁用', 'info');
            updateGlobalEnabled(false);
        }
    }

    handleGesture(gesture) {
        const config = getGestureConfig();
        
        if (!config.enabled) return;
        
        const gestureConfig = config.gestures[gesture];
        if (!gestureConfig || !gestureConfig.enabled) {
            console.log('手势已禁用:', gesture);
            return;
        }
        
        console.log('识别到手势:', gesture, gestureConfig.name);
        this.showGestureIndicator(gestureConfig.name);
        
        if (window.gestureActionHandler) {
            window.gestureActionHandler.executeAction(gestureConfig.action);
        }
    }

    showGestureIndicator(gestureName) {
        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(102, 126, 234, 0.9);
            color: white;
            padding: 20px 40px;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            z-index: 10001;
            animation: fadeInOut 1.5s ease;
        `;
        indicator.textContent = gestureName;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
            style.remove();
        }, 1500);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            info: '#2196F3',
            warning: '#ff9800'
        };
        
        notification.style.cssText = `
            position: fixed;
            bottom: 90px;
            right: 20px;
            background: ${colors[type] || colors.info};
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
            z-index: 9999;
            animation: slideInRight 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        `;
        notification.textContent = message;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => {
                notification.remove();
                style.remove();
            }, 300);
        }, 2000);
    }

    loadState() {
        const config = getGestureConfig();
        if (config.enabled) {
            this.statusIndicator.style.background = '#44ff44';
        } else {
            this.statusIndicator.style.background = '#ff4444';
        }
    }
}

window.GestureUI = GestureUI;

document.addEventListener('DOMContentLoaded', () => {
    const gestureUI = new GestureUI();
    gestureUI.init();
    window.gestureUI = gestureUI;
});
