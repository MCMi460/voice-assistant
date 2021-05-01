import tkinter as Tk
import speech_recognition as sr
from gtts import gTTS
from pynput import keyboard
import threading
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import audioplayer
import youtube_dl
from youtube_search import YoutubeSearch
import os
import sys

version = 0.4

window = Tk.Tk()
window.title(f"Assistant v{version}")
window.geometry("200x200")
window.resizable(False,False)

frame = Tk.Frame(window, width=800, height=400)
frame.pack()

type = False
chatter = False

window_closed = False
listen = False
keygrab = False
language = 'en'
text = None
fin = False
openapp = False
playsong = False
playing = False
player = None
stop = False
chatstart = False
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
    tts = gTTS(text="I'm listening?", lang=language, slow=False)
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    startvoice = AudioSegment.from_file(mp3_fp, format="mp3")
except:
    sys.exit("Cannot create voice.\nPlease create a Github issue at https://github.com/MCMi460/voice-assistant/issues/new")

r = sr.Recognizer()

if chatter:
    from chatterbot import ChatBot
    from chatterbot.trainers import ChatterBotCorpusTrainer
    chatbot = ChatBot('Voice Assistant')

    # Create a new trainer for the chatbot
    trainer = ChatterBotCorpusTrainer(chatbot)

    # Train the chatbot based on the english corpus
    trainer.train("chatterbot.corpus.english")

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
        global stop
        global chatstart

        while True:
            if window_closed:
                break
            if fin:
                fp = BytesIO()
                tts = gTTS(text=text, lang=language, slow=False)
                tts.write_to_fp(fp)
                fp.seek(0)
                voice = AudioSegment.from_file(fp, format="mp3")
                play(voice)
                fin = False
            if listen:
                failed = True
                play(startvoice)
                if not type:
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
                else:
                    text = sys.stdin.readline()
                    text = text.replace("\n","")
                    failed = False
                    listen = False
                if not failed:
                    print(f"Text heard:\n\"{text}\"")
                    lower = text.lower()
                    if "open" in lower:
                        openapp = True
                    elif lower.startswith('play'):
                        playsong = True
                    elif 'chat' in lower and chatter:
                        chatstart = not chatstart
                    elif lower.startswith('stop'):
                        stop = True
                    else:
                        text = "That's not available right now."
                        fin = True

class BackgroundTask(threading.Thread):
    def run(self,*args,**kwargs):
        global fin
        global text

        # Global functions
        global openapp
        global chatstart
        global playsong
        global playing
        global player
        global stop

        while True:
            if window_closed:
                break
            if stop:
                stop = False
                player.stop()
                playing = False
                text = "Stopped music."
                fin = True
            elif openapp:
                openapp = False
                text = text.lower().split("open ")[1]
                if platform.startswith('linux'):
                    print("Sorry, Linux support is not available.")
                elif platform.startswith('darwin'):
                    os.system(f"open -a \"{text}\"")
                elif platform.startswith('win32'):
                    print("Sorry, Windows support is not available.")
                else:
                    print("Sorry, support for your operating system is not available.")
                text = f"Opening {text}"
                fin = True
            elif chatstart:
                chat_text = ""
                if not type:
                    with sr.Microphone() as source:
                        print("Start speaking!")
                        audio = r.listen(source)
                    try:
                        chat_text = r.recognize_google(audio)
                        print(f"<YOU> {chat_text}")
                        chat_text = f"{chatbot.get_response(chat_text)}"
                    except sr.UnknownValueError:
                        chat_text = "I couldn't understand you, please speak again."
                else:
                    chat_text = sys.stdin.readline()
                    chat_text = text.replace("\n","")
                    chat_text = f"{chatbot.get_response(chat_text)}"
                print(f"<CHAT-BOT> {chat_text}")
                fp = BytesIO()
                tts = gTTS(text=chat_text, lang=language, slow=False)
                tts.write_to_fp(fp)
                fp.seek(0)
                voice = AudioSegment.from_file(fp, format="mp3")
                play(voice)
            elif playsong:
                playsong = False
                if playing:
                    player.stop()
                    playing = False
                try:
                    text = text.lower().split("play ")[1]
                except:
                    text = "Never gonna give you up"
                if text.startswith("song "):
                    text = text.replace("song ","")
                try:
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        results = YoutubeSearch(text, max_results=1).to_dict()[0]
                        ydl.download([f'https://www.youtube.com/{results["url_suffix"]}'])
                    text = f"Playing {str(results['title'])}"
                except:
                    text = "Could not get song from Youtube."
                try:
                    player = audioplayer.AudioPlayer('yt.mp3')
                    playing = True
                    player.play()
                except FileNotFoundError():
                    text = "Format not supported."
                fin = True

voice = BackgroundVoice()
voice.daemon = True
voice.start()

task = BackgroundTask()
task.daemon = True
task.start()

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

def toggle():
    global type
    type = not type
    print(f"Toggled speaking! Permissions to type are now {type}.")

togglespeak = Tk.Button(frame,text="Toggle Speaking",font=("Helvetica",12),command=toggle)
togglespeak.place(x=35,y=125,width=130,height=20)

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
if player:
    player.close()
listen = False
window_closed = True
