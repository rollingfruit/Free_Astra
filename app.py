import os
import cv2
import threading
import base64
import time
import requests
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from queue import Queue
from pydub import AudioSegment
from pydub.playback import play
import google.generativeai as genai
from PIL import Image
import numpy as np
import errno
import os
from dotenv import load_dotenv

from openai import OpenAI
import tempfile
# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')


# 加载.env文件中的配置
load_dotenv()
# 读取环境变量
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Voice ID for ElevenLabs API (可以在这个url选择VOICE_ID："https://api.elevenlabs.io/v1/voices")
VOICE_ID = 'yoZ06aMxZJJ28mfd3POQ'

client = OpenAI(api_key=OPENAI_API_KEY)
# Configure the Google AI client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

# Folder to save frames
folder = "frames"
if not os.path.exists(folder):
    os.makedirs(folder)

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

# Queue to store text responses
text_queue = Queue()

# Flag to indicate when audio playback is in progress
audio_playing = threading.Event()

# Global variables
running = True
capture_interval = 2  # Default interval in seconds
# updated_text = "Please describe what you see in max 30 words. You are an helpful and friendly assistant called Astra. If you see questions visually answer them is very important! "
updated_text = "请用中文回答问题，30个词以内"
# 定义全局变量
encoded_image_forAudio = None

def process_audio(audio_data):
    # 将音频数据写入临时文件
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
        temp_audio_file.write(audio_data)
        temp_audio_file_path = temp_audio_file.name

    # 打开临时文件并使用 OpenAI 的 API 进行转录
    with open(temp_audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    # 删除临时文件
    os.remove(temp_audio_file_path)

    return transcription

@socketio.on('audio')
def handle_audio(data):
    
    global script, updated_text, encoded_image_forAudio
    audio_data = base64.b64decode(data)
    text = process_audio(audio_data)  # 更新全局变量 text
    updated_text = text
    # text_queue.put(text)     # 注释掉，用户的话不需要文转音
    # socketio.emit('text', {'message': text})
    socketio.emit('text', {'usermessage': text})


    # 打印encoded_image的大小
    print(f"encoded_image size: {len(encoded_image_forAudio)}")  # Debug print
    response_text = analyze_image(encoded_image_forAudio, script)
    print(f"Jarvis's response: {response_text}")

    with text_queue.mutex:
        text_queue.queue.clear()  # Clear the queue

    text_queue.put(response_text)
    socketio.emit('text', {'message': response_text})
    script.append(
        {
            "role": "model",
            "content": {
                "parts": [
                    {
                        "text": response_text
                    }
                ]
            }
        }
    )
    encoded_image_forAudio = None # Reset the variable

def encode_image(image_path):
    global encoded_image_forAudio
    while True:
        try:
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                encoded_image_forAudio = encoded_image
            return encoded_image
        except IOError as e:
            if e.errno == errno.EACCES:
                print("Permission denied, retrying in 5 seconds...")
                time.sleep(5)
            else:
                print(f"Error {e.errno}: {e.strerror}")
                return None

def generate_audio(text, filename):
    if len(text) > 2500:
        raise ValueError("Text exceeds the character limit of 2500 characters.")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    with open(filename, 'wb') as f:
        f.write(response.content)

def play_audio():
    global audio_playing
    current_audio = "voice_current.mp3"
    next_audio = "voice_next.mp3"
    while True:
        text = text_queue.get()
        if text is None:
            break
        audio_playing.set()
        try:
            generate_audio(text, next_audio)
            os.rename(next_audio, current_audio)

            audio = AudioSegment.from_file(current_audio, format="mp3")
            play(audio)
        except Exception as e:
            print(f"Error in play_audio: {e}")
        finally:
            audio_playing.clear()

def generate_new_line(encoded_image):
    global updated_text
    return [
        {
            "role": "user",
            "content": {
                "parts": [
                    {
                        # "text": "Please describe what you see in max 30 words. You are an helpful and friendly assistant called Astra. If you see questions visually answer them is very important! "
                        # "text": "Please describe in max 30 words. "+ updated_text
                        "text":updated_text +  " 请用中文回答，30个词以内。 "
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": encoded_image
                        }
                    }
                ]
            }
        }
    ]

def analyze_image(encoded_image, script):
    try:
        messages = script + generate_new_line(encoded_image)
        content_messages = [
            {
                "role": message["role"],
                "parts": [
                    {"text": part["text"]} if "text" in part else {"inline_data": part["inline_data"]}
                    for part in message["content"]["parts"]
                ]
            }
            for message in messages
        ]
        response = model.generate_content(content_messages)
        return response.text
    except Exception as e:
        print(f"Error in analyze_image: {e}")
        return ""

def capture_images():
    global capture_interval
    global script
    script = []
    cap = cv2.VideoCapture(0)
    while running:
        try:
            ret, frame = cap.read()
            if ret:
                # Resize and compress the image
                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                max_size = 250
                ratio = max_size / max(pil_img.size)
                new_size = tuple([int(x * ratio) for x in pil_img.size])
                resized_img = pil_img.resize(new_size, Image.LANCZOS)
                frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

                path = f"{folder}/frame.jpg"
                cv2.imwrite(path, frame)
                print("📸 Saving photo.")

                encoded_image = encode_image(path)
                print(f"Encoded image: {encoded_image[:30]}...")  # Debug print

                if not encoded_image:
                    print("Failed to encode image. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                socketio.emit('stream', {'image': encoded_image})
                
                # response_text = analyze_image(encoded_image, script)
                # print(f"Jarvis's response: {response_text}")

                # with text_queue.mutex:
                #     text_queue.queue.clear()  # Clear the queue

                # text_queue.put(response_text)
                # socketio.emit('text', {'message': response_text})
                # script.append(
                #     {
                #         "role": "model",
                #         "content": {
                #             "parts": [
                #                 {
                #                     "text": response_text
                #                 }
                #             ]
                #         }
                #     }
                # )
            else:
                print("Failed to capture image")

            time.sleep(capture_interval)
        except Exception as e:
            print(f"Error in capture_images: {e}")
    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stop')
def stop():
    global running
    running = False
    return jsonify({"status": "stopped"})

@app.route('/resume')
def resume():
    global running
    global capture_thread
    running = True
    if not capture_thread.is_alive():
        capture_thread = threading.Thread(target=capture_images)
        capture_thread.start()
    return jsonify({"status": "resumed"})

@app.route('/set_interval', methods=['POST'])
def set_interval():
    global capture_interval
    interval = request.json.get('interval')
    if interval:
        capture_interval = interval
        return jsonify({"status": "interval updated", "interval": capture_interval})
    return jsonify({"status": "failed", "message": "Invalid interval"}), 400

import webbrowser

if __name__ == '__main__':
    global capture_thread
    global audio_thread
    running = True
    capture_thread = threading.Thread(target=capture_images)
    capture_thread.start()
    audio_thread = threading.Thread(target=play_audio)
    audio_thread.start()
    
    # Open the default web browser to the server link
    webbrowser.open('http://localhost:5001')
    
    socketio.run(app, host='0.0.0.0', port=5001)
    capture_thread.join()
    text_queue.put(None)
    audio_thread.join()
