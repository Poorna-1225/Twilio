import os
import json
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI() 

from elevenlabs.client import ElevenLabs
elvenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
elevenlabs_client = ElevenLabs(api_key=elvenlabs_api_key)

def transcribe(audio_bytes):
    if audio_bytes:
        transcription = openai_client.audio.transcriptions.create(model = "whisper-1", file = audio_bytes)

    return transcription

def get_chat_response(user_message):
    messages = load_messages()
    content = user_message.text # Extract the content from the object
    messages.append({'role':'user', 'content':content})
    gpt_response = gpt_response = openai_client.chat.completions.create(
        model ='gpt-3.5-turbo',
        messages = messages
    )
    parsed_gpt_response = gpt_response.choices[0].message.content

    #print(parsed_gpt_response)
    save_messages(content, parsed_gpt_response)

    return parsed_gpt_response

def load_messages():
    messages=[]
    file = 'new_database.json'
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
            {'role':'system', 
             'content': "You are interviweing the user for a AI Engineer or Generative AI Engineer position. Ask short questions that are relevant to a junior level developer.\
                  Your name is sam. Ask user for his name and use it through out the interview to call him.Keep responses under 30 words and be funny sometimes."},

        )
    return messages

def save_messages(content, parsed_gpt_response):
      # Load the entire chat history
    file = 'new_database.json'

    user_message_dict ={'role':'user', 'content':content}
    gpt_response_dict = {'role': 'assistant', 'content': parsed_gpt_response}

    messages = load_messages()
    messages.append(user_message_dict)  # Append the user message to the chat history
    messages.append(gpt_response_dict) # Append the GPT response to the chat history
    with open(file, 'w') as db_file:
        json.dump(messages, db_file)


def text_to_speech(text_response):
    audio_response = elevenlabs_client.text_to_speech.convert_as_stream(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    output_format="mp3_44100_128",
    text= text_response,
    model_id="eleven_multilingual_v2",)

    return audio_response
