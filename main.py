import tkinter as Tk
import speech_recognition as sr
from gtts import gTTS
from pynput import keyboard
import threading
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import youtube_dl
import os
import sys

version = 0.3

window = Tk.Tk()
window.title(f"Assistant v{version}")
window.geometry("200x200")
window.resizable(False,False)

frame = Tk.Frame(window, width=800, height=400)
frame.pack()

window_closed = False
listen = False
keygrab = False
language = 'en'
text = None
fin = False
openapp = False
playsong = False
platform = sys.platform

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'yt.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

try:
    mp3_fp = BytesIO()
    tts = gTTS(text="Yes?", lang=language, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    startvoice = AudioSegment.from_file(mp3_fp, format="mp3")
except:
    sys.exit("Cannot create voice.\nPlease create a Github issue at https://github.com/MCMi460/voice-assistant/issues/new")

# START WORKING ON SECOND THREAD WITH FUNCTIONS AND KEEP VOICE LISTENING TO FIRST THREAD TOMORROW

class BackgroundVoice(threading.Thread):
    def run(self,*args,**kwargs):
        mp3_fp = BytesIO()
        tts = gTTS(text="Voice Assistant started successfully.", lang=language, slow=False)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        play(AudioSegment.from_file(mp3_fp, format="mp3"))
        global listen
        global text
        global fin

        # Global functions
        global openapp
        global playsong

        while True:
            if window_closed:
                break
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
                    print(f"Text heard:\n\"{text}\"")
                    text = text.lower()
                    if "open" in text:
                        openapp = True
                    elif text.startswith('play'):
                        playsong = True
                    else:
                        text = "That's not available right now."
                        fin = True
            if fin:
                fp = BytesIO()
                tts = gTTS(text=text, lang=language, slow=False)
                tts.write_to_fp(fp)
                fp.seek(0)
                voice = AudioSegment.from_file(fp, format="mp3")
                play(voice)
                fin = False

class BackgroundFunc(threading.Thread):
    def run(self,*args,**kwargs):
        global fin
        global text

        # Global functions
        global openapp
        global playsong

        while True:
            if window_closed:
                break
            if openapp:
                openapp = False
                text = text.split("open ")[1]
                if platform.startswith('linux'):
                    os.system(f"{text}")
                elif platform.startswith('darwin'):
                    os.system(f"open -a \"{text}\"")
                elif platform.startswith('win32'):
                    print("Windows support non-existent")
                text = f"Opening {text}"
                fin = True
            if playsong:
                playsong = False
                text = text.split("play ")[1]
                text = "Playing song"
                fin = True
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download(['https://www.youtube.com/watch?v=rXbv7gMsqxY'])
                    play(AudioSegment.from_file('yt.mp3', format="mp3"))

voice = BackgroundVoice()
voice.daemon = True
voice.start()

func = BackgroundFunc()
func.daemon = True
func.start()

COMBINATIONS = [
    {keyboard.Key.f4}
]

current = set()

def remap():
    global keygrab
    keygrab = True
    while True:
        if not keygrab or window_closed:
            break
    keyname = str(COMBINATIONS[0]).split(":")[0].replace("{<Key.","").capitalize()
    remapbutton.config(text=f"Activate Key: {keyname}")

remapbutton = Tk.Button(frame,text="Activate Key: F4",font=("Helvetica",12),command=remap)
remapbutton.place(x=35,y=100,width=130,height=20)

def execute():
    global listen
    listen = True

button = Tk.Button(frame,text="Start",font=("Helvetica",12),command=execute)
button.place(x=50,y=70,width=100,height=20)

author = Tk.Label(frame,text="By Deltaion Lee")
author.config(font=("Helvetica",10))
author.place(x=60,y=150,width=80,height=20)
author.bind("<Button-1>", lambda e: print("https://mi460.dev/github"))

title = Tk.Label(frame,text=f"Voice\n Assistant\n v{version}")
title.config(font=("Helvetica",15))
title.place(x=55,y=0,width=90,height=50)
title.bind("<Button-1>", lambda e: print("https://github.com/MCMi460/voice-assistant"))

# BROKEN, FIX TOMORROW
# ---
# IT IS TOMORROW, I FIXED IT, YOU'RE WELCOME

def on_press(key):
    if any([key in COMBO for COMBO in COMBINATIONS]):
        current.add(key)
        if any(all(k in current for k in COMBO) for COMBO in COMBINATIONS):
            execute()

def on_release(key):
    global keygrab
    global COMBINATIONS
    if any([key in COMBO for COMBO in COMBINATIONS]):
        current.remove(key)
    elif keygrab:
        COMBINATIONS = []
        COMBINATIONS.append({key})
        keygrab = False

keyboardlistener = keyboard.Listener(on_press=on_press, on_release=on_release)

keyboardlistener.start()
window.mainloop()
listen = False
window_closed = True
