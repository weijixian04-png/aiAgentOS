class GestureUI {
    constructor() {
        this.container = null;
        this.toggleButton = null;
        this.statusIndicator = null;
        this.gestureRecognition = null;
        this.gestureActionHandler = null;
        this.isInitialized = false;
        this.isRecognizing = false;
        this.notificationTimeouts = [];
    }

    init() {
        if (this.isInitialized) return;
        console.log('[Gesture] Initializing UI...');

        this.gestureActionHandler = new GestureActionHandler();
        window.gestureActionHandler = this.gestureActionHandler;

        this.createContainer();
        this.createToggleButton();
        this.loadSavedState();
        this.isInitialized = true;
        console.log('[Gesture] UI initialized');
    }

    createContainer() {
        if (document.getElementById('gesture-control-container')) {
            this.container = document.getElementById('gesture-control-container');
            return;
        }
        this.container = document.createElement('div');
        this.container.id = 'gesture-control-container';
        this.container.style.cssText = `
            position:fixed; bottom:20px; right:20px; z-index:99998;
            font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
        `;
        document.body.appendChild(this.container);
    }

    createToggleButton() {
        const existing = document.getElementById('gesture-toggle-button');
        if (existing) {
            existing.remove();
        }

        this.toggleButton = document.createElement('div');
        this.toggleButton.id = 'gesture-toggle-button';
        this.toggleButton.style.cssText = `
            width:60px; height:60px; border-radius:50%;
            background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);
            box-shadow:0 4px 20px rgba(79,172,254,0.5);
            cursor:pointer; display:flex; align-items:center; justify-content:center;
            transition:all 0.3s cubic-bezier(0.4,0,0.2,1);
            position:relative; user-select:none; -webkit-user-select:none;
        `;

        this.toggleButton.innerHTML = `
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"></path>
                <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"></path>
                <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"></path>
                <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"></path>
            </svg>
            <div id="gesture-status-indicator" style="position:absolute; top:-5px; right:-5px; width:18px; height:18px;
                border-radius:50%; background:#ff4444; border:2px solid white; transition:all 0.3s ease;
                box-shadow:0 2px 6px rgba(0,0,0,0.2);"></div>
        `;

        this.statusIndicator = this.toggleButton.querySelector('#gesture-status-indicator');

        this.toggleButton.addEventListener('mouseenter', () => {
            this.toggleButton.style.transform = 'scale(1.08)';
            this.toggleButton.style.boxShadow = '0 6px 25px rgba(79,172,254,0.6)';
        });
        this.toggleButton.addEventListener('mouseleave', () => {
            if (!this.isRecognizing) {
                this.toggleButton.style.transform = 'scale(1)';
                this.toggleButton.style.boxShadow = '0 4px 20px rgba(79,172,254,0.5)';
            }
        });
        this.toggleButton.addEventListener('click', () => {
            this.toggleGestureRecognition();
        });

        this.container.appendChild(this.toggleButton);
    }

    async toggleGestureRecognition() {
        if (!this.isRecognizing) {
            await this.startGestureRecognition();
        } else {
            this.stopGestureRecognition();
        }
    }

    async startGestureRecognition() {
        try {
            this.showLoadingState();
            this.showToast('正在启用手势识别...', 'info');

            if (!this.gestureRecognition) {
                this.gestureRecognition = new GestureRecognition();
                await this.gestureRecognition.init();

                const config = (typeof getGestureConfig === 'function') ? getGestureConfig() : {};
                if (config.gestures) {
                    const first = Object.values(config.gestures)[0];
                    if (first && first.sensitivity) {
                        this.gestureRecognition.setConfig({
                            holdTime: first.sensitivity.holdTime || 500
                        });
                    }
                }

                this.gestureRecognition.onGesture((gestureType, confidence) => {
                    this.handleDetectedGesture(gestureType, confidence);
                });
            }

            this.gestureRecognition.start();
            this.isRecognizing = true;
            this.updateUIForActiveState();

            if (typeof updateGlobalEnabled === 'function') updateGlobalEnabled(true);

            this.showToast('手势识别已启用！', 'success');
        } catch (error) {
            console.error('[Gesture] Start failed:', error);
            let msg = '启用手势识别失败';
            if (error.name === 'NotAllowedError') {
                msg = '摄像头权限被拒绝，请允许摄像头访问';
            } else if (error.name === 'NotFoundError') {
                msg = '未找到摄像头设备';
            } else if (error.message && error.message.includes('timeout')) {
                msg = '摄像头初始化超时';
            } else if (error.message) {
                msg = error.message;
            }
            this.showToast(msg, 'error');
            this.resetToInactiveState();
        }
    }

    stopGestureRecognition() {
        if (this.gestureRecognition) {
            this.gestureRecognition.stop();
        }
        this.isRecognizing = false;
        this.updateUIForInactiveState();
        if (typeof updateGlobalEnabled === 'function') updateGlobalEnabled(false);
        this.showToast('手势识别已停止', 'warning');
    }

    handleDetectedGesture(gestureType, confidence) {
        console.log(`[Gesture] Detected: ${gestureType} (${(confidence * 100).toFixed(1)}%)`);
        const config = (typeof getGestureConfig === 'function') ? getGestureConfig() : { gestures: {} };
        const gestureConfig = config.gestures ? config.gestures[gestureType] : null;
        if (gestureConfig && !gestureConfig.enabled) return;

        if (this.gestureActionHandler) {
            this.gestureActionHandler.executeAction(gestureType, confidence);
        }
    }

    updateUIForActiveState() {
        if (this.statusIndicator) {
            this.statusIndicator.style.background = '#44ff44';
            this.statusIndicator.style.boxShadow = '0 0 10px #44ff44';
        }
        this.toggleButton.style.animation = 'gesturePulse 2s infinite';
        this.toggleButton.style.boxShadow = '0 6px 25px rgba(68,255,68,0.5)';

        if (!document.getElementById('gesture-pulse-style')) {
            const style = document.createElement('style');
            style.id = 'gesture-pulse-style';
            style.textContent = `
                @keyframes gesturePulse {
                    0% { box-shadow:0 6px 25px rgba(68,255,68,0.5); }
                    50% { box-shadow:0 8px 30px rgba(68,255,68,0.7); }
                    100% { box-shadow:0 6px 25px rgba(68,255,68,0.5); }
                }
            `;
            document.head.appendChild(style);
        }
    }

    updateUIForInactiveState() {
        if (this.statusIndicator) {
            this.statusIndicator.style.background = '#ff4444';
            this.statusIndicator.style.boxShadow = '0 2px 6px rgba(0,0,0,0.2)';
        }
        this.toggleButton.style.animation = '';
        this.toggleButton.style.boxShadow = '0 4px 20px rgba(79,172,254,0.5)';
    }

    showLoadingState() {
        if (this.statusIndicator) {
            this.statusIndicator.style.background = '#ffaa00';
            this.statusIndicator.style.boxShadow = '0 0 10px #ffaa00';
        }
    }

    resetToInactiveState() {
        if (this.statusIndicator) {
            this.statusIndicator.style.animation = '';
        }
        this.updateUIForInactiveState();
    }

    loadSavedState() {
        const config = (typeof getGestureConfig === 'function') ? getGestureConfig() : { enabled: false };
        if (config.enabled) {
            console.log('[Gesture] Was previously enabled');
        }
    }

    showToast(message, type = 'info') {
        this.notificationTimeouts.forEach(t => clearTimeout(t));
        this.notificationTimeouts = [];

        let notification = document.getElementById('gesture-ui-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'gesture-ui-notification';
            notification.style.cssText = `
                position:fixed; bottom:90px; right:20px; padding:12px 22px; border-radius:10px;
                z-index:99999; font-size:13px; font-weight:500; max-width:300px; line-height:1.5;
                transition:all 0.3s cubic-bezier(0.4,0,0.2,1); opacity:0; transform:translateY(20px);
                box-shadow:0 4px 15px rgba(0,0,0,0.15); white-space:pre-line;
            `;
            document.body.appendChild(notification);
        }

        const colors = { success:'#4facfe', error:'#f44336', warning:'#ff9800', info:'#667eea' };
        notification.style.background = colors[type] || colors.info;
        notification.style.color = 'white';
        notification.textContent = message;

        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);

        const hideTimeout = setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
        }, 3500);
        this.notificationTimeouts.push(hideTimeout);
    }

    destroy() {
        if (this.gestureRecognition) {
            this.gestureRecognition.destroy();
            this.gestureRecognition = null;
        }
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        this.notificationTimeouts.forEach(t => clearTimeout(t));
        this.isInitialized = false;
        this.isRecognizing = false;
    }

    getStatus() {
        return {
            isInitialized: this.isInitialized,
            isRecognizing: this.isRecognizing,
            hasRecognitionInstance: !!this.gestureRecognition,
            recognitionStatus: this.gestureRecognition ? this.gestureRecognition.getStatus() : null
        };
    }
}

window.GestureUI = GestureUI;

if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const gestureUI = new GestureUI();
            gestureUI.init();
            window.gestureUI = gestureUI;
            console.log('[Gesture] System ready');
        });
    } else {
        const gestureUI = new GestureUI();
        gestureUI.init();
        window.gestureUI = gestureUI;
        console.log('[Gesture] System ready');
    }
}
