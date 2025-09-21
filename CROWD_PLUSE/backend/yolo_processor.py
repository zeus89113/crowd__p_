import cv2
import os
from ultralytics import YOLO
import subprocess

# Load the lightweight YOLOv8n model
model = YOLO('yolov8n.pt')

def process_video_file(video_path, output_folder):
    """
    Processes a video, extracts analytics, draws annotations using .plot(),
    and uses FFmpeg to ensure the final MP4 is web-compatible.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return None, None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # --- Analytics Variables ---
    all_counts = []
    total_frames = 0

    # --- Temporary File for OpenCV Output ---
    base_filename = os.path.splitext(os.path.basename(video_path))[0]
    temp_output_path = os.path.join(output_folder, f"temp_{base_filename}.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_output_path, fourcc, fps, (frame_width, frame_height))

    if not out.isOpened():
        print("Error: Could not open VideoWriter for temporary file.")
        cap.release()
        return None, None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        total_frames += 1
        
        # Run YOLO model on the frame
        results = model(frame)
        
        # Get the annotated frame using the reliable .plot() method
        # The .plot() method returns an RGB image
        annotated_frame_rgb = results[0].plot()
        
        # Convert the RGB image to BGR for OpenCV's VideoWriter
        annotated_frame_bgr = cv2.cvtColor(annotated_frame_rgb, cv2.COLOR_RGB2BGR)
        
        # Extract person count for analytics
        person_count = 0
        for box in results[0].boxes:
            if box.cls == 0: # 0 is the class ID for 'person'
                person_count += 1
        all_counts.append(person_count)
        
        # Write the correctly formatted (BGR) annotated frame to the temporary video
        out.write(annotated_frame_bgr)

    cap.release()
    out.release()
    
    # --- Analytics Calculation ---
    analytics = {
        "peak_count": max(all_counts) if all_counts else 0,
        "average_count": round(sum(all_counts) / len(all_counts), 2) if all_counts else 0,
        "total_frames": total_frames
    }

    # --- FFmpeg Conversion for Web Compatibility ---
    final_output_path = os.path.join(output_folder, f"processed_{base_filename}.mp4")
    command = [
        'ffmpeg',
        '-i', temp_output_path,
        '-vcodec', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-y',
        final_output_path
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"--- FFmpeg Error ---: {e.stderr}")
        return None, None
    finally:
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)

    return final_output_path, analytics

def generate_stream_frames(video_source, socketio=None): # Added socketio for future use
    """
    Generates annotated frames from a live video source for streaming.
    """
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source {video_source}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame from stream.")
            break
        
        # --- IMPROVED: Using the .plot() method for robust annotation ---
        results = model.track(frame, persist=True, verbose=False)
        annotated_frame = results[0].plot() # This single line handles all drawing

        # Encode the ANNOTATED frame as JPEG
        (flag, encodedImage) = cv2.imencode(".jpg", annotated_frame)
        if not flag:
            continue
        
        # Yield the output frame for the browser
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
    
    cap.release()