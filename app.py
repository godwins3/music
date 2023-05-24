from flask import Flask, render_template, Response
import cv2
from psonic import *
import threading

app = Flask(__name__)

# Global variables
camera = cv2.VideoCapture(0)
frame_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

def process_image():
    while True:
        with frame_lock:
            _, frame = camera.read()
            # Perform image processing on 'frame' using OpenCV
            # ...

            # Generate audio using psonic based on the processed image
            # ...
            # Example: Play a note based on the average pixel intensity
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            avg_intensity = int(gray_frame.mean())
            synth.play(70 + avg_intensity)

def generate_frames():
    while True:
        with frame_lock:
            _, frame = camera.read()

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start a separate thread for image processing and audio generation
    processing_thread = threading.Thread(target=process_image)
    processing_thread.daemon = True
    processing_thread.start()

    app.run(debug=True)
