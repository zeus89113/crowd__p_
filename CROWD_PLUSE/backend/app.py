from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import uuid
import json
import threading
from werkzeug.utils import secure_filename
from yolo_processor import process_video_file, generate_stream_frames

app = Flask(__name__)
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")
SECRET_PASSKEY = "098"
tasks = {}

# --- API Routes ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('passkey') == SECRET_PASSKEY:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid passkey"}), 401

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files: return jsonify({"error": "No video file provided"}), 400
    file = request.files['video']
    filename = secure_filename(file.filename)
    upload_folder = 'static/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    video_path = os.path.join(upload_folder, filename)
    file.save(video_path)
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "result_path": None}
    thread = threading.Thread(target=process_video_file_threaded, args=(task_id, video_path))
    thread.start()
    return jsonify({"message": "Processing started", "task_id": task_id}), 202

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route('/api/analytics/<task_id>', methods=['GET'])
def get_analytics(task_id):
    analytics_file = os.path.join('static/processed', f"{task_id}.json")
    if not os.path.exists(analytics_file):
        return jsonify({"error": "Analytics not found"}), 404
    return send_from_directory('static/processed', f"{task_id}.json")

@app.route('/video_feed/<source>')
def video_feed(source):
    # This remains largely the same, but now is a pure API endpoint
    video_source = 0 if source == 'webcam' else "YOUR_CCTV_URL"
    return Response(generate_stream_frames(video_source, socketio),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Helper for background processing ---
def process_video_file_threaded(task_id, video_path):
    processed_folder = 'static/processed'
    os.makedirs(processed_folder, exist_ok=True)
    
    # original processing function
    result_path, analytics = process_video_file(video_path, processed_folder) 
    
    if result_path and analytics is not None:
        # Create a web-accessible path
        web_path = os.path.join('processed', os.path.basename(result_path))
        web_path = web_path.replace('\\', '/') # Ensure forward slashes for web URLs
        analytics_path = os.path.join(processed_folder, f"{task_id}.json")
        with open(analytics_path, 'w') as f:
            json.dump(analytics, f)
            
        tasks[task_id] = {"status": "complete", "result_path": web_path}
    else:
        tasks[task_id] = {"status": "failed", "result_path": None}

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)