/**
 * 手势动作处理器
 * 处理各种手势触发的系统动作
 */

class GestureActionHandler {
    constructor() {
        this.recentFunctions = [];
        this.maxRecentFunctions = 3;
    }

    async executeAction(actionName) {
        console.log('执行手势动作:', actionName);
        
        switch (actionName) {
            case 'navigateBack':
                await this.navigateBack();
                break;
            case 'refreshCurrentPage':
                await this.refreshCurrentPage();
                break;
            case 'openQuickPanel':
                await this.openQuickPanel();
                break;
            case 'navigateToChat':
                await this.navigateToChat();
                break;
            case 'takeScreenshot':
                await this.takeScreenshot();
                break;
            default:
                console.warn('未知的手势动作:', actionName);
        }
        
        this.recordFunctionUsage(actionName);
    }

    async navigateBack() {
        this.showGestureToast('返回上一页');
        
        if (window.history.length > 1) {
            window.history.back();
        } else {
            this.showGestureToast('已是首页，无法返回');
        }
    }

    async refreshCurrentPage() {
        this.showGestureToast('刷新当前页面');
        
        const currentPath = window.location.pathname;
        
        if (currentPath.includes('/chat')) {
            if (typeof loadChatHistory === 'function') {
                await loadChatHistory();
            }
        } else if (currentPath.includes('/datav')) {
            if (typeof refreshDataVData === 'function') {
                await refreshDataVData();
            }
        } else {
            window.location.reload();
        }
    }

    async openQuickPanel() {
        this.showGestureToast('打开快捷工具面板');
        
        let panel = document.getElementById('gesture-quick-panel');
        
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'gesture-quick-panel';
            panel.style.cssText = `
                position: fixed;
                top: 0;
                right: -300px;
                width: 300px;
                height: 100vh;
                background: rgba(255, 255, 255, 0.95);
                box-shadow: -2px 0 10px rgba(0, 0, 0, 0.3);
                z-index: 9999;
                transition: right 0.3s ease;
                padding: 20px;
                overflow-y: auto;
            `;
            
            panel.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; color: #333;">快捷工具面板</h3>
                    <button onclick="document.getElementById('gesture-quick-panel').style.right = '-300px'" 
                            style="position: absolute; top: 10px; right: 10px; border: none; background: none; font-size: 20px; cursor: pointer;">×</button>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #666;">手势状态</h4>
                    <div id="gesture-status-indicator" style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
                        加载中...
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #666;">系统时间</h4>
                    <div id="gesture-system-time" style="padding: 10px; background: #f0f0f0; border-radius: 5px; font-family: monospace;">
                        --:--:--
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px 0; color: #666;">最近使用功能</h4>
                    <div id="gesture-recent-functions" style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
                        暂无记录
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <button onclick="window.gestureActionHandler.clearCache()" 
                            style="width: 100%; padding: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        清理缓存
                    </button>
                </div>
            `;
            
            document.body.appendChild(panel);
            
            setInterval(() => {
                const timeEl = document.getElementById('gesture-system-time');
                if (timeEl) {
                    const now = new Date();
                    timeEl.textContent = now.toLocaleString('zh-CN');
                }
            }, 1000);
        }
        
        setTimeout(() => {
            panel.style.right = '0px';
        }, 10);
        
        this.updateQuickPanelContent();
    }

    updateQuickPanelContent() {
        const statusEl = document.getElementById('gesture-status-indicator');
        if (statusEl) {
            const config = getGestureConfig();
            statusEl.innerHTML = `
                <div>手势识别: ${config.enabled ? '<span style="color: green;">已启用</span>' : '<span style="color: red;">已禁用</span>'}</div>
                <div style="margin-top: 5px; font-size: 12px; color: #666;">
                    已启用 ${Object.values(config.gestures).filter(g => g.enabled).length} 个手势
                </div>
            `;
        }
        
        const recentEl = document.getElementById('gesture-recent-functions');
        if (recentEl) {
            if (this.recentFunctions.length > 0) {
                recentEl.innerHTML = this.recentFunctions.map(f => 
                    `<div style="margin-bottom: 5px;">• ${this.getActionDisplayName(f)}</div>`
                ).join('');
            } else {
                recentEl.textContent = '暂无记录';
            }
        }
    }

    async navigateToChat() {
        this.showGestureToast('跳转到智能问数');
        window.location.href = '/chat';
    }

    async takeScreenshot() {
        this.showGestureToast('正在截图...');
        
        try {
            const canvas = await html2canvas(document.body, {
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#ffffff'
            });
            
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `cnAgentOS-screenshot-${timestamp}.png`;
            
            const link = document.createElement('a');
            link.download = filename;
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            this.showGestureToast('截图已保存');
        } catch (error) {
            console.error('截图失败:', error);
            this.showGestureToast('截图失败，请确保已加载html2canvas库');
        }
    }

    clearCache() {
        const keysToKeep = ['gesture_config', 'username'];
        const allKeys = Object.keys(localStorage);
        
        allKeys.forEach(key => {
            if (!keysToKeep.includes(key)) {
                localStorage.removeItem(key);
            }
        });
        
        this.showGestureToast('缓存已清理');
        
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    recordFunctionUsage(actionName) {
        if (this.recentFunctions.includes(actionName)) {
            this.recentFunctions = this.recentFunctions.filter(f => f !== actionName);
        }
        
        this.recentFunctions.unshift(actionName);
        
        if (this.recentFunctions.length > this.maxRecentFunctions) {
            this.recentFunctions.pop();
        }
    }

    getActionDisplayName(actionName) {
        const names = {
            navigateBack: '返回上一页',
            refreshCurrentPage: '刷新页面',
            openQuickPanel: '快捷工具',
            navigateToChat: '智能问数',
            takeScreenshot: '截图'
        };
        return names[actionName] || actionName;
    }

    showGestureToast(message) {
        let toast = document.getElementById('gesture-toast');
        
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'gesture-toast';
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 10000;
                font-size: 14px;
                transition: opacity 0.3s;
            `;
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        toast.style.opacity = '1';
        
        setTimeout(() => {
            toast.style.opacity = '0';
        }, 2000);
    }
}

window.GestureActionHandler = GestureActionHandler;
window.gestureActionHandler = new GestureActionHandler();
