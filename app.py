from flask import Flask, render_template, request, jsonify
import pyautogui
import threading
import time
import Quartz
import subprocess
app = Flask(__name__)

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
            return 50

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
                subprocess.run(['osascript', '-e', 'set volume with output unmuted'])
                self.is_muted = False
            else:
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
    app.run(host='0.0.0.0', port=5252, debug=True)