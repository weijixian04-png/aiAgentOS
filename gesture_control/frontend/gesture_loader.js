(function() {
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.src = url;
        script.onload = callback;
        script.onerror = function() {
            console.warn('Gesture script load failed:', url);
        };
        document.head.appendChild(script);
    }

    if (window.gestureControlLoaded) return;
    window.gestureControlLoaded = true;

    loadScript('/gesture_control/config/gesture_config.js', function() {
        loadScript('/gesture_control/frontend/gesture_recognition.js', function() {
            loadScript('/gesture_control/frontend/gesture_actions.js', function() {
                loadScript('/gesture_control/frontend/gesture_ui.js', function() {
                    console.log('[Gesture] System loaded (MediaPipe Hands local)');
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', initGestureControl);
                    } else {
                        initGestureControl();
                    }
                });
            });
        });
    });

    function initGestureControl() {
        window.gestureUI = new GestureUI();
        window.gestureUI.init();

        const floatingWindowEnabled = localStorage.getItem('gesture_floating_window_enabled');
        if (floatingWindowEnabled === null) {
            localStorage.setItem('gesture_floating_window_enabled', 'true');
        }

        if (floatingWindowEnabled === 'true' || floatingWindowEnabled === null) {
            const container = document.getElementById('gesture-control-container');
            if (container) {
                container.style.display = 'block';
            }
        }
    }
})();
