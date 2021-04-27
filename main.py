import tkinter as Tk
import speech_recognition as sr
from gtts import gTTS
from pynput import keyboard
import threading
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import os
import sys

window = Tk.Tk()
window.title("Assistant v0.1")
window.geometry("200x200")
window.resizable(False,False)

frame = Tk.Frame(window, width=800, height=400)
frame.pack()

window_closed = False
listen = False
language = 'en'
platform = sys.platform

try:
    mp3_fp = BytesIO()
    tts = gTTS(text="I'm listening", lang=language, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    startvoice = AudioSegment.from_file(mp3_fp, format="mp3")
except:
    sys.exit("Cannot create voice.")

class Background(threading.Thread):
    def run(self,*args,**kwargs):
        while True:
            if window_closed:
                break
            global listen
            if listen:
                failed = True
                play(startvoice)
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    print("Start speaking!")
                    audio = r.listen(source)
                try:
                    text = r.recognize_google(audio)
                    failed = False
                    listen = False
                except sr.UnknownValueError:
                    text = "We couldn't understand you, please speak again."
                except sr.RequestError as e:
                    text = "Could not connect to Google Voice Recognition Services."
                    listen = False
                if not failed:
                    if "open" in text.lower():
                        text = text.split("open ")[1]
                        if platform.startswith('linux'):
                            os.system(f"{text}")
                        elif platform.startswith('darwin'):
                            os.system(f"open -a \"{text}\"")
                        elif platform.startswith('win32'):
                            print("Windows support non-existent")
                        text = f"Opening {text}"
                    else:
                        text = "That's not avaiable right now."
                fp = BytesIO()
                tts = gTTS(text=text, lang=language, slow=False)
                tts.write_to_fp(fp)
                fp.seek(0)
                voice = AudioSegment.from_file(fp, format="mp3")
                play(voice)

task = Background()
task.daemon = True
task.start()

COMBINATIONS = [
    {keyboard.Key.f4}
]

current = set()

def execute():
    global listen
    listen = True

button = Tk.Button(frame,text="Start",font=("Helvetica",12),command=execute)
button.place(x=70,y=70,width=60,height=20)

def on_press(key):
    if any([key in COMBO for COMBO in COMBINATIONS]):
        current.add(key)
        if any(all(k in current for k in COMBO) for COMBO in COMBINATIONS):
            execute()

def on_release(key):
    if any([key in COMBO for COMBO in COMBINATIONS]):
        current.remove(key)

keyboardlistener = keyboard.Listener(on_press=on_press, on_release=on_release)

keyboardlistener.start()
window.mainloop()
listen = False
window_closed = True
