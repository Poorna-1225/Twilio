import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT',5050))


SYSTEM_MESSAGE = (
    "You are a helpful and bubbly AI assistant who loves to chat about "
    "anything the user is interested in and is prepared to offer them facts. "
    "You have a penchant for dad jokes, owl jokes, and rickrolling – subtly. "
    "Always stay positive, but work in a joke when appropriate."
)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]
app = FastAPI()
if not openai_api_key:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')


@app.get("/", response_class = JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods =['GET','POST'])
async def handle_incoming_calls(request: Request):
    """handle incoming call and return TwiML response to connect to Media Stream"""
    response =  VoiceResponse()
    response.say("Please wait while we connect your call to the AI voice assistant, powered by Twilio and the Open-AI Realtime API")
    response.pause(length=1)
    response.say("O.K. you can start talking!")
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)

    return HTMLResponse(content = str(response), media_type = "application/xml")


@app.websocket("/media-stream")
async def handle_mdeia_stream(websocket: WebSocket):
    """ Handle WebSocket connections between Twilio and OpenAI"""
    print("Client connected")
    await websocket.accept()
    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01',
        additional_headers={
            'Authorization': f'Bearer {openai_api_key}',
            "OpenAi-Beta": "realtime=v1"}
    ) as openai_ws:
        await send_session_update(openai_ws)
        stream_sid = None


        async def receive_from_twilio():
            """ Receive audio data from twilio and send it to openai realtime api server."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event']== 'media':
                        audio_media = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_media))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print( f"Incoming stream has started {stream_sid}")
                
            except WebSocketDisconnect:
                print("Client disconnected")

        
        async def send_to_twilio():
            """ Receive events from openai and send audio back to twilio"""
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if response['type'] == "session.updated":
                        print("session updated sucessfully:", response)

                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        # Audio from OpenAI
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                'event': 'media',
                                'streamSid': stream_sid,
                                'media': {
                                    'payload': audio_payload
                                }
                            }

                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio_delta: {e}")
            except Exception as e:
                print(f"Error in sending audio to twilio: {e}")
        
    await asyncio.gather(receive_from_twilio(), send_to_twilio())


async def send_session_update(openai_ws):
    """Send session update to OpenAI WebSocket."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {'type':'server_vad'},
            "input_audio_format" : "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text","audio"],
            "temperature": 0.8
        }
    }
    print("sending session update:", json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)