/**
 * 手势识别核心引擎 - MediaPipe Hands 版本
 * 基于 Google MediaPipe Hands 进行手部关键点检测
 * 支持手势：上划、下划、张开手掌、竖起大拇指、握拳
 */

class GestureRecognitionMediaPipe {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isActive = false;
        this.stream = null;
        this.animationId = null;
        
        // MediaPipe 相关
        this.hands = null;
        this.results = null;
        
        // 手势检测状态
        this.currentGesture = null;
        this.gestureStartTime = 0;
        this.gestureHoldTime = 500;
        this.onGestureCallback = null;
        
        // 手部追踪
        this.handPositionHistory = [];
        this.maxHistoryLength = 15;
        
        // 配置参数
        this.config = {
            swipeThreshold: 50,
            holdTime: 500,
            detectionInterval: 100
        };
        
        this.lastDetectionTime = 0;
        this.isProcessing = false;
    }

    /**
     * 初始化 MediaPipe Hands
     */
    async init() {
        try {
            console.log('🎥 正在初始化 MediaPipe 手势识别系统...');
            
            // 加载 MediaPipe Hands
            const { Hands, RESULTS } = await import('https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/hands.js');
            
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`;
                }
            });
            
            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });
            
            this.hands.onResults((results) => {
                this.results = results;
            });
            
            // 创建视频元素（显示在页面上）
            this.video = document.createElement('video');
            this.video.setAttribute('playsinline', '');
            this.video.setAttribute('autoplay', '');
            this.video.muted = true;
            this.video.style.cssText = `
                position:fixed;
                bottom: 100px;
                right: 20px;
                width: 240px;
                height: 180px;
                border-radius: 12px;
                border: 3px solid rgba(102, 126, 234, 0.6);
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                z-index: 9997;
                background: #1a1a2e;
                transform: scaleX(-1);
                display: none;
            `;
            this.video.id = 'gesture-camera-feed';
            document.body.appendChild(this.video);

            // 创建Canvas元素（显示关键点）
            this.canvas = document.createElement('canvas');
            this.canvas.width = 320;
            this.canvas.height = 240;
            this.canvas.style.cssText = `
                position:fixed;
                bottom: 300px;
                right: 20px;
                width: 240px;
                height: 180px;
                border-radius: 12px;
                border: 3px solid rgba(68, 255, 68, 0.6);
                box-shadow: 0 4px 20px rgba(68, 255, 68, 0.3);
                z-index: 9996;
                background: #1a1a2e;
                display: none;
            `;
            this.canvas.id = 'gesture-processed-feed';
            document.body.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');

            // 请求摄像头权限
            console.log('📷 正在请求摄像头权限...');
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'user',
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                    frameRate: { ideal: 30 }
                }
            });
            
            this.stream = stream;
            this.video.srcObject = stream;
            
            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    console.log('✅ MediaPipe 手势识别初始化完成');
                    resolve(true);
                };
            });
            
        } catch (error) {
            console.error('❌ MediaPipe 初始化失败:', error);
            throw error;
        }
    }

    /**
     * 启动手势识别
     */
    start() {
        if (this.isActive) {
            console.log('⚠️ 手势识别已在运行中');
            return;
        }
        
        this.isActive = true;
        
        // 显示摄像头画面
        if (this.video) {
            this.video.style.display = 'block';
        }
        if (this.canvas) {
            this.canvas.style.display = 'block';
        }
        
        this.detectLoop();
        console.log('▶️ MediaPipe 手势识别已启动');
    }

    /**
     * 停止手势识别
     */
    stop() {
        this.isActive = false;
        
        // 隐藏摄像头画面
        if (this.video) {
            this.video.style.display = 'none';
        }
        if (this.canvas) {
            this.canvas.style.display = 'none';
        }
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        console.log('⏹️ MediaPipe 手势识别已停止');
    }

    /**
     * 完全释放资源
     */
    destroy() {
        this.stop();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.video && this.video.parentNode) {
            this.video.parentNode.removeChild(this.video);
            this.video = null;
        }
        
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
            this.canvas = null;
        }
        
        if (this.hands) {
            this.hands.close();
            this.hands = null;
        }
        
        this.isActive = false;
        console.log('🗑️ MediaPipe 手势识别资源已释放');
    }

    /**
     * 主检测循环
     */
    async detectLoop() {
        if (!this.isActive) return;

        const now = Date.now();
        
        if (now - this.lastDetectionTime >= this.config.detectionInterval && !this.isProcessing) {
            this.lastDetectionTime = now;
            await this.performDetection();
        }

        this.animationId = requestAnimationFrame(() => this.detectLoop());
    }

    /**
     * 执行一次完整的检测流程
     */
    async performDetection() {
        if (this.isProcessing || !this.video || !this.ctx) return;
        
        this.isProcessing = true;
        
        try {
            // 处理视频帧
            if (this.results && this.results.multiHandLandmarks) {
                const handLandmarks = this.results.multiHandLandmarks[0];
                const handedness = this.results.multiHandedness[0];
                
                if (handLandmarks) {
                    // 绘制关键点
                    this.drawLandmarks(handLandmarks);
                    
                    // 分析手势
                    const gesture = this.analyzeGesture(handLandmarks, handedness);
                    
                    if (gesture) {
                        this.processGesture(gesture);
                    } else {
                        this.resetGesture();
                    }
                }
            }
            
            // 处理下一帧
            if (this.hands && this.video && this.isActive) {
                await this.hands.send({ image: this.video });
            }
            
        } catch (error) {
            console.error('检测过程出错:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * 绘制手部关键点
     */
    drawLandmarks(landmarks) {
        if (!this.ctx || !landmarks) return;
        
        const canvas = this.canvas;
        const ctx = this.ctx;
        
        // 清除画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 镜像翻转
        ctx.save();
        ctx.scale(-1, 1);
        ctx.translate(-canvas.width, 0);
        
        // 绘制手掌连接
        const connections = [
            [0, 1], [1, 2], [2, 3], [3, 4],  // 拇指
            [0, 5], [5, 6], [6, 7], [7, 8],  // 食指
            [0, 9], [9, 10], [10, 11], [11, 12],  // 中指
            [0, 13], [13, 14], [14, 15], [15, 16],  // 无名指
            [0, 17], [17, 18], [18, 19], [19, 20]   // 小指
        ];
        
        // 绘制连接线
        ctx.strokeStyle = '#44ff44';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        connections.forEach(([start, end]) => {
            const startPoint = landmarks[start];
            const endPoint = landmarks[end];
            
            ctx.moveTo(startPoint.x * canvas.width, startPoint.y * canvas.height);
            ctx.lineTo(endPoint.x * canvas.width, endPoint.y * canvas.height);
        });
        
        ctx.stroke();
        
        // 绘制关键点
        landmarks.forEach((landmark, index) => {
            const x = landmark.x * canvas.width;
            const y = landmark.y * canvas.height;
            
            ctx.beginPath();
            ctx.arc(x, y, index === 0 ? 6 : 4, 0, Math.PI * 2);
            ctx.fillStyle = index === 0 ? '#ff4444' : '#ffffff';
            ctx.fill();
            ctx.strokeStyle = '#44ff44';
            ctx.lineWidth = 2;
            ctx.stroke();
        });
        
        ctx.restore();
    }

    /**
     * 判断手指是否伸直
     */
    isFingerExtended(landmarks, fingerIndex) {
        // fingerIndex: 0=拇指, 1=食指, 2=中指, 3=无名指, 4=小指
        const baseIndex = fingerIndex * 4;
        const mcp = landmarks[baseIndex + 1];  // 掌指关节
        const pip = landmarks[baseIndex + 2];  // 近端指间关节
        const dip = landmarks[baseIndex + 3];  // 远端指间关节
        const tip = landmarks[baseIndex + 4];  // 指尖
        
        // 计算指尖到掌指关节的距离
        const tipToMcp = Math.sqrt(
            Math.pow(tip.x - mcp.x, 2) + 
            Math.pow(tip.y - mcp.y, 2)
        );
        
        // 计算指关节之间的距离
        const pipToMcp = Math.sqrt(
            Math.pow(pip.x - mcp.x, 2) + 
            Math.pow(pip.y - mcp.y, 2)
        );
        
        const dipToPip = Math.sqrt(
            Math.pow(dip.x - pip.x, 2) + 
            Math.pow(dip.y - pip.y, 2)
        );
        
        // 计算掌宽（用于归一化）
        const palmWidth = Math.sqrt(
            Math.pow(landmarks[5].x - landmarks[17].x, 2) +
            Math.pow(landmarks[5].y - landmarks[17].y, 2)
        );
        
        // 手指伸直的判断：指尖到掌指关节的距离应该大于指关节长度之和
        const isExtended = tipToMcp > (pipToMcp + dipToPip) * 0.85;
        
        return isExtended;
    }

    /**
     * 判断是否为竖起大拇指
     */
    isThumbsUp(landmarks, handedness) {
        // 大拇指伸直，其他四指弯曲
        const thumbExtended = this.isFingerExtended(landmarks, 0);
        
        // 检查其他四指是否弯曲
        let otherFingersBent = true;
        for (let i = 1; i <= 4; i++) {
            if (this.isFingerExtended(landmarks, i)) {
                otherFingersBent = false;
                break;
            }
        }
        
        // 大拇指方向检测（应该向上）
        const thumbTip = landmarks[4];
        const thumbMcp = landmarks[1];
        const palmCenter = landmarks[0];
        
        // 大拇指应该高于手掌中心
        const thumbUp = thumbTip.y < palmCenter.y * 0.9;
        
        return thumbExtended && otherFingersBent && thumbUp;
    }

    /**
     * 判断是否为握拳
     */
    isFist(landmarks) {
        // 所有手指都弯曲
        let allFingersBent = true;
        for (let i = 0; i <= 4; i++) {
            if (this.isFingerExtended(landmarks, i)) {
                allFingersBent = false;
                break;
            }
        }
        
        return allFingersBent;
    }

    /**
     * 判断是否为张开手掌
     */
    isOpenPalm(landmarks) {
        // 所有手指都伸直
        let allFingersExtended = true;
        for (let i = 0; i <= 4; i++) {
            if (!this.isFingerExtended(landmarks, i)) {
                allFingersExtended = false;
                break;
            }
        }
        
        return allFingersExtended;
    }

    /**
     * 检测滑动手势
     */
    detectSwipeGesture(landmarks) {
        if (this.handPositionHistory.length < 8) return null;
        
        // 获取手掌中心位置
        const palmCenter = landmarks[0];
        const currentX = palmCenter.x;
        const currentY = palmCenter.y;
        
        // 更新位置历史
        this.handPositionHistory.push({
            x: currentX,
            y: currentY,
            time: Date.now()
        });
        
        // 保持历史长度
        while (this.handPositionHistory.length > this.maxHistoryLength) {
            this.handPositionHistory.shift();
        }
        
        // 取最近的位置点
        const recentPositions = this.handPositionHistory.slice(-8);
        const firstPos = recentPositions[0];
        const lastPos = recentPositions[recentPositions.length - 1];
        
        // 计算位移（相对于视频尺寸）
        const deltaX = (lastPos.x - firstPos.x) * this.video.videoWidth;
        const deltaY = (lastPos.y - firstPos.y) * this.video.videoHeight;
        const deltaTime = lastPos.time - firstPos.time;
        
        // 时间窗口检查
        if (deltaTime > 500 || deltaTime < 50) return null;
        
        // 计算速度
        const speed = Math.sqrt(deltaX * deltaX + deltaY * deltaY) / deltaTime;
        
        // 必须是垂直方向的主导运动
        if (Math.abs(deltaY) < this.config.swipeThreshold) return null;
        if (Math.abs(deltaX) > Math.abs(deltaY)) return null;
        
        // 速度必须足够快
        if (speed < 0.25) return null;
        
        // 判断方向
        if (deltaY < -this.config.swipeThreshold) {
            return { type: 'swipe_up', confidence: 0.9 };
        } else if (deltaY > this.config.swipeThreshold) {
            return { type: 'swipe_down', confidence: 0.9 };
        }
        
        return null;
    }

    /**
     * 分析手势类型
     */
    analyzeGesture(landmarks, handedness) {
        // 优先检测滑动动作
        const swipeGesture = this.detectSwipeGesture(landmarks);
        if (swipeGesture) {
            console.log(`👆 检测到滑动手势: ${swipeGesture.type}, 置信度: ${swipeGesture.confidence}`);
            return swipeGesture;
        }
        
        // 检测静态手势
        if (this.isThumbsUp(landmarks, handedness)) {
            console.log('✋ 检测到手势: thumbs_up, 置信度: 0.92');
            return { type: 'thumbs_up', confidence: 0.92 };
        }
        
        if (this.isFist(landmarks)) {
            console.log('✋ 检测到手势: fist, 置信度: 0.9');
            return { type: 'fist', confidence: 0.9 };
        }
        
        if (this.isOpenPalm(landmarks)) {
            console.log('✋ 检测到手势: open_palm, 置信度: 0.91');
            return { type: 'open_palm', confidence: 0.91 };
        }
        
        return null;
    }

    /**
     * 处理检测到的手势
     */
    processGesture(gesture) {
        const now = Date.now();
        
        if (this.currentGesture && this.currentGesture.type === gesture.type) {
            const heldDuration = now - this.gestureStartTime;
            
            if (heldDuration >= this.gestureHoldTime) {
                if (this.onGestureCallback) {
                    this.onGestureCallback(gesture.type, gesture.confidence);
                }
                
                this.resetGesture();
            }
        } else {
            this.currentGesture = gesture;
            this.gestureStartTime = now;
        }
    }

    /**
     * 重置手势状态
     */
    resetGesture() {
        this.currentGesture = null;
        this.gestureStartTime = 0;
    }

    /**
     * 设置手势检测回调函数
     */
    onGesture(callback) {
        this.onGestureCallback = callback;
    }

    /**
     * 更新配置参数
     */
    setConfig(config) {
        Object.assign(this.config, config);
        if (config.holdTime) {
            this.gestureHoldTime = config.holdTime;
        }
    }

    /**
     * 获取当前状态
     */
    getStatus() {
        return {
            isActive: this.isActive,
            hasResults: !!this.results,
            currentGesture: this.currentGesture
        };
    }
}

// 导出到全局
window.GestureRecognitionMediaPipe = GestureRecognitionMediaPipe;
