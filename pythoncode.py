import os
import glob
import base64
import socket
import subprocess
import threading
import time
import uuid
import requests
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import ollama

app = Flask(__name__)
# Enable CORS for all routes and origins so other devices on your Wi-Fi can communicate freely
CORS(app, resources={r"/*": {"origins": "*"}})

# Paths & configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOOOCUS_OUTPUT_DIR = r"C:\Users\Jacob\Documents\Usefull scripts\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\Fooocus\outputs"
FOOOCUS_API_URL = "http://127.0.0.1:7865"
# Fooocus is launched lazily from its Windows launcher when an image is requested.
FOOOCUS_RUN_BAT = os.path.join(os.path.dirname(os.path.dirname(FOOOCUS_OUTPUT_DIR)), 'run.bat')

# SkyReels local paths
SKYREELS_DIR = r"E:\SkyReels\SkyReels-V2"
SKYREELS_PYTHON = os.path.join(SKYREELS_DIR, ".venv", "Scripts", "python.exe")
SKYREELS_MODEL = os.path.join(SKYREELS_DIR, "models", "SkyReels-V2-DF-1.3B-540P")
SKYREELS_OUTPUT_DIR = os.path.join(SKYREELS_DIR, "result", "diffusion_forcing")

# Track video generation jobs: {job_id: {"status": ..., "output_path": ..., "error": ...}}
video_jobs = {}
ollama_pull_jobs = {}
# Reference the Ollama child process launched by this app. The kill switch
# uses this reference so it does not terminate a separately managed server.
ollama_process = None
# Reference to the Fooocus launcher started by this app for safe shutdown.
fooocus_process = None

def fooocus_is_running():
    """Return True when Fooocus is responding on its local Gradio port."""
    try:
        return requests.get(f'{FOOOCUS_API_URL}/', timeout=1.0).status_code < 500
    except requests.RequestException:
        return False

def ensure_fooocus_running():
    """Start Fooocus only when needed and return an explanatory error if not."""
    global fooocus_process
    if fooocus_is_running():
        return None
    if not os.path.exists(FOOOCUS_RUN_BAT):
        return f'Fooocus launcher not found at {FOOOCUS_RUN_BAT}'
    try:
        fooocus_process = subprocess.Popen(['cmd', '/c', FOOOCUS_RUN_BAT],
                                            cwd=os.path.dirname(FOOOCUS_RUN_BAT),
                                            creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0),
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            time.sleep(1)
            if fooocus_is_running():
                return None
        return 'Fooocus did not become ready within 60 seconds.'
    except Exception as e:
        return f'Could not start Fooocus: {e}'

@app.route('/api/fooocus/stop', methods=['POST'])
def stop_fooocus():
    """Stop only the Fooocus process tree started by this app."""
    global fooocus_process
    if fooocus_process and fooocus_process.poll() is None:
        subprocess.run(['taskkill', '/PID', str(fooocus_process.pid), '/T', '/F'],
                       capture_output=True, text=True)
        fooocus_process = None
        return jsonify({'stopped': True, 'message': 'Fooocus stopped.'})
    return jsonify({'stopped': False, 'message': 'This app did not start Fooocus.'})

@app.route('/api/model-catalog', methods=['GET'])
def model_catalog():
    """Get model names from Ollama's official library for the pull picker.

    Ollama exposes the library as a website rather than a stable public JSON
    endpoint, so the route extracts model links from the HTML and keeps a
    small fallback list for offline use or temporary website changes.
    """
    fallback = ['llama3.1', 'llama3.2', 'gemma3', 'qwen2.5', 'deepseek-r1', 'mistral', 'phi4', 'gpt-oss']
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
    """Start Ollama on demand before a chat message is sent.

    If Ollama is already running, the existing server is reused. This route is
    intentionally automatic, so the UI does not need a separate Start button.
    """
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
    """Stop the Ollama process started by this app, if one exists."""
    global ollama_process
    if ollama_process and ollama_process.poll() is None:
        ollama_process.terminate()
        try:
            ollama_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ollama_process.kill()
        ollama_process = None
        return jsonify({'stopped': True, 'message': 'Ollama stopped.'})
    return jsonify({'stopped': False, 'message': 'This app did not start an Ollama process.'})

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
    """Reports connection status for Flask, Ollama, Fooocus, and detected network IPs."""
    ollama_ready = False
    fooocus_ready = False

    # Check Ollama
    try:
        res = requests.get('http://127.0.0.1:11434/', timeout=1.0)
        ollama_ready = res.status_code == 200
    except Exception:
        ollama_ready = False

    # Check Fooocus
    try:
        res = requests.get(f'{FOOOCUS_API_URL}/', timeout=1.0)
        fooocus_ready = res.status_code == 200
    except Exception:
        fooocus_ready = False

    return jsonify({
        'backend': True,
        'ollama': ollama_ready,
        'fooocus': fooocus_ready,
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

@app.route('/generate-image', methods=['POST'])
def generate_image():
    """Dispatches image generation request to Fooocus via Gradio client."""
    data = request.json or {}
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    aspect_ratio = data.get('aspect_ratio', '1152*896')
    style = data.get('style', 'Fooocus V2')
    performance = data.get('performance', 'Speed')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        startup_error = ensure_fooocus_running()
        if startup_error:
            return jsonify({'error': startup_error}), 503
        from gradio_client import Client
        client = Client(FOOOCUS_API_URL)
        
        # Fooocus/Gradio versions have used different names for this event.
        # Try the known names so an upgrade does not break image generation.
        generation_args = [
            prompt, negative_prompt, [style], performance, aspect_ratio,
            1, "png", -1, False, 2.0, 7.0,
            "juggernautXL_v8Rundiffusion.safetensors", "None", 0.5,
        ]
        last_error = None
        for endpoint in ("/generate_clicked", "/generate", "/predict"):
            try:
                client.predict(*generation_args, api_name=endpoint)
                break
            except Exception as endpoint_error:
                last_error = endpoint_error
        else:
            raise RuntimeError(
                f'Fooocus API endpoint was not found. Available API names may have changed. '
                f'Open Fooocus and use its "Use via API" link. Details: {last_error}'
            )

        # Look for the newly generated image in outputs
        if os.path.exists(FOOOCUS_OUTPUT_DIR):
            png_files = glob.glob(os.path.join(FOOOCUS_OUTPUT_DIR, '**', '*.png'), recursive=True)
            if png_files:
                latest_image = max(png_files, key=os.path.getctime)
                with open(latest_image, "rb") as img_file:
                    b64_data = base64.b64encode(img_file.read()).decode('utf-8')
                    return jsonify({'image_url': f"data:image/png;base64,{b64_data}"})

        return jsonify({'error': 'Image was rendered but output file could not be located'}), 500

    except Exception as e:
        return jsonify({
            'error': f'Fooocus error: {str(e)}. Make sure Fooocus run.bat is started.'
        }), 500

@app.route('/generate-video', methods=['POST'])
def generate_video():
    """
    LOCAL SkyReels Video Generation:
    Runs generate_video_df.py as a subprocess using the SkyReels venv.
    Returns a job_id for async polling since generation takes several minutes.
    """
    data = request.json or {}
    prompt = data.get('prompt', '')
    num_frames = data.get('num_frames', 25)
    steps = data.get('steps', 20)
    height = data.get('height', 544)
    width = data.get('width', 960)
    seed = data.get('seed', 42)

    if not prompt:
        return jsonify({'error': 'Video prompt is required'}), 400

    # Verify SkyReels installation exists
    if not os.path.exists(SKYREELS_PYTHON):
        return jsonify({'error': f'SkyReels Python not found at {SKYREELS_PYTHON}. Check E:\\SkyReels installation.'}), 500

    job_id = str(uuid.uuid4())[:8]
    video_jobs[job_id] = {"status": "starting", "output_path": None, "error": None}

    def run_skyreels():
        try:
            video_jobs[job_id]["status"] = "running"

            cmd = [
                SKYREELS_PYTHON, "-u", "generate_video_df.py",
                "--model_id", SKYREELS_MODEL,
                "--resolution", "540P",
                "--height", str(height),
                "--width", str(width),
                "--num_frames", str(num_frames),
                "--base_num_frames", str(num_frames),
                "--inference_steps", str(steps),
                "--guidance_scale", "6.0",
                "--shift", "8.0",
                "--seed", str(seed),
                "--offload",
                "--teacache",
                "--use_ret_steps",
                "--teacache_thresh", "0.3",
                "--prompt", prompt,
            ]

            print(f"[SkyReels] Job {job_id} starting: {' '.join(cmd[:6])}...")
            result = subprocess.run(
                cmd,
                cwd=SKYREELS_DIR,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
                video_jobs[job_id]["status"] = "failed"
                video_jobs[job_id]["error"] = error_msg
                print(f"[SkyReels] Job {job_id} FAILED: {error_msg}")
                return

            # Find the most recently created mp4 in the output dir
            mp4_files = glob.glob(os.path.join(SKYREELS_OUTPUT_DIR, "*.mp4"))
            if mp4_files:
                latest = max(mp4_files, key=os.path.getctime)
                video_jobs[job_id]["status"] = "done"
                video_jobs[job_id]["output_path"] = latest
                print(f"[SkyReels] Job {job_id} DONE: {latest}")
            else:
                video_jobs[job_id]["status"] = "failed"
                video_jobs[job_id]["error"] = "Generation finished but no .mp4 output file found."

        except subprocess.TimeoutExpired:
            video_jobs[job_id]["status"] = "failed"
            video_jobs[job_id]["error"] = "Generation timed out (30 min limit)."
        except Exception as e:
            video_jobs[job_id]["status"] = "failed"
            video_jobs[job_id]["error"] = str(e)

    thread = threading.Thread(target=run_skyreels, daemon=True)
    thread.start()

    return jsonify({
        'job_id': job_id,
        'message': 'Video generation started. This typically takes 10-20 minutes on your GPU.',
    })


@app.route('/video-status/<job_id>', methods=['GET'])
def video_status(job_id):
    """Poll this endpoint to check if video generation is complete."""
    job = video_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Unknown job ID'}), 404

    response = {'status': job['status']}
    if job['status'] == 'done':
        response['video_url'] = f'/video-file/{job_id}'
    elif job['status'] == 'failed':
        response['error'] = job.get('error', 'Unknown error')
    return jsonify(response)


@app.route('/video-file/<job_id>', methods=['GET'])
def video_file(job_id):
    """Serves the generated .mp4 file for a completed job."""
    job = video_jobs.get(job_id)
    if not job or job['status'] != 'done' or not job.get('output_path'):
        return jsonify({'error': 'Video not ready or job not found'}), 404
    return send_file(job['output_path'], mimetype='video/mp4')

if __name__ == '__main__':
    ips = get_network_ips()
    print("\n" + "=" * 65)
    print("      LOCAL AI HUB BACKEND STARTED SUCCESSFULLY")
    print("=" * 65)
    print("  Access on this PC:")
    print("    -> http://127.0.0.1:5000")
    print("    -> http://localhost:5000")
    print("\n  Access from other devices on your Wi-Fi / Local Network:")
    for ip in ips:
        print(f"    -> http://{ip}:5000")
    print("=" * 65 + "\n")

    # host='0.0.0.0' allows connections from any device on your Wi-Fi/LAN
    app.run(host='0.0.0.0', port=5000, debug=True)
