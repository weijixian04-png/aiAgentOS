class GestureRecognition {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.ctx = null;
        this.isActive = false;
        this.stream = null;
        this.animationId = null;

        this.hands = null;
        this.camera = null;
        this.lastResults = null;

        this.currentGesture = null;
        this.gestureStartTime = 0;
        this.gestureHoldTime = 500;
        this.onGestureCallback = null;
        this.lastGestureTime = 0;
        this.gestureCooldown = 1500;

        this.config = {
            holdTime: 500,
            detectionInterval: 80
        };

        this.lastDetectionTime = 0;
        this.isProcessing = false;
        this.isDarkMode = false;
    }

    async init() {
        try {
            console.log('[Gesture] Initializing MediaPipe Hands...');

            this.video = document.createElement('video');
            this.video.setAttribute('playsinline', '');
            this.video.setAttribute('autoplay', '');
            this.video.muted = true;
            this.video.id = 'gesture-camera-feed';
            this.video.style.cssText = `
                position:fixed; bottom:100px; right:20px; width:200px; height:150px;
                border-radius:10px; border:2px solid rgba(102,126,234,0.5);
                box-shadow:0 4px 15px rgba(102,126,234,0.3); z-index:9997;
                background:#1a1a2e; transform:scaleX(-1); display:none; object-fit:cover;
            `;
            document.body.appendChild(this.video);

            this.canvas = document.createElement('canvas');
            this.canvas.width = 320;
            this.canvas.height = 240;
            this.canvas.id = 'gesture-processed-feed';
            this.canvas.style.cssText = `
                position:fixed; bottom:260px; right:20px; width:200px; height:150px;
                border-radius:10px; border:2px solid rgba(68,255,68,0.5);
                box-shadow:0 4px 15px rgba(68,255,68,0.2); z-index:9996;
                background:#1a1a2e; display:none;
            `;
            document.body.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');

            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode:'user', width:{ideal:320}, height:{ideal:240}, frameRate:{ideal:24} }
            });
            this.stream = stream;
            this.video.srcObject = stream;

            await new Promise((resolve, reject) => {
                this.video.onloadedmetadata = () => {
                    this.video.play().then(resolve).catch(reject);
                };
                this.video.onerror = () => reject(new Error('Video load failed'));
                setTimeout(() => reject(new Error('Camera init timeout')), 10000);
            });

            await this.initMediaPipe();

            console.log('[Gesture] Initialization complete');
            return true;
        } catch (error) {
            console.error('[Gesture] Init failed:', error);
            throw error;
        }
    }

    async initMediaPipe() {
        const mpBasePath = '/static/dist/mediapipe/hands/';

        if (typeof Hands === 'undefined') {
            console.warn('[Gesture] Hands class not found, loading script...');
            await this.loadScript(mpBasePath + 'hands.js');
        }

        this.hands = new Hands({
            locateFile: (file) => mpBasePath + file
        });

        this.hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.6,
            minTrackingConfidence: 0.5
        });

        this.hands.onResults((results) => {
            this.lastResults = results;
        });

        console.log('[Gesture] MediaPipe Hands ready');
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }
            const script = document.createElement('script');
            script.src = src;
            script.crossOrigin = 'anonymous';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Failed to load: ' + src));
            document.head.appendChild(script);
        });
    }

    start() {
        if (this.isActive) return;
        this.isActive = true;
        if (this.video) this.video.style.display = 'block';
        if (this.canvas) this.canvas.style.display = 'block';
        this.detectLoop();
        console.log('[Gesture] Recognition started');
    }

    stop() {
        this.isActive = false;
        if (this.video) this.video.style.display = 'none';
        if (this.canvas) this.canvas.style.display = 'none';
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        console.log('[Gesture] Recognition stopped');
    }

    destroy() {
        this.stop();
        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
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
        console.log('[Gesture] Resources released');
    }

    async detectLoop() {
        if (!this.isActive) return;
        const now = Date.now();
        if (now - this.lastDetectionTime >= this.config.detectionInterval && !this.isProcessing) {
            this.lastDetectionTime = now;
            await this.performDetection();
        }
        this.animationId = requestAnimationFrame(() => this.detectLoop());
    }

    async performDetection() {
        if (this.isProcessing || !this.video || !this.ctx || !this.hands) return;
        this.isProcessing = true;
        try {
            await this.hands.send({ image: this.video });

            if (this.lastResults && this.lastResults.multiHandLandmarks && this.lastResults.multiHandLandmarks.length > 0) {
                const landmarks = this.lastResults.multiHandLandmarks[0];
                const handedness = this.lastResults.multiHandedness ? this.lastResults.multiHandedness[0] : null;

                this.drawLandmarks(landmarks);

                const gesture = this.analyzeGesture(landmarks, handedness);
                if (gesture) {
                    this.processGesture(gesture);
                } else {
                    this.resetGesture();
                }
            } else {
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.resetGesture();
            }
        } catch (error) {
            console.error('[Gesture] Detection error:', error);
        } finally {
            this.isProcessing = false;
        }
    }

    drawLandmarks(landmarks) {
        if (!this.ctx || !landmarks) return;
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        ctx.clearRect(0, 0, w, h);
        ctx.save();
        ctx.scale(-1, 1);
        ctx.translate(-w, 0);

        if (this.video.readyState >= 2) {
            ctx.globalAlpha = 0.3;
            ctx.drawImage(this.video, 0, 0, w, h);
            ctx.globalAlpha = 1;
        }

        const connections = [
            [0,1],[1,2],[2,3],[3,4],
            [0,5],[5,6],[6,7],[7,8],
            [5,9],[9,10],[10,11],[11,12],
            [9,13],[13,14],[14,15],[15,16],
            [13,17],[17,18],[18,19],[19,20],
            [0,17]
        ];

        ctx.strokeStyle = '#44ff44';
        ctx.lineWidth = 2;
        ctx.beginPath();
        connections.forEach(([s, e]) => {
            ctx.moveTo(landmarks[s].x * w, landmarks[s].y * h);
            ctx.lineTo(landmarks[e].x * w, landmarks[e].y * h);
        });
        ctx.stroke();

        landmarks.forEach((lm, i) => {
            ctx.beginPath();
            ctx.arc(lm.x * w, lm.y * h, i === 0 ? 5 : 3, 0, Math.PI * 2);
            ctx.fillStyle = [0,4,8,12,16,20].includes(i) ? '#ff4444' : '#ffffff';
            ctx.fill();
            ctx.strokeStyle = '#44ff44';
            ctx.lineWidth = 1;
            ctx.stroke();
        });

        ctx.restore();
    }

    isFingerExtended(landmarks, fingerIdx) {
        const tips = [4, 8, 12, 16, 20];
        const pips = [3, 6, 10, 14, 18];
        const mcps = [2, 5, 9, 13, 17];

        if (fingerIdx === 0) {
            const tipX = landmarks[tips[0]].x;
            const mcpX = landmarks[mcps[0]].x;
            const wristX = landmarks[0].x;
            const isRightHand = landmarks[17].x < landmarks[5].x;
            if (isRightHand) {
                return tipX < mcpX;
            } else {
                return tipX > mcpX;
            }
        }

        const tipY = landmarks[tips[fingerIdx]].y;
        const pipY = landmarks[pips[fingerIdx]].y;
        const mcpY = landmarks[mcps[fingerIdx]].y;
        return tipY < pipY && pipY < mcpY;
    }

    getFingerStates(landmarks) {
        return [0,1,2,3,4].map(i => this.isFingerExtended(landmarks, i));
    }

    detectThumbsUp(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        return fingers[0] && !fingers[1] && !fingers[2] && !fingers[3] && !fingers[4];
    }

    detectOpenPalm(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        return fingers[0] && fingers[1] && fingers[2] && fingers[3] && fingers[4];
    }

    detectVictory(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        return fingers[1] && fingers[2] && !fingers[3] && !fingers[4];
    }

    detectPointing(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        return fingers[1] && !fingers[2] && !fingers[3] && !fingers[4];
    }

    detectCallMe(landmarks) {
        const fingers = this.getFingerStates(landmarks);
        return fingers[0] && !fingers[1] && !fingers[2] && !fingers[3] && fingers[4];
    }

    analyzeGesture(landmarks, handedness) {
        if (this.detectThumbsUp(landmarks)) {
            return { type: 'thumbs_up', confidence: 0.9 };
        }
        if (this.detectOpenPalm(landmarks)) {
            return { type: 'open_palm', confidence: 0.9 };
        }
        if (this.detectPointing(landmarks)) {
            return { type: 'pointing', confidence: 0.88 };
        }
        if (this.detectVictory(landmarks)) {
            return { type: 'victory', confidence: 0.9 };
        }
        if (this.detectCallMe(landmarks)) {
            return { type: 'call_me', confidence: 0.85 };
        }

        return null;
    }

    processGesture(gesture) {
        const now = Date.now();
        if (now - this.lastGestureTime < this.gestureCooldown) return;

        if (this.currentGesture && this.currentGesture.type === gesture.type) {
            const held = now - this.gestureStartTime;
            if (held >= this.gestureHoldTime) {
                if (this.onGestureCallback) {
                    this.onGestureCallback(gesture.type, gesture.confidence);
                }
                this.lastGestureTime = now;
                this.resetGesture();
            }
        } else {
            this.currentGesture = gesture;
            this.gestureStartTime = now;
        }
    }

    resetGesture() {
        this.currentGesture = null;
        this.gestureStartTime = 0;
    }

    onGesture(callback) {
        this.onGestureCallback = callback;
    }

    setConfig(config) {
        Object.assign(this.config, config);
        if (config.holdTime) this.gestureHoldTime = config.holdTime;
    }

    getStatus() {
        return {
            isActive: this.isActive,
            currentGesture: this.currentGesture?.type || null,
            hasCamera: !!this.stream,
            hasMediaPipe: !!this.hands
        };
    }
}

window.GestureRecognition = GestureRecognition;
