from flask import Flask, render_template, Response
import cv2
from model.sonic import*

app = Flask(__name__)

# Create a VideoCapture object.
cap = cv2.VideoCapture(0)

def generate_frames():
    while True:
        # Read a frame from the webcam.
        ret, frame = cap.read()

        # Convert the frame to a NumPy array.
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Yield the frame.
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg', frame)[1].tobytes() + b'\r\n')
#================================================================================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():

        # Save Cam images frames to an in-program stream
        # Setup video stream on a processor Thread for faster speed
    # if WEBCAM:   #  Start Web Cam stream (Note USB webcam must be plugged in)
    #     print("Initializing USB Web Camera ....")
    #     vs = WebcamVideoStream().start()
    #     vs.CAM_SRC = WEBCAM_SRC
    #     vs.CAM_WIDTH = WEBCAM_WIDTH
    #     vs.CAM_HEIGHT = WEBCAM_HEIGHT
    #     time.sleep(4.0)  # Allow WebCam to initialize
    # else:
    #     print("Initializing Pi Camera ....")
    #     vs = PiVideoStream().start()
    #     #vs.camera.rotation = CAMERA_ROTATION
    #     #vs.camera.hflip = CAMERA_HFLIP
    #     #vs.camera.vflip = CAMERA_VFLIP
    #     time.sleep(2.0)  # Allow PiCamera to initialize

    # sonicTrack()
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
