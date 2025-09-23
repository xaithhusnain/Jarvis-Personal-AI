import re
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import webbrowser
import os
import musicLibrary
import requests

# API KEYS 
NEWS_API_KEY = "Use_your_api_key"
GROQ_API_KEY = "Use_your_api_key"


# Function to speak text aloud
def speak(text):
    print("Jarvis:", text)
    tts = gTTS(text=text, lang="en")
    filename = "temp.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# GROQ SETTINGS
url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def trim_response(text, max_words=35, min_words=12, max_overflow=20):
    """
    Smart trimming:
      - Try to return complete sentences (split by . ? !) while staying <= max_words when possible.
      - If accumulated full sentences are fewer than min_words, continue adding sentences (even if it exceeds max_words)
        up to a reasonable overflow (max_overflow).
      - If no sentence boundary is found, fall back to simple word trim.
    """
    if not text:
        return text

    words = text.split()
    if len(words) <= max_words:
        return text.strip()

    sentences = re.split(r'(?<=[\.\?\!])\s+', text.strip())

    accumulated = []
    total_words = 0

    for s in sentences:
        s_words = len(s.split())
        if total_words + s_words <= max_words:
            accumulated.append(s.strip())
            total_words += s_words
            continue
        if total_words < min_words:
            accumulated.append(s.strip())
            total_words += s_words
            if total_words >= min_words:
                break
            else:
                continue
        break

    if accumulated:
        result = " ".join(accumulated).strip()
        res_words = result.split()
        if len(res_words) <= max_words + max_overflow:
            return result if len(res_words) <= max_words else " ".join(res_words[:max_words]) + "..."
        else:
            return " ".join(res_words[:max_words]) + "..."
    return " ".join(words[:max_words]) + "..."

def ask_groq(prompt):
    # Force concise replies from the model
    concise_prompt = f"Answer concisely in one or two sentences: {prompt}"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": concise_prompt}],
        "temperature": 0.7,
        "max_tokens": 100
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 200:
        full_answer = r.json()["choices"][0]["message"]["content"]
        return trim_response(full_answer)
    else:
        return f"Error {r.status_code}: {r.text}"


# Function to process commands
def processcommand(c):
    c = c.lower()
    if c in ["exit", "quit", "goodbye"]:
        speak("Goodbye! Shutting down.")
        exit()

    if "google" in c:
        speak("Opening Google")
        webbrowser.open("https://www.google.com")
    elif "youtube" in c:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")
    elif "facebook" in c:
        speak("Opening Facebook")
        webbrowser.open("https://www.facebook.com")
    elif "linkedin" in c:
        speak("Opening LinkedIn")
        webbrowser.open("https://www.linkedin.com")
    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link = musicLibrary.music.get(song, None)
        if link:
            webbrowser.open(link)
        else:
            speak("I couldn't find that song in the library.")
    elif "news" in c.lower():
        r = requests.get(
            f"https://newsapi.org/v2/everything?q=Pakistan&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        )
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])
            for article in articles[:5]:
                speak(article["title"])
        else:
            speak("Sorry, I couldn't fetch the news.")
    else:
        answer = ask_groq(c)
        speak(answer)

if __name__ == "__main__":
    speak("Initializing Jarvis...")

    while True:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening for wake word...")
            try:
                audio = r.listen(source, timeout=2, phrase_time_limit=2)
                word = r.recognize_google(audio)
                print("Heard:", word)

                if word.lower() == "jarvis":
                    speak("Ya")
                    
                    with sr.Microphone() as source:
                        print("Jarvis Active... Listening for command...")
                        audio = r.listen(source, timeout=5, phrase_time_limit=5)
                        command = r.recognize_google(audio)
                        print("Command:", command)
                        processcommand(command)

            except Exception as e:
                print("Error:", e)
