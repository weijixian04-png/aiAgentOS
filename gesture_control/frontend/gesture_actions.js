class GestureActionHandler {
    constructor() {
        this.recentActions = [];
        this.maxRecentActions = 5;
        this.isSpeaking = false;
        this.speechSynth = window.speechSynthesis || null;
        this.notificationPanel = null;
        this.isPanelOpen = false;
        this.html2canvasLoaded = false;

        this.actionNames = {
            'thumbs_up': '全局返回',
            'open_palm': '刷新数据',
            'victory': '消息通知中心',
            'pointing': '全屏截图',
            'call_me': '语音朗读切换'
        };

        this.actionIcons = {
            'thumbs_up': '\u{1F44D}',
            'open_palm': '\u{1F590}',
            'victory': '\u270C',
            'pointing': '\u261D',
            'call_me': '\u{1F919}'
        };
    }

    async executeAction(gestureType, confidence) {
        console.log(`[Gesture] Execute: ${gestureType} (${(confidence * 100).toFixed(1)}%)`);
        this.showGestureIndicator(gestureType);
        this.recordRecentAction(gestureType);

        try {
            switch (gestureType) {
                case 'thumbs_up':
                    await this.goBack();
                    break;
                case 'open_palm':
                    await this.refreshPage();
                    break;
                case 'victory':
                    await this.openNotificationCenter();
                    break;
                case 'pointing':
                    await this.takeScreenshot();
                    break;
                case 'call_me':
                    await this.toggleVoiceReading();
                    break;
                default:
                    console.warn(`[Gesture] Unknown gesture: ${gestureType}`);
            }
        } catch (error) {
            console.error('[Gesture] Action failed:', error);
            this.showToast('操作失败: ' + error.message, 'error');
        }
    }

    async goBack() {
        console.log('[Gesture] Go back');
        this.showToast('正在返回...', 'info');

        const modal = document.querySelector('.modal.show') ||
                      document.querySelector('.layui-layer') ||
                      document.querySelector('[class*="modal"][class*="show"]') ||
                      document.querySelector('[class*="dialog"][style*="display: block"]');

        if (modal) {
            const closeBtn = modal.querySelector('.btn-close') ||
                            modal.querySelector('.close') ||
                            modal.querySelector('[data-dismiss="modal"]') ||
                            modal.querySelector('.layui-layer-close');
            if (closeBtn) {
                closeBtn.click();
                this.showToast('已关闭弹窗', 'success');
                return true;
            }
        }

        if (window.history.length > 1) {
            const canGoBack = window.history.length > 1 &&
                              document.referrer &&
                              new URL(document.referrer).origin === window.location.origin;
            if (canGoBack) {
                window.history.back();
                this.showToast('已返回上一页', 'success');
            } else {
                this.showToast('已在最顶层页面，无法继续返回', 'warning');
            }
        } else {
            this.showToast('已在最顶层页面，无法继续返回', 'warning');
        }
        return true;
    }

    async refreshPage() {
        console.log('[Gesture] Refresh page data');
        this.showToast('正在刷新数据...', 'info');

        const refreshBtn = document.querySelector('[onclick*="refresh"]') ||
                          document.querySelector('[onclick*="reload"]') ||
                          document.querySelector('.layui-btn[onclick*="reload"]') ||
                          document.querySelector('[class*="refresh"]') ||
                          document.querySelector('#refreshBtn');

        if (refreshBtn) {
            refreshBtn.click();
            this.showToast('数据已刷新', 'success');
            return true;
        }

        if (typeof layui !== 'undefined' && layui.table) {
            try {
                layui.table.reload('currentTableId');
                this.showToast('表格数据已刷新', 'success');
                return true;
            } catch (e) {
                const tables = document.querySelectorAll('.layui-table');
                if (tables.length > 0) {
                    const tableId = tables[0].id || tables[0].closest('[lay-filter]')?.getAttribute('lay-filter');
                    if (tableId) {
                        layui.table.reload(tableId);
                        this.showToast('表格数据已刷新', 'success');
                        return true;
                    }
                }
            }
        }

        window.location.reload();
        return true;
    }

    async openNotificationCenter() {
        console.log('[Gesture] Open notification center');

        if (this.isPanelOpen && this.notificationPanel) {
            this.closeNotificationCenter();
            return true;
        }

        if (!this.notificationPanel) {
            this.createNotificationCenter();
        }

        this.notificationPanel.style.right = '0';
        this.isPanelOpen = true;
        this.updateNotificationContent();
        this.showToast('通知中心已打开', 'info');
        return true;
    }

    createNotificationCenter() {
        this.notificationPanel = document.createElement('div');
        this.notificationPanel.id = 'gesture-notification-center';
        this.notificationPanel.style.cssText = `
            position:fixed; top:0; right:-360px; width:360px; height:100vh;
            background:linear-gradient(180deg,#ffffff 0%,#f8f9fa 100%);
            box-shadow:-4px 0 25px rgba(0,0,0,0.15); z-index:99999;
            transition:right 0.35s cubic-bezier(0.4,0,0.2,1);
            overflow-y:auto; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
        `;

        this.notificationPanel.innerHTML = `
            <div style="padding:20px; background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%); color:white;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; font-size:18px;">&#x1F514; 通知中心</h3>
                    <button id="gesture-close-notif" style="background:none; border:none; color:white; font-size:24px; cursor:pointer; padding:0; line-height:1;">&times;</button>
                </div>
                <p style="margin:8px 0 0 0; font-size:13px; opacity:0.9;">手势控制通知</p>
            </div>
            <div style="padding:20px;">
                <div style="background:white; border-radius:10px; padding:15px; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 10px 0; color:#333; font-size:14px;">&#x1F4CA; 系统状态</h4>
                    <div id="notif-system-status" style="font-size:13px; color:#666; line-height:1.8;">加载中...</div>
                </div>
                <div style="background:white; border-radius:10px; padding:15px; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 10px 0; color:#333; font-size:14px;">&#x1F552; 当前时间</h4>
                    <div id="notif-current-time" style="font-family:monospace; font-size:22px; color:#4facfe; text-align:center; letter-spacing:2px;">--:--:--</div>
                    <div id="notif-current-date" style="text-align:center; font-size:12px; color:#999; margin-top:5px;">----</div>
                </div>
                <div style="background:white; border-radius:10px; padding:15px; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 10px 0; color:#333; font-size:14px;">&#x1F4CB; 最近手势</h4>
                    <div id="notif-recent-actions" style="font-size:13px; color:#666;">暂无记录</div>
                </div>
                <div style="background:white; border-radius:10px; padding:15px; margin-bottom:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 10px 0; color:#333; font-size:14px;">&#x1F4A1; 快捷操作</h4>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                        <button id="notif-btn-back" style="padding:10px; border:1px solid #e0e0e0; border-radius:8px; background:white; cursor:pointer; font-size:12px; transition:all 0.2s;">
                            &#x1F448; 返回
                        </button>
                        <button id="notif-btn-voice" style="padding:10px; border:1px solid #e0e0e0; border-radius:8px; background:white; cursor:pointer; font-size:12px; transition:all 0.2s;">
                            &#x1F50A; 语音朗读
                        </button>
                        <button id="notif-btn-refresh" style="padding:10px; border:1px solid #e0e0e0; border-radius:8px; background:white; cursor:pointer; font-size:12px; transition:all 0.2s;">
                            &#x1F504; 刷新
                        </button>
                        <button id="notif-btn-config" style="padding:10px; border:1px solid #e0e0e0; border-radius:8px; background:white; cursor:pointer; font-size:12px; transition:all 0.2s;">
                            &#x2699; 设置
                        </button>
                    </div>
                </div>
                <div style="background:white; border-radius:10px; padding:15px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 10px 0; color:#333; font-size:14px;">&#x1F4D6; 手势指南</h4>
                    <div style="font-size:12px; color:#666; line-height:2;">
                        <div>&#x1F44D; 点赞 &rarr; 全局返回</div>
                        <div>&#x1F590; 张开手掌 &rarr; 刷新数据</div>
                        <div>&#x270C; 胜利手势 &rarr; 通知中心</div>
                        <div>&#x261D; 食指指向 &rarr; 全屏截图</div>
                        <div>&#x1F919; 打电话 &rarr; 语音切换</div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(this.notificationPanel);

        document.getElementById('gesture-close-notif').addEventListener('click', () => {
            this.closeNotificationCenter();
        });
        document.getElementById('notif-btn-back').addEventListener('click', () => {
            this.goBack();
        });
        document.getElementById('notif-btn-voice').addEventListener('click', () => {
            this.toggleVoiceReading();
        });
        document.getElementById('notif-btn-refresh').addEventListener('click', () => {
            this.refreshPage();
        });
        document.getElementById('notif-btn-config').addEventListener('click', () => {
            window.location.href = '/admin/gesture';
        });

        this.startClockUpdate();
    }

    closeNotificationCenter() {
        if (this.notificationPanel) {
            this.notificationPanel.style.right = '-360px';
        }
        this.isPanelOpen = false;
    }

    updateNotificationContent() {
        const statusEl = document.getElementById('notif-system-status');
        if (statusEl) {
            const config = (typeof getGestureConfig === 'function') ? getGestureConfig() : { enabled: false };
            statusEl.innerHTML = `
                <div>手势: ${config.enabled ? '<span style="color:#4CAF50;font-weight:bold;">运行中</span>' : '<span style="color:#f44336;">已停止</span>'}</div>
                <div>页面: <span style="color:#4facfe;">${window.location.pathname}</span></div>
                <div>屏幕: <span>${window.innerWidth} x ${window.innerHeight}</span></div>
                <div>语音: <span style="color:${this.isSpeaking ? '#4CAF50' : '#999'};">${this.isSpeaking ? '开启' : '关闭'}</span></div>
            `;
        }

        const recentEl = document.getElementById('notif-recent-actions');
        if (recentEl) {
            if (this.recentActions.length > 0) {
                recentEl.innerHTML = this.recentActions.map((action, i) =>
                    `<div style="padding:5px 0; border-bottom:1px solid #f0f0f0; display:flex; align-items:center;">
                        <span style="color:#4facfe; font-weight:bold; margin-right:8px;">${i + 1}.</span>
                        <span>${this.actionIcons[action] || ''} ${this.actionNames[action] || action}</span>
                    </div>`
                ).join('');
            } else {
                recentEl.innerHTML = '<span style="color:#999;">暂无手势记录</span>';
            }
        }
    }

    startClockUpdate() {
        setInterval(() => {
            const timeEl = document.getElementById('notif-current-time');
            const dateEl = document.getElementById('notif-current-date');
            if (timeEl && dateEl) {
                const now = new Date();
                timeEl.textContent = now.toLocaleTimeString('zh-CN', { hour12: false });
                dateEl.textContent = now.toLocaleDateString('zh-CN', {
                    year:'numeric', month:'long', day:'numeric', weekday:'long'
                });
            }
        }, 1000);
    }

    async takeScreenshot() {
        console.log('[Gesture] Take screenshot');
        this.showToast('正在截图...', 'info');

        if (typeof html2canvas === 'undefined' && !this.html2canvasLoaded) {
            await this.loadHtml2Canvas();
        }

        if (typeof html2canvas === 'undefined') {
            this.showToast('截图库加载失败，请刷新页面重试', 'error');
            return false;
        }

        try {
            const canvas = await html2canvas(document.body, {
                useCORS: true,
                allowTaint: true,
                scale: window.devicePixelRatio || 1,
                backgroundColor: '#ffffff',
                logging: false
            });

            const now = new Date();
            const timestamp = now.getFullYear().toString() +
                String(now.getMonth() + 1).padStart(2, '0') +
                String(now.getDate()).padStart(2, '0') + '_' +
                String(now.getHours()).padStart(2, '0') +
                String(now.getMinutes()).padStart(2, '0') +
                String(now.getSeconds()).padStart(2, '0');

            const link = document.createElement('a');
            link.download = `screenshot_${timestamp}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();

            this.showToast('截图已保存到本地', 'success');
        } catch (error) {
            console.error('[Gesture] Screenshot failed:', error);
            this.showToast('截图失败: ' + error.message, 'error');
        }
        return true;
    }

    async loadHtml2Canvas() {
        return new Promise((resolve) => {
            if (typeof html2canvas !== 'undefined') {
                this.html2canvasLoaded = true;
                resolve();
                return;
            }
            const script = document.createElement('script');
            script.src = '/static/dist/html2canvas/html2canvas.min.js';
            script.onload = () => {
                this.html2canvasLoaded = true;
                resolve();
            };
            script.onerror = () => {
                console.error('[Gesture] Failed to load html2canvas');
                resolve();
            };
            document.head.appendChild(script);
        });
    }

    async toggleVoiceReading() {
        console.log('[Gesture] Toggle voice reading');

        if (!this.speechSynth) {
            this.showToast('浏览器不支持语音合成', 'error');
            return false;
        }

        if (this.isSpeaking) {
            this.speechSynth.cancel();
            this.isSpeaking = false;
            this.showToast('语音朗读已停止', 'warning');
            return true;
        }

        const mainContent = document.querySelector('.layui-body') ||
                           document.querySelector('main') ||
                           document.querySelector('.main-content') ||
                           document.querySelector('#content') ||
                           document.body;

        const textElements = mainContent.querySelectorAll('h1,h2,h3,h4,p,li,td,th,span,a');
        let textContent = '';
        textElements.forEach(el => {
            const t = el.textContent.trim();
            if (t && t.length > 2 && t.length < 500) {
                textContent += t + '. ';
            }
        });

        if (!textContent || textContent.trim().length < 5) {
            textContent = 'Current page has no readable content.';
        }

        if (textContent.length > 1000) {
            textContent = textContent.substring(0, 1000) + '... Content truncated.';
        }

        const utterance = new SpeechSynthesisUtterance(textContent);
        utterance.lang = 'zh-CN';
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onend = () => {
            this.isSpeaking = false;
            this.showToast('语音朗读完成', 'info');
        };
        utterance.onerror = () => {
            this.isSpeaking = false;
        };

        this.speechSynth.speak(utterance);
        this.isSpeaking = true;
        this.showToast('语音朗读已开始', 'success');
        return true;
    }

    recordRecentAction(actionName) {
        this.recentActions = this.recentActions.filter(a => a !== actionName);
        this.recentActions.unshift(actionName);
        if (this.recentActions.length > this.maxRecentActions) {
            this.recentActions.pop();
        }
        if (this.isPanelOpen) {
            this.updateNotificationContent();
        }
    }

    showGestureIndicator(gestureType) {
        const name = this.actionNames[gestureType] || gestureType;
        const icon = this.actionIcons[gestureType] || '\u270B';

        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position:fixed; top:50%; left:50%; transform:translate(-50%,-50%) scale(0.8);
            background:linear-gradient(135deg,rgba(79,172,254,0.95) 0%,rgba(0,242,254,0.95) 100%);
            color:white; padding:25px 50px; border-radius:15px; font-size:22px; font-weight:bold;
            z-index:100000; opacity:0; animation:gesturePopup 1.5s ease-out forwards;
            box-shadow:0 10px 40px rgba(79,172,254,0.4); backdrop-filter:blur(10px);
            text-align:center; min-width:200px;
        `;
        indicator.innerHTML = `<div style="font-size:48px; margin-bottom:10px;">${icon}</div><div>${name}</div>`;

        if (!document.getElementById('gesture-popup-anim')) {
            const style = document.createElement('style');
            style.id = 'gesture-popup-anim';
            style.textContent = `
                @keyframes gesturePopup {
                    0% { opacity:0; transform:translate(-50%,-50%) scale(0.8); }
                    20% { opacity:1; transform:translate(-50%,-50%) scale(1.05); }
                    30% { transform:translate(-50%,-50%) scale(1); }
                    80% { opacity:1; transform:translate(-50%,-50%) scale(1); }
                    100% { opacity:0; transform:translate(-50%,-50%) scale(0.95); }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(indicator);
        setTimeout(() => indicator.remove(), 1600);
    }

    showToast(message, type = 'info') {
        let toast = document.getElementById('gesture-action-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'gesture-action-toast';
            toast.style.cssText = `
                position:fixed; top:80px; left:50%; transform:translateX(-50%);
                padding:12px 28px; border-radius:25px; z-index:100001; font-size:14px;
                font-weight:500; transition:all 0.3s ease; max-width:400px; text-align:center;
                box-shadow:0 4px 15px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(toast);
        }

        const colors = { success:'#4facfe', error:'#f44336', warning:'#ff9800', info:'#667eea' };
        toast.style.background = colors[type] || colors.info;
        toast.style.color = 'white';
        toast.textContent = message;
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(-50%) translateY(0)';

        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(-50%) translateY(-20px)';
        }, 2500);
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

window.GestureActionHandler = GestureActionHandler;
