import os
import socket
import subprocess
import threading
import time
import uuid
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ollama

app = Flask(__name__)
# Enable CORS for all routes and origins so other devices on your Wi-Fi can communicate freely
CORS(app, resources={r"/*": {"origins": "*"}})

# Paths & configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ollama_pull_jobs = {}
# Reference the Ollama child process launched by this app. The kill switch
# uses this reference so it does not terminate a separately managed server.
ollama_process = None
@app.route('/api/model-catalog', methods=['GET'])
def model_catalog():
    try:
        page = requests.get('https://ollama.com/library', timeout=8).text
        names = []
        import re
        for name in re.findall(r'href=["\']/library/([a-zA-Z0-9][a-zA-Z0-9._-]*)', page):
            if name not in names and name not in ('library',):
                names.append(name)
        return jsonify({'models': names[:80] or fallback, 'source': 'ollama.com/library'})
    except Exception:
        return jsonify({'models': fallback, 'source': 'fallback', 'error': 'Ollama library could not be reached.'})

def ollama_command(*args):
    """Run an Ollama CLI command using the executable available on PATH."""
    return subprocess.run(['ollama', *args], capture_output=True, text=True, timeout=30)

@app.route('/api/models', methods=['GET'])
def list_models():
    """Return locally installed models from ``ollama list``."""
    try:
        result = ollama_command('list')
        if result.returncode != 0:
            return jsonify({'error': result.stderr.strip() or 'ollama list failed'}), 503
        models = []
        lines = result.stdout.strip().splitlines()
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append({'name': parts[0], 'size': ' '.join(parts[2:-2]) if len(parts) > 4 else ''})
        return jsonify({'models': models})
    except FileNotFoundError:
        return jsonify({'error': 'Ollama CLI was not found. Install Ollama or add it to PATH.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/start', methods=['POST'])
def start_ollama():
    global ollama_process
    try:
        requests.get('http://127.0.0.1:11434/', timeout=0.8)
        return jsonify({'started': False, 'message': 'Ollama is already running.'})
    except requests.RequestException:
        pass
    try:
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        ollama_process = subprocess.Popen(['ollama', 'serve'], creationflags=creationflags,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        return jsonify({'started': True, 'message': 'Ollama server started.'})
    except FileNotFoundError:
        return jsonify({'error': 'Ollama was not found on PATH.'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/stop', methods=['POST'])
def stop_ollama():
    global ollama_process
    if ollama_process is None or ollama_process.poll() is not None:
        return jsonify({'stopped': False, 'message': 'This app did not start Ollama.'})
    try:
        ollama_process.terminate()
        ollama_process = None
        return jsonify({'stopped': True, 'message': 'Ollama server stopped.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/pull', methods=['POST'])
def pull_model():
    """Start ``ollama pull`` in the background and return a job ID.

    Pulls can take a long time, so the browser polls the status route instead
    of holding the original HTTP request open.
    """
    model = (request.json or {}).get('model', '').strip()
    if not model:
        return jsonify({'error': 'Model name is required'}), 400
    job_id = str(uuid.uuid4())[:8]
    ollama_pull_jobs[job_id] = {'status': 'starting', 'model': model, 'progress': '', 'error': None}

    def run_pull():
        job = ollama_pull_jobs[job_id]
        try:
            job['status'] = 'pulling'
            process = subprocess.Popen(['ollama', 'pull', model], stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                job['progress'] = line.strip()
            code = process.wait()
            job['status'] = 'done' if code == 0 else 'failed'
            if code != 0:
                job['error'] = job['progress'] or 'Model pull failed.'
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)

    threading.Thread(target=run_pull, daemon=True).start()
    return jsonify({'job_id': job_id, 'model': model})

@app.route('/api/models/pull/<job_id>', methods=['GET'])
def pull_status(job_id):
    job = ollama_pull_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Unknown pull job'}), 404
    return jsonify(job)

def get_network_ips():
    """Detects active IPv4 addresses on this PC (LAN Wi-Fi, Ethernet, Tailscale)."""
    ip_list = []
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ip_list.append(ip)
    except Exception:
        pass
    return ip_list

@app.route('/')
def serve_index():
    """Serves the index.html page."""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/style.css')
def serve_css():
    """Serves style.css."""
    return send_from_directory(BASE_DIR, 'style.css')

@app.route('/api/status', methods=['GET'])
def system_status():
    """Reports connection status for Flask, Ollama, and detected network IPs."""
    ollama_ready = False

    # Check Ollama
    try:
        res = requests.get('http://127.0.0.1:11434/', timeout=1.0)
        ollama_ready = res.status_code == 200
    except Exception:
        ollama_ready = False

    return jsonify({
        'backend': True,
        'ollama': ollama_ready,
        'network_ips': get_network_ips()
    })

@app.route('/ask-ollama', methods=['POST'])
def ask_ollama():
    """Receives message and model from the webpage and queries Ollama."""
    data = request.json or {}
    user_text = data.get('message', '')
    selected_model = data.get('model', 'llama3.2')
    
    if not user_text:
        return jsonify({'error': 'Message content cannot be empty'}), 400

    try:
        response = ollama.chat(
            model=selected_model, 
            messages=[{'role': 'user', 'content': user_text}]
        )
        ai_answer = response['message']['content']
        return jsonify({'reply': ai_answer})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    ips = get_network_ips()
    print("    -> http://localhost:5000")
    print("\n  Access from other devices on your Wi-Fi / Local Network:")
    for ip in ips:
        print(f"    -> http://{ip}:5000")
    # Bind to every local interface so phones and other computers on the LAN
    # can connect. Disable the reloader because it starts a second server
    # process and makes network troubleshooting confusing on Windows.
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
