import os
from flask import Flask, request, render_template, redirect, url_for, Response
from werkzeug.utils import secure_filename
from yolo_processor import process_video_file, generate_stream_frames


# --- CONFIGURATION ---
# Options: 'upload', 'webcam', 'cctv'
OPERATION_MODE = 'upload'


# --- Paths and Constants ---
UPLOAD_FOLDER = os.path.join('static', 'uploads')
PROCESSED_FOLDER = os.path.join('static', 'processed')
CCTV_URL = "rtsp://your_username:your_password@192.168.1.108:554/stream1"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def home():


    if OPERATION_MODE == 'upload':
        if request.method == 'POST':
            if 'video' not in request.files or request.files['video'].filename == '':
                return redirect(request.url)
            
            file = request.files['video']
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            
            processed_path = process_video_file(video_path, app.config['PROCESSED_FOLDER'])
            
            # UPDATED: Add a check to ensure processing was successful
            if processed_path:
                processed_filename = os.path.basename(processed_path)
                relative_path = os.path.join('processed', processed_filename)
                # UPDATED: Render the dashboard to show the result
                return render_template('dashboard.html', mode='upload_result', video_path=relative_path)
            else:
                return "Error: Video processing failed. Please check the console.", 500
        
        # UPDATED: Render the dashboard to show the upload form
        return render_template('dashboard.html', mode='upload_form')
    
    elif OPERATION_MODE in ['webcam', 'cctv']:
        # UPDATED: Render the dashboard to show the live stream
        return render_template('dashboard.html', mode=OPERATION_MODE)
    
    else:
        return "Error: Invalid OPERATION_MODE set in the backend.", 500

@app.route('/video_feed')
def video_feed():
    if OPERATION_MODE == 'webcam':
        video_source = 0
    elif OPERATION_MODE == 'cctv':
        video_source = CCTV_URL
    else:
        return "Video feed not available in upload mode.", 404
    
    return Response(generate_stream_frames(video_source), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # To use the pytz library, you may need to install it: pip install pytz
    app.run(debug=True)