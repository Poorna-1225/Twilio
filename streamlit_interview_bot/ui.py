import streamlit as st
import os
import time
from backend import transcribe, get_chat_response, text_to_speech
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
elvenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
elevenlabs_client = ElevenLabs(api_key=elvenlabs_api_key)


st.title (" Interview Bot")
st.text_input("Enter Name Here...")
audio_value = st.audio_input("Ask your question")

if audio_value:
    start = time.time()
    user_input = transcribe(audio_value)
    bot_response_text = get_chat_response(user_input)
    bot_audio_response = text_to_speech(bot_response_text)
    end = time.time()
    elapsed_time = end - start
    print(f"Execution time: {elapsed_time:.4f} seconds")
    stream(bot_audio_response)

