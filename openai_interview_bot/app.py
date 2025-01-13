
import os
from typing import IO
from io import BytesIO
from dotenv import load_dotenv
load_dotenv()
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs


import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from elevenlabs import stream

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY,
)

audio_stream = client.text_to_speech.convert_as_stream(
    text="hey keerthi em chesthunav? enti phone chesthe lift cheyaledhu? malli call back cheyaledhu? don't you wanna talk to me again. if that is it, it's upto you.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2"
)

# option 1: play the streamed audio locally
stream(audio_stream)

# check if stream(audio_stream) works if you are trying to execute it non locally.
