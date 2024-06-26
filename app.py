from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google.cloud import speech
import io
import subprocess
import asyncio
from aiohttp import web
from aiohttp_wsgi import WSGIHandler

RATE = 48000
CHUNK = int(RATE / 10)

load_dotenv()

app = Flask('aioflask')

language_code = "en-US"  # a BCP-47 language tag

client = speech.SpeechClient()
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    sample_rate_hertz=RATE,
    language_code=language_code,
    max_alternatives=1,
    model="default"
)

streaming_config = speech.StreamingRecognitionConfig(
    config=config, interim_results=True
)

async def STT(audio_content):
    try:
        stream = io.BytesIO(audio_content)

        requests = (
            speech.StreamingRecognizeRequest(audio_content=chunk)
            for chunk in iter(lambda: stream.read(RATE), b'')

        )

        responses = client.streaming_recognize(
            streaming_config, requests
        )
        # print("Response:", [response for response in responses])
        # print("1")

        for response in responses:
            # print(response)
            for result in response.results:
                # print(result)
                print(f'Transcript: {result.alternatives[0].transcript}')
                # Here you can send the transcript back to the client or process it further
                return result.alternatives[0].transcript
    except Exception as e:
        print(f"Error: {e}")

from pydub import AudioSegment
import io

class OpusToLinearConverter:
    def __init__(self):
        self.ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'webm',            # input format
            '-i', '-',               # read from stdin
            '-f', 's16le',           # output format: signed 16-bit PCM little-endian
            '-acodec', 'pcm_s16le',  # audio codec
            '-ar', '16000',          # sample rate: 16kHz (adjust as needed)
            '-ac', '1',              # channels: mono (adjust as needed)
            '-'                      # output to stdout
        ]
        self.ffmpeg_process = None
    
    def convert_opus_to_linear16(self, opus_bytes):
        # Restart ffmpeg process for each new conversion
        self.ffmpeg_process = subprocess.Popen(self.ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Run ffmpeg command and capture stdout
        stdout, stderr = self.ffmpeg_process.communicate(input=opus_bytes)
        
        # Check for errors
        if self.ffmpeg_process.returncode != 0:
            print(f'ffmpeg error: {stderr.decode()}')
            return None
        
        # Return the converted audio data
        return stdout


@app.route('/')
def index():
    return render_template('index.html')

async def socket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request) 
    converter = OpusToLinearConverter()

    i = 0
    while i < 2:
        response = await ws.receive()
        # print(response)
        # print(response.data)
        # break
        # with open(f'test{i}.webm', 'wb') as f:
        #     f.write(response.data)
        #     i += 1
        # linear16_bytes = converter.convert_opus_to_linear16(response.data)
        transcription = await STT(response.data)
        await ws.send_str(str(transcription) if transcription else "")
        

  

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    aio_app = web.Application()
    wsgi = WSGIHandler(app)
    aio_app.router.add_route('*', '/{path_info: *}', wsgi.handle_request)
    aio_app.router.add_route('GET', '/listen', socket)
    web.run_app(aio_app, port=5555)
    # app.run(port=5555, debug=True)