from flask import Flask, render_template_string, redirect, url_for, request, session
import serial
import time

app = Flask(__name__)
app.secret_key = 'iot-secret-key-2024'
ser = serial.Serial('COM7', 9600, timeout=1)

ADMIN_USER = 'admin'
ADMIN_PASS = 'admin'

HTML_LOGIN = '''
<!DOCTYPE html>
<html>
<head>
    <title>IoT — Вход</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 16px; padding: 48px 40px; width: 360px; }
        .logo { font-size: 32px; margin-bottom: 8px; }
        h2 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
        .sub { color: #666; font-size: 14px; margin-bottom: 32px; }
        label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
        input { width: 100%; padding: 12px 16px; background: #0f0f1a; border: 1px solid #2a2a4a; border-radius: 8px; color: #fff; font-size: 15px; margin-bottom: 16px; outline: none; transition: border 0.2s; }
        input:focus { border-color: #4ecca3; }
        button { width: 100%; padding: 13px; background: #4ecca3; color: #0f0f1a; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
        button:hover { opacity: 0.85; }
        .error { background: #2a1a1a; border: 1px solid #e94560; color: #e94560; padding: 10px 14px; border-radius: 8px; font-size: 14px; margin-bottom: 16px; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">⚡</div>
        <h2>IoT Panel</h2>
        <p class="sub">Войдите для управления устройствами</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <label>Логин</label>
            <input type="text" name="username" placeholder="admin" autocomplete="off">
            <label>Пароль</label>
            <input type="password" name="password" placeholder="••••••">
            <button type="submit">Войти →</button>
        </form>
    </div>
</body>
</html>
'''

HTML_PANEL = '''
<!DOCTYPE html>
<html>
<head>
    <title>IoT Panel</title>
    <meta charset="utf-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #fff; min-height: 100vh; }

        /* Navbar */
        nav { display: flex; align-items: center; justify-content: space-between; padding: 20px 40px; border-bottom: 1px solid #1e1e35; }
        .nav-logo { font-size: 18px; font-weight: 600; letter-spacing: 0.5px; }
        .nav-logo span { color: #4ecca3; }
        .nav-right { display: flex; align-items: center; gap: 20px; }
        .badge { background: #1a2a1a; border: 1px solid #2a4a2a; color: #4ecca3; font-size: 12px; padding: 4px 12px; border-radius: 20px; }
        .logout { color: #555; font-size: 14px; text-decoration: none; transition: color 0.2s; }
        .logout:hover { color: #e94560; }

        /* Main */
        main { max-width: 960px; margin: 0 auto; padding: 48px 24px; }
        .page-title { font-size: 26px; font-weight: 600; margin-bottom: 4px; }
        .page-sub { color: #555; font-size: 15px; margin-bottom: 40px; }

        /* Device card */
        .devices { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .device { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 16px; padding: 28px; transition: border-color 0.3s; }
        .device.active { border-color: #4ecca3; }
        .device-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
        .device-icon { font-size: 28px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #2a2a4a; transition: background 0.3s; }
        .status-dot.on { background: #4ecca3; box-shadow: 0 0 8px #4ecca3; }
        .device-name { font-size: 17px; font-weight: 600; margin-bottom: 4px; }
        .device-status { font-size: 13px; color: #555; margin-bottom: 24px; }
        .device-status span { color: #4ecca3; }
        .device-status span.off { color: #e94560; }

        /* Toggle buttons */
        .controls { display: flex; gap: 10px; }
        .btn { flex: 1; padding: 11px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
        .btn-on { background: #4ecca3; color: #0f0f1a; }
        .btn-on:hover { opacity: 0.85; }
        .btn-off { background: #1e1e35; color: #888; border: 1px solid #2a2a4a; }
        .btn-off:hover { border-color: #e94560; color: #e94560; }
        .btn:disabled { opacity: 0.4; cursor: not-allowed; }

        /* Log */
        .log-section { margin-top: 48px; }
        .log-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #888; text-transform: uppercase; letter-spacing: 1px; font-size: 12px; }
        .log { background: #0a0a14; border: 1px solid #1e1e35; border-radius: 12px; padding: 20px; font-family: 'Courier New', monospace; font-size: 13px; color: #4ecca3; height: 160px; overflow-y: auto; }
        .log-entry { margin-bottom: 4px; color: #555; }
        .log-entry .time { color: #333; }
        .log-entry .cmd-on { color: #4ecca3; }
        .log-entry .cmd-off { color: #e94560; }
    </style>
</head>
<body>
    <nav>
        <div class="nav-logo">⚡ IoT <span>Panel</span></div>
        <div class="nav-right">
            <div class="badge">● Online</div>
            <a href="/logout" class="logout">Выйти</a>
        </div>
    </nav>

    <main>
        <div class="page-title">Управление устройствами</div>
        <p class="page-sub">Arduino Uno — COM7</p>

        <div class="devices">
            <div class="device" id="device1">
                <div class="device-header">
                    <span class="device-icon">💡</span>
                    <div class="status-dot" id="dot"></div>
                </div>
                <div class="device-name">Светодиод</div>
                <div class="device-status">Статус: <span class="off" id="statusText">ВЫКЛ</span></div>
                <div class="controls">
                    <button class="btn btn-on" onclick="sendCmd('on')">Включить</button>
                    <button class="btn btn-off" onclick="sendCmd('off')">Выключить</button>
                </div>
            </div>
        </div>

        <div class="log-section">
            <div class="log-title">Лог команд</div>
            <div class="log" id="log"></div>
        </div>
    </main>

    <script>
        let busy = false;

        function now() {
            return new Date().toLocaleTimeString('ru-RU');
        }

        function addLog(cmd) {
            const log = document.getElementById('log');
            const cls = cmd === 'on' ? 'cmd-on' : 'cmd-off';
            const text = cmd === 'on' ? 'LED ON' : 'LED OFF';
            log.innerHTML += `<div class="log-entry"><span class="time">[${now()}]</span> → <span class="${cls}">${text}</span></div>`;
            log.scrollTop = log.scrollHeight;
        }

        function sendCmd(cmd) {
            if (busy) return;
            busy = true;

            const dot = document.getElementById('dot');
            const status = document.getElementById('statusText');
            const device = document.getElementById('device1');

            fetch('/' + cmd).then(r => r.text()).then(() => {
                if (cmd === 'on') {
                    dot.className = 'status-dot on';
                    status.textContent = 'ВКЛ';
                    status.className = '';
                    device.classList.add('active');
                } else {
                    dot.className = 'status-dot';
                    status.textContent = 'ВЫКЛ';
                    status.className = 'off';
                    device.classList.remove('active');
                }
                addLog(cmd);
                setTimeout(() => busy = false, 300);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template_string(HTML_PANEL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['user'] = request.form['username']
            return redirect(url_for('index'))
        error = 'Неверный логин или пароль'
    return render_template_string(HTML_LOGIN, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/on')
def led_on():
    if 'user' not in session:
        return 'Unauthorized', 401
    ser.write(bytes([49]))
    ser.flush()
    time.sleep(0.1)
    return 'ON'

@app.route('/off')
def led_off():
    if 'user' not in session:
        return 'Unauthorized', 401
    ser.write(bytes([48]))
    ser.flush()
    time.sleep(0.1)
    return 'OFF'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)