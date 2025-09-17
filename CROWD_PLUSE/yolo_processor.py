import cv2
import os
from ultralytics import YOLO

# Load the lightweight YOLOv8n model
model = YOLO('yolov8n.pt')

def process_video_file(video_path, output_folder):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return None

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    output_filename = f"processed_{os.path.basename(video_path)}"
    output_path = os.path.join(output_folder, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # This is the same detection logic as before
        results = model(frame, verbose=False)
        person_count = 0
        for r in results:
            for box in r.boxes:
                if box.cls[0] == 0: # Class 0 is 'person'
                    person_count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        text = f'Crowd Count: {person_count}'
        cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        out.write(frame)

    cap.release()
    out.release()
    return output_path


def generate_stream_frames(video_source):

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source {video_source}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame from stream.")
            break
        
        # Same detection logic
        results = model.track(frame, persist=True, verbose=False)
        
        # Check if tracks are found
        if results[0].boxes.id is not None:
            person_count = 0
            # Get the bounding boxes and track IDs
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)

            # Loop over the detected objects and draw their track
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                
                # Draw the bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # --- DRAW THE TRACK ID ---
                id_text = f"ID: {track_id}"
                cv2.putText(frame, id_text, (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        text = f'Crowd Count: {person_count}'
        cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Encode the frame as JPEG
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        
        # Yield the output frame in the byte format for streaming
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
    
    cap.release()