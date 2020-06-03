from __future__ import print_function
import speech_recognition as sr

import webbrowser
import datetime
import time
import pickle
import os
import pyttsx3
import os.path
import random
import pytz
import subprocess
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from time import ctime

r= sr.Recognizer()
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september", "october", "november", "december"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_EXTENTIONS = ["rd", "th", "st", "nd"]

def there_exists(terms):
    for term in terms:
        if term in voice_data:
            return True

def record_audio(ask = False):
    with sr.Microphone() as source:
        print("Listening...")
        if ask:
            JARVIS_speak(ask)
        audio = r.listen(source)
        voice_data = ''
        try:
            print("Recognizing...")
            voice_data = r.recognize_google(audio)
        except sr.UnknownValueError:
            JARVIS_speak('What did you say?')
        except sr.RequestError:
            JARVIS_speak('Sorry, my speech service is down!')
        return voice_data


def JARVIS_speak(audio_string):
    engine = pyttsx3.init()
    en_voice_id = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"
    engine.setProperty('voice', en_voice_id)
    engine.say(audio_string)
    engine.runAndWait() 


def authenticate_google():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

def get_events(day, service):
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        JARVIS_speak('No upcoming events found.')
    else:
        JARVIS_speak(f"You have {len(events)} events on this day.")

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("+")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
                start_time = start_time + "pm"

            JARVIS_speak(event["summary"] + " at " + start_time)


def get_date(audio_string):
    audio_string = audio_string.lower()
    today = datetime.date.today()

    if audio_string.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in audio_string.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENTIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    if month < today.month and month != -1:  
        year = year+1

    if month == -1 and day != -1:  
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if audio_string.count("next") >= 1:
                dif += 7

        return today + datetime.timedelta(dif)

    if day != -1:  
        return datetime.date(month=month, day=day, year=year)

def note(audio_string):
    date = datetime.datetime.now()
    file_name = str(date).replace(":", "-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(audio_string)

    subprocess.Popen(["notepad.exe", file_name])

SERVICE = authenticate_google()
print("Start")
audio_string = record_audio()

def respond(voice_data):
    #greetings
    if there_exists(['hey','hi','hello']):
        greetings = ["hey nico, how can I help you", "hey nico, what's up?", "I'm listening nico", "hello Nico"]
        greet = greetings[random.randint(0,len(greetings)-1)]
        JARVIS_speak(greet)

    #Calendar
    if there_exists(["what do i have", "do i have plans", "am i busy"]):
        date = get_date(audio_string)
        if date:
            get_events(date, SERVICE)
        else:
            JARVIS_speak("I didn't quite get that")

    #note
    if there_exists(["make a note", "write this down", "remember this", "type this"]):
        JARVIS_speak("What would you like me to write down? ")
        write_down = voice_data
        note(write_down)
        JARVIS_speak("I've made a note of that.")

    #name
    if there_exists(["what is your name","what's your name","tell me your name"]):
        JARVIS_speak("My Name is J.A.R.V.I.S. Version 1BF64B")

    #age
    if 'how old are you' in voice_data:
        JARVIS_speak('The first letter of my program was typed at the 16th may 2020!')

    #developer
    if 'who made you' in voice_data:
        JARVIS_speak('Its Nico, but most of the programming he got from a youtuber called Traversy Media!')

    #time
    if 'what time is it' in voice_data:
        time = ctime().split(" ")[3].split(":")[0:2]
        if time[0] == "00":
            hours = '12'
        else:
            hours = time[0]
        minutes = time[1]
        time = f'{hours} {minutes}'
        JARVIS_speak(time)

    # search google
    if there_exists(["search for"]):
        search_term = voice_data.split("for")[-1]
        url = f"https://google.com/search?q={search_term}"
        webbrowser.get().open(url)
        JARVIS_speak(f'Here is what I found for {search_term} on google')

    # open whatsapp
    if there_exists(["check for messages"]):
        url = "https://web.whatsapp.com/"
        webbrowser.get().open(url)
        JARVIS_speak("opening WhatsApp")

    #exit
    if there_exists(["exit", "quit", "goodbye"]):
        JARVIS_speak("Going offline")
        exit()

time.sleep(7)
while(1):
    voice_data = record_audio() # get the voice input
    respond(voice_data) # respond

