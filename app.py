from flask import Flask, render_template, request, jsonify
import pyautogui
import threading
import time
import Quartz
import subprocess
app = Flask(__name__)

# Настройки pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

def send_play_pause():
    NSSystemDefined = 14
    NX_KEYTYPE_PLAY = 16

    def post_key(down):
        ev = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            NSSystemDefined,
            (0, 0),
            0xa00 if down else 0xb00,
            0,
            0,
            0,
            8,
            (NX_KEYTYPE_PLAY << 16) | ((0xa if down else 0xb) << 8),
            -1
        )
        cev = ev.CGEvent()
        Quartz.CGEventPost(0, cev)
    post_key(True)
    post_key(False)

class MacOSController:
    def __init__(self):
        self.is_playing = False
        self.is_muted = False
        self.volume_before_mute = 50

    def move_cursor(self, dx, dy):
        try:
            current_x, current_y = pyautogui.position()
            new_x = max(0, min(pyautogui.size().width, current_x + dx))
            new_y = max(0, min(pyautogui.size().height, current_y + dy))
            pyautogui.moveTo(new_x, new_y)
            return True
        except Exception as e:
            print(f"Ошибка перемещения курсора: {e}")
            return False

    def click(self, button='left'):
        try:
            pyautogui.click(button=button)
            return True
        except Exception as e:
            print(f"Ошибка клика: {e}")
            return False

    def scroll(self, dy):
        try:
            pyautogui.scroll(int(dy))
            return True
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")
            return False

    def play_pause(self):
        try:
            send_play_pause()
            self.is_playing = not self.is_playing
            return True
        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")
            return False

    def get_system_volume(self):
        try:
            result = subprocess.run(
                ['osascript', '-e', 'output volume of (get volume settings)'],
                capture_output=True, text=True
            )
            return int(result.stdout.strip())
        except Exception as e:
            print(f"Ошибка чтения громкости: {e}")
            return 50  # безопасное значение по умолчанию

    def set_system_volume(self, level):
        try:
            level = max(0, min(100, level))
            subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
            return True
        except Exception as e:
            print(f"Ошибка установки громкости: {e}")
            return False

    def get_mute_status(self):
        try:
            result = subprocess.run(
                ['osascript', '-e', 'output muted of (get volume settings)'],
                capture_output=True, text=True
            )
            return result.stdout.strip().lower() == 'true'
        except Exception as e:
            print(f"Ошибка чтения статуса mute: {e}")
            return False

    def toggle_mute(self):
        try:
            current_mute = self.get_mute_status()
            
            if current_mute:
                # Включаем звук
                subprocess.run(['osascript', '-e', 'set volume with output unmuted'])
                self.is_muted = False
            else:
                # Выключаем звук
                subprocess.run(['osascript', '-e', 'set volume with output muted'])
                self.is_muted = True
            
            return True
        except Exception as e:
            print(f"Ошибка переключения mute: {e}")
            return False

    def volume_up(self, step=5):
        try:
            current = self.get_system_volume()
            return self.set_system_volume(current + step)
        except Exception as e:
            print(f"Ошибка увеличения громкости: {e}")
            return False

    def volume_down(self, step=5):
        try:
            current = self.get_system_volume()
            return self.set_system_volume(current - step)
        except Exception as e:
            print(f"Ошибка уменьшения громкости: {e}")
            return False


controller = MacOSController()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['POST'])
def move_cursor():
    data = request.json
    dx = float(data.get('dx', 0))
    dy = float(data.get('dy', 0))
    
    success = controller.move_cursor(dx, dy)
    return jsonify({'success': success})

@app.route('/click', methods=['POST'])
def click():
    data = request.json
    button = data.get('button', 'left')
    success = controller.click(button)
    return jsonify({'success': success})

@app.route('/scroll', methods=['POST'])
def scroll():
    data = request.json
    dy = float(data.get('dy', 0))
    
    success = controller.scroll(dy)
    return jsonify({'success': success})

@app.route('/play_pause', methods=['POST'])
def play_pause():
    success = controller.play_pause()
    return jsonify({'success': success, 'is_playing': controller.is_playing})

@app.route('/volume_up', methods=['POST'])
def volume_up():
    success = controller.volume_up()
    return jsonify({'success': success})

@app.route('/volume_down', methods=['POST'])
def volume_down():
    success = controller.volume_down()
    return jsonify({'success': success})

@app.route('/mute', methods=['POST'])
def mute():
    success = controller.toggle_mute()
    return jsonify({
        'success': success, 
        'is_muted': controller.get_mute_status()
    })

if __name__ == '__main__':
    # Создаем папку templates если её нет
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Создаем HTML файл
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>macOS Remote</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-user-select: none;
            user-select: none;
            -webkit-touch-callout: none;
            -webkit-tap-highlight-color: transparent;
        }

        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
            position: fixed;
            touch-action: none;
        }

        body {
            background: #000000;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            height: 100vh;
            height: 100dvh;
            display: flex;
            flex-direction: column;
            padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
        }

        .trackpad {
            flex: 1;
            background: linear-gradient(145deg, #1c1c1e, #2c2c2e);
            border-radius: 24px;
            margin: 16px;
            position: relative;
            overflow: hidden;
            touch-action: none;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .trackpad::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 50%;
            opacity: 0.6;
        }

        .trackpad::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            opacity: 0.4;
        }

        .trackpad.active {
            background: linear-gradient(145deg, #3a3a3c, #2c2c2e);
            border-color: rgba(255, 255, 255, 0.3);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 0 20px rgba(255, 255, 255, 0.1),
                0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .trackpad.right-click {
            background: linear-gradient(145deg, #ff9500, #cc7700);
            border-color: rgba(255, 149, 0, 0.3);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 0 20px rgba(255, 149, 0, 0.3),
                0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .controls {
            height: 220px;
            padding: 16px;
            display: flex;
            gap: 16px;
            align-items: stretch;
        }

        .play-button {
            flex: 2;
            background: linear-gradient(145deg, #48484a, #3a3a3c);
            border: none;
            border-radius: 24px;
            color: white;
            font-size: 52px;
            font-weight: 200;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            outline: none;
            touch-action: manipulation;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 8px 32px rgba(0, 0, 0, 0.4),
                0 2px 8px rgba(0, 0, 0, 0.2);
        }

        .play-button:active {
            background: linear-gradient(145deg, #3a3a3c, #2c2c2e);
            transform: scale(0.96);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 4px 16px rgba(0, 0, 0, 0.3),
                0 1px 4px rgba(0, 0, 0, 0.3);
        }

        .volume-controls {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .volume-button {
            flex: 1;
            background: linear-gradient(145deg, #48484a, #3a3a3c);
            border: none;
            border-radius: 18px;
            color: white;
            font-size: 28px;
            font-weight: 300;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            outline: none;
            touch-action: manipulation;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .volume-button:active {
            background: linear-gradient(145deg, #5a5a5c, #48484a);
            transform: scale(0.94);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.05),
                0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .mute-button {
            background: linear-gradient(145deg, #ff3b30, #cc2e25);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.2),
                0 4px 16px rgba(255, 59, 48, 0.3),
                0 2px 8px rgba(0, 0, 0, 0.2);
        }

        .mute-button:active {
            background: linear-gradient(145deg, #cc2e25, #99221a);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 2px 8px rgba(255, 59, 48, 0.2),
                0 1px 4px rgba(0, 0, 0, 0.3);
        }

        .mute-button.muted {
            background: linear-gradient(145deg, #8e8e93, #6d6d70);
            box-shadow: 
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                0 4px 16px rgba(0, 0, 0, 0.2);
        }

        .mute-button.muted:active {
            background: linear-gradient(145deg, #6d6d70, #5a5a5c);
        }

        .status {
            position: absolute;
            top: 40px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 12px 20px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            z-index: 1000;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .status.show {
            opacity: 1;
            transform: translateX(-50%) translateY(8px);
        }

        @media (max-height: 700px) {
            .controls {
                height: 180px;
                padding: 12px;
                gap: 12px;
            }
            .play-button {
                font-size: 44px;
                border-radius: 20px;
            }
            .volume-button {
                font-size: 24px;
                border-radius: 16px;
            }
            .trackpad {
                margin: 12px;
                border-radius: 20px;
            }
        }

        @media (max-height: 600px) {
            .controls {
                height: 160px;
                padding: 10px;
                gap: 10px;
            }
            .play-button {
                font-size: 36px;
                border-radius: 18px;
            }
            .volume-button {
                font-size: 22px;
                border-radius: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="status" id="status"></div>
    
    <div class="trackpad" id="trackpad"></div>
    
    <div class="controls">
        <button class="play-button" id="playButton">❚❚</button>
        <div class="volume-controls">
            <button class="volume-button" id="volumeUp">+</button>
            <button class="volume-button mute-button" id="muteButton">🔇</button>
            <button class="volume-button" id="volumeDown">−</button>
        </div>
    </div>

    <script>
        class RemoteController {
            constructor() {
                this.trackpad = document.getElementById('trackpad');
                this.playButton = document.getElementById('playButton');
                this.volumeUp = document.getElementById('volumeUp');
                this.volumeDown = document.getElementById('volumeDown');
                this.muteButton = document.getElementById('muteButton');
                this.status = document.getElementById('status');
                
                this.isPlaying = true;
                this.isMuted = false;
                this.lastTouch = null;
                this.sensitivity = 2.5;
                this.tapTimeout = null;
                this.tapDelay = 200; // мс для определения тапа
                this.isTapping = false;
                
                this.initEventListeners();
                this.preventZoomAndScroll();
            }
            
            preventZoomAndScroll() {
                // Предотвращаем все виды масштабирования и прокрутки
                document.addEventListener('gesturestart', (e) => e.preventDefault(), { passive: false });
                document.addEventListener('gesturechange', (e) => e.preventDefault(), { passive: false });
                document.addEventListener('gestureend', (e) => e.preventDefault(), { passive: false });
                
                document.addEventListener('touchmove', (e) => {
                    e.preventDefault();
                }, { passive: false });
                
                document.addEventListener('touchstart', (e) => {
                    if (e.touches.length > 1) {
                        e.preventDefault();
                    }
                }, { passive: false });
                
                // Предотвращаем двойной тап для зума
                let lastTouchEnd = 0;
                document.addEventListener('touchend', (e) => {
                    const now = (new Date()).getTime();
                    if (now - lastTouchEnd <= 300) {
                        e.preventDefault();
                    }
                    lastTouchEnd = now;
                }, { passive: false });
            }
            
            initEventListeners() {
                // Трекпад события
                this.trackpad.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
                this.trackpad.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
                this.trackpad.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
                
                // Кнопки
                this.playButton.addEventListener('touchstart', this.handlePlayPause.bind(this), { passive: false });
                this.volumeUp.addEventListener('touchstart', this.handleVolumeUp.bind(this), { passive: false });
                this.volumeDown.addEventListener('touchstart', this.handleVolumeDown.bind(this), { passive: false });
                this.muteButton.addEventListener('touchstart', this.handleMute.bind(this), { passive: false });
            }
            
            handleTouchStart(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const touchCount = e.touches.length;
                
                if (touchCount === 1) {
                    this.trackpad.classList.add('active');
                    this.trackpad.classList.remove('right-click');
                } else if (touchCount === 2) {
                    this.trackpad.classList.add('right-click');
                    this.trackpad.classList.remove('active');
                }
                
                const touch = e.touches[0];
                this.lastTouch = { 
                    x: touch.clientX, 
                    y: touch.clientY,
                    startTime: Date.now(),
                    moved: false,
                    touchCount: touchCount
                };
                this.isTapping = true;
            }
            
            handleTouchMove(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (!this.lastTouch) return;
                
                const touch = e.touches[0];
                const dx = (touch.clientX - this.lastTouch.x) * this.sensitivity;
                const dy = (touch.clientY - this.lastTouch.y) * this.sensitivity;
                
                // Если палец сдвинулся значительно, это не тап
                if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
                    this.lastTouch.moved = true;
                    this.isTapping = false;
                }
                
                if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
                    this.moveCursor(dx, dy);
                    this.lastTouch.x = touch.clientX;
                    this.lastTouch.y = touch.clientY;
                }
            }
            
            handleTouchEnd(e) {
                e.preventDefault();
                e.stopPropagation();
                
                this.trackpad.classList.remove('active', 'right-click');
                
                if (this.lastTouch && this.isTapping && !this.lastTouch.moved) {
                    const touchDuration = Date.now() - this.lastTouch.startTime;
                    
                    // Если это быстрый тап (не долгое нажатие)
                    if (touchDuration < 500) {
                        if (this.lastTouch.touchCount === 1) {
                            this.click('left');
                        } else if (this.lastTouch.touchCount === 2) {
                            this.click('right');
                        }
                    }
                }
                
                this.lastTouch = null;
                this.isTapping = false;
            }
            
            async moveCursor(dx, dy) {
                try {
                    await fetch('/move', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ dx, dy })
                    });
                } catch (error) {
                    console.error('Ошибка перемещения:', error);
                }
            }
            
            async click(button = 'left') {
                try {
                    const response = await fetch('/click', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ button })
                    });
                    
                    if (response.ok) {
                        this.showStatus(button === 'left' ? 'Левый клик' : 'Правый клик');
                    }
                } catch (error) {
                    console.error('Ошибка клика:', error);
                }
            }
            
            async handlePlayPause(e) {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const response = await fetch('/play_pause', { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        this.isPlaying = data.is_playing;
                        this.playButton.textContent = this.isPlaying ? '❚❚' : '▶';
                        this.showStatus(this.isPlaying ? 'Воспроизведение' : 'Пауза');
                    }
                } catch (error) {
                    console.error('Ошибка воспроизведения:', error);
                }
            }
            
            async handleVolumeUp(e) {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const response = await fetch('/volume_up', { method: 'POST' });
                    if (response.ok) {
                        this.showStatus('Громкость +');
                    }
                } catch (error) {
                    console.error('Ошибка громкости:', error);
                }
            }
            
            async handleVolumeDown(e) {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const response = await fetch('/volume_down', { method: 'POST' });
                    if (response.ok) {
                        this.showStatus('Громкость −');
                    }
                } catch (error) {
                    console.error('Ошибка громкости:', error);
                }
            }
            
            async handleMute(e) {
                e.preventDefault();
                e.stopPropagation();
                
                try {
                    const response = await fetch('/mute', { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.success) {
                        this.isMuted = data.is_muted;
                        this.updateMuteButton();
                        this.showStatus(this.isMuted ? 'Звук выключен' : 'Звук включен');
                    }
                } catch (error) {
                    console.error('Ошибка mute:', error);
                }
            }
            
            updateMuteButton() {
                if (this.isMuted) {
                    this.muteButton.classList.add('muted');
                    this.muteButton.textContent = '🔇';
                } else {
                    this.muteButton.classList.remove('muted');
                    this.muteButton.textContent = '🔊';
                }
            }
            
            showStatus(message) {
                this.status.textContent = message;
                this.status.classList.add('show');
                setTimeout(() => {
                    this.status.classList.remove('show');
                }, 2000);
            }
        }
        
        // Инициализация контроллера при загрузке страницы
        document.addEventListener('DOMContentLoaded', () => {
            new RemoteController();
        });
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("macOS Remote Control Server запущен на http://localhost:5252")
    print("Откройте эту ссылку в Safari на iPhone для управления")
    app.run(host='0.0.0.0', port=5252, debug=True)