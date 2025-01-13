# This is a speech to speech application. the following are the core steps
#1. send in audio(user input) and get it transcribed
#2. We want to send the trascribed text to chatgpt and get a response
#3. we want to save the chat history to send back and forth for context.


from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse,FileResponse

from openai import OpenAI

from elevenlabs.client import ElevenLabs
from elevenlabs import stream, VoiceSettings

import os
import json
import requests

from dotenv import load_dotenv
load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
openai_org = os.getenv("OPENAI_ORG")
elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')

client = OpenAI()

elevenlabs_client = ElevenLabs(
    api_key=elevenlabs_key,
)

app = FastAPI()

#1. send in audio(user input) and get it transcribed
@app.post('/talk')
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)

    with open("temp_audio.mp3", "wb") as f:
            for chunk in audio_output:
                f.write(chunk)

    return FileResponse("temp_audio.mp3", media_type="audio/mpeg", filename="response.mp3")
    
def transcribe_audio(file):
    audio_file = open(file.filename, 'rb')
    transcription = client.audio.transcriptions.create(model = "whisper-1", file =audio_file)
    #transcription = {'role':'user', 'content':'who won the world series in 2020?'}
    # print(transcription)
    return transcription

def get_chat_response(user_message):
    messages = load_messages()
    content = user_message.text # Extract the content from the object
    messages.append({'role':'user', 'content':content})
    gpt_response = gpt_response = client.chat.completions.create(
        model ='gpt-3.5-turbo',
        messages = messages
    )
    parsed_gpt_response = gpt_response.choices[0].message.content

    #print(parsed_gpt_response)
    save_messages(content, parsed_gpt_response)

    return parsed_gpt_response

def load_messages():
    messages=[]
    file = 'database.json'
# If the file is empty we need to add the context, 
# if not add the last message of the user and last response of the bot

    empty = os.stat(file).st_size ==0
    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)
    else:
        messages.append(
            {'role':'system', 'content': "You are interviweing the user for a front-end react developer position. Ask\
              short questions that are relevant to a junior level developer. Your name is sam. The user is sai. Keep responses under 30 words and be funny sometimes."},

        )
    return messages

def save_messages(content, parsed_gpt_response):
      # Load the entire chat history
    file = 'database.json'

    user_message_dict ={'role':'user', 'content':content}
    gpt_response_dict = {'role': 'assistant', 'content': parsed_gpt_response}

    messages = load_messages()
    messages.append(user_message_dict)  # Append the user message to the chat history
    messages.append(gpt_response_dict) # Append the GPT response to the chat history
    with open(file, 'w') as db_file:
        json.dump(messages, db_file)


def text_to_speech(text):
    audio_stream = elevenlabs_client.text_to_speech.convert_as_stream(
    text="",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2")

    return audio_stream


# Tried multple ways of streaming. check them if interested.
"""
def text_to_speech(text):
    voice_id = 'pNInz6obpgDQGcFmaJgB'
    
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    headers = {
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
        "xi-api-key": elevenlabs_key
    }

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print('something went wrong')
    except Exception as e:
        print(e)


import uuid
from io import BytesIO
from typing import IO

if not elevenlabs_api_key:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")


def text_to_speech_stream(text: str) -> IO[bytes]:
    response = elevenlabs_client.text_to_speech.convert(
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
            optimize_streaming_latency="0",
            output_format="mp3_22050_32",
            text=text,
            model_id="eleven_multilingual_v2",
            voice_settings=VoiceSettings(
                stability=0.0,
                similarity_boost=1.0,
                style=0.0,
                use_speaker_boost=True,
            ),
        )

    print("Streaming audio data...")

        # Create a BytesIO object to hold audio data
    audio_stream = BytesIO()

        # Write each chunk of audio data to the stream
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)

        # Reset stream position to the beginning
    audio_stream.seek(0)

        # Return the stream for further use
    return audio_stream
    
"""