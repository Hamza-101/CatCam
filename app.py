
from flask import Flask, Response, render_template, request, redirect, url_for, session, jsonify
from Systems.Camera import VideoStream  # Ensure this import matches your directory structure
import pyaudio
import threading
import sys

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize VideoStream without overlay_path
video_stream = VideoStream()  # Remove the overlay_path argument

# Audio parameters
FORMAT = pyaudio.paInt16  # Audio format (16-bit)
CHANNELS = 2  # Number of audio channels (1 for mono, 2 for stereo)
RATE = 44100  # Sample rate (samples per second)
CHUNK = 1024  # Size of each audio chunk

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Create streams
stream_output = audio.open(format=FORMAT,
                           channels=CHANNELS,
                           rate=RATE,
                           output=True)

stream_input = audio.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)

# Flag to control the recording loop
recording = False
recording_thread = None

def record_and_playback():
    global recording
    while recording:
        # Read a chunk of data from the microphone
        data = stream_input.read(CHUNK)

        # Write the data to the output stream (playback)
        stream_output.write(data)

def start_recording():
    global recording, recording_thread
    if not recording:
        recording = True
        recording_thread = threading.Thread(target=record_and_playback)
        recording_thread.start()

def stop_recording():
    global recording
    if recording:
        recording = False
        recording_thread.join()  # Ensure the thread finishes

@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', username=session.get('user', 'Guest'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password in ['secret', 'deadman', 'mykingdom', 'AliveAndWell']:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('intrude.html')
    
    return render_template('signin.html')

@app.route('/camera_off', methods=['POST'])
def camera_off():
    video_stream.stop()  # Stop the video stream
    return redirect(url_for('dashboard'))

@app.route('/signout', methods=['POST'])
def signout():
    session.pop('user', None)
    return redirect(url_for('signin'))

@app.route('/video_feed')
def video_feed():
    return Response(video_stream.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_talking', methods=['POST'])
def toggle_talking():
    global recording
    data = request.get_json()
    enable = data.get('enabled', False)
    if enable:
        start_recording()
    else:
        stop_recording()
    return jsonify({'enabled': enable})

if __name__ == '__main__':
    app.run(debug=True)

# Cleanup on exit
import atexit
atexit.register(lambda: (stream_input.stop_stream(), stream_input.close(), stream_output.stop_stream(), stream_output.close(), audio.terminate()))
