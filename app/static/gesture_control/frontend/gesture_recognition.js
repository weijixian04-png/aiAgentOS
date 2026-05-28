/**
 * 手势识别核心模块
 * 基于摄像头视频流的手势识别系统
 * 支持手势：上划、下划、张开手掌、竖起大拇指、握拳
 */

class GestureRecognition {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isActive = false;
        this.stream = null;
        this.lastGesture = null;
        this.gestureStartTime = 0;
        this.gestureHoldTime = 500;
        this.onGestureCallback = null;
        this.handTracker = null;
        this.lastPosition = null;
        this.positionHistory = [];
        this.historyMaxLength = 10;
        this.sensitivity = {
            swipeThreshold: 50,
            holdTime: 500,
            fingerThreshold: 30
        };
    }

    async init() {
        try {
            this.video = document.createElement('video');
            this.video.setAttribute('playsinline', '');
            this.video.setAttribute('autoplay', '');
            this.video.style.display = 'none';
            document.body.appendChild(this.video);

            this.canvas = document.createElement('canvas');
            this.canvas.style.display = 'none';
            document.body.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');

            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: 640, height: 480 }
            });
            this.stream = stream;
            this.video.srcObject = stream;
            
            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    resolve(true);
                };
            });
        } catch (error) {
            console.error('手势识别初始化失败:', error);
            throw error;
        }
    }

    start() {
        if (!this.isActive) {
            this.isActive = true;
            this.detectLoop();
            console.log('手势识别已启动');
        }
    }

    stop() {
        this.isActive = false;
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        console.log('手势识别已停止');
    }

    detectLoop() {
        if (!this.isActive) return;

        this.ctx.drawImage(this.video, 0, 0);
        const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        const gesture = this.detectGesture(imageData);
        if (gesture && gesture !== this.lastGesture) {
            this.lastGesture = gesture;
            this.gestureStartTime = Date.now();
        } else if (gesture && gesture === this.lastGesture) {
            if (Date.now() - this.gestureStartTime >= this.gestureHoldTime) {
                if (this.onGestureCallback) {
                    this.onGestureCallback(gesture);
                }
                this.lastGesture = null;
            }
        } else {
            this.lastGesture = null;
        }

        requestAnimationFrame(() => this.detectLoop());
    }

    detectGesture(imageData) {
        const skinPixels = this.detectSkinColor(imageData);
        const handRegion = this.findHandRegion(skinPixels);
        
        if (!handRegion) return null;

        const gesture = this.analyzeHandGesture(handRegion, imageData);
        return gesture;
    }

    detectSkinColor(imageData) {
        const pixels = [];
        const data = imageData.data;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            if (this.isSkinColor(r, g, b)) {
                const pixelIndex = i / 4;
                const x = pixelIndex % imageData.width;
                const y = Math.floor(pixelIndex / imageData.width);
                pixels.push({ x, y, r, g, b });
            }
        }
        
        return pixels;
    }

    isSkinColor(r, g, b) {
        const lower1 = [0, 20, 60];
        const upper1 = [20, 255, 255];
        
        const lower2 = [0, 40, 90];
        const upper2 = [20, 255, 255];
        
        return (
            (r > 95 && g > 40 && b > 20 &&
             r > g && r > b &&
             Math.abs(r - g) > 15 &&
             r - g > 15 && r - b > 15) ||
            (r > 220 && g > 210 && b > 170 &&
             Math.abs(r - g) <= 15 &&
             r > b && g > b)
        );
    }

    findHandRegion(skinPixels) {
        if (skinPixels.length < 100) return null;

        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        skinPixels.forEach(pixel => {
            minX = Math.min(minX, pixel.x);
            minY = Math.min(minY, pixel.y);
            maxX = Math.max(maxX, pixel.x);
            maxY = Math.max(maxY, pixel.y);
        });

        return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            centerX: (minX + maxX) / 2,
            centerY: (minY + maxY) / 2,
            pixels: skinPixels
        };
    }

    analyzeHandGesture(handRegion, imageData) {
        const { centerX, centerY, width, height } = handRegion;
        
        this.positionHistory.push({ x: centerX, y: centerY, time: Date.now() });
        if (this.positionHistory.length > this.historyMaxLength) {
            this.positionHistory.shift();
        }

        const gesture = this.detectSwipeGesture();
        if (gesture) return gesture;

        const aspectRatio = width / height;
        const area = width * height;
        
        if (aspectRatio > 0.8 && aspectRatio < 1.2 && area > 10000) {
            return 'open_palm';
        }
        
        if (aspectRatio < 0.6 && height > width * 1.5) {
            return 'thumbs_up';
        }
        
        if (area < 5000 && aspectRatio > 0.7 && aspectRatio < 1.3) {
            return 'fist';
        }

        return null;
    }

    detectSwipeGesture() {
        if (this.positionHistory.length < 5) return null;

        const recent = this.positionHistory.slice(-5);
        const first = recent[0];
        const last = recent[recent.length - 1];
        
        const deltaX = last.x - first.x;
        const deltaY = last.y - first.y;
        const deltaTime = last.time - first.time;

        if (deltaTime > 300) return null;

        if (Math.abs(deltaY) > this.sensitivity.swipeThreshold && 
            Math.abs(deltaY) > Math.abs(deltaX)) {
            if (deltaY < 0) {
                return 'swipe_up';
            } else {
                return 'swipe_down';
            }
        }

        return null;
    }

    onGesture(callback) {
        this.onGestureCallback = callback;
    }

    setSensitivity(config) {
        Object.assign(this.sensitivity, config);
    }
}

window.GestureRecognition = GestureRecognition;
