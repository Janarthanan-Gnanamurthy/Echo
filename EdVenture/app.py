from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import asyncio
from pathlib import Path
import json
import requests

from api_get_tts import get_tts
from movie import movie_pro

import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate
from moviepy.video.fx.all import speedx
from moviepy.audio.fx.all import volumex, audio_fadein, audio_fadeout


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory='templates')

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse('index.html',{'request': request} )

@app.post('/home/{name}', response_class=HTMLResponse)
def root(name, request : Request):
    video_path = f'../static/video/{name}.mp4'

    return templates.TemplateResponse('home.html', {'request': request, 'video_path':video_path, 'name': name})

@app.post('/upload-video', response_class=RedirectResponse)
async def upload_video(video: UploadFile = File(...)):
    #name = Path(video.filename).name
    name='test_1'
    with open(f"static/video/{name}.mp4", "wb") as f:
        f.write(video.file.read())
    
    print('\n <video successfully uploaded> \n')

    extract_audio(name)

    #whisper_ai(name)

    return RedirectResponse(f'/home/{name}')

@app.post('/extract-audio/{name}')
def extract_audio(name):
    video = VideoFileClip(f'static/video/{name}.mp4')
    audio = video.audio
    audio.write_audiofile(f'static/audio/{name}.mp3')
    print('\n <audio extracted successfully> \n')

    return {'message':'success'}

@app.post("/whisper")
async def whisper_ai(request: Request):
    obj = await request.json()
    name = obj['name']
    voice_id = obj['id']

    model = whisper.load_model("small")
    result=model.transcribe(f'static/audio/{name}.mp3', task='translate')
    print('<Whisper executed successfully>')  
    segments=result['segments']
    
    i=0
    for segment in segments:
        i+=1
        x=str(i)
        seg_name=f'{name}_v{x}'

        '''text=segment['text']
        start=segment['start']
        end=segment['end']'''

        task= asyncio.create_task(tts(seg_name, segment['text'], voice_id))
        await task
    
    final_video_clips = []
    j=0
    for segment in segments:
        j += 1
        x = str(j)
        seg_name = f'{name}_v{x}'

        start = segment['start']
        end = segment['end']

        video_clip = VideoFileClip(f'static/video/{name}.mp4').subclip(start, end)
        adjusted_audio = AudioFileClip(f'static/tts/{seg_name}.mp3')
        
        # Calculate speed factor to adjust the video playback speed
        speed_factor = video_clip.duration /adjusted_audio.duration
        
        # Adjust the playback speed of the video clip
        adjusted_video_clip = video_clip.speedx(speed_factor)
        
        # Set the synchronized audio using the adjusted audio
        final_video_clip = adjusted_video_clip.set_audio(adjusted_audio)
        final_video_clips.append(final_video_clip)
    
    final_output_video = concatenate(final_video_clips, method="compose")
    final_output_video.write_videofile(f'static/output/{name}.mp4')

    return segments

@app.post('/tts/api')
async def tts_api(request: Request):
    obj = await request.json()
    name = obj['name']
    text = obj['text']
    id = obj['id']
    task= asyncio.create_task(tts(name, text, id))
    await task

    return 'success API'

@app.post('/tts')
async def tts(name, text, id):
    
    url = "https://play.ht/api/v2/tts"

    payload = {
        "text": text,
        "voice": id,
        "quality": "medium",
        "output_format": "mp3",
        "speed": 1,
        "sample_rate": 24000,
        "seed": None,
        "temperature": None
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer adfd5353bc934ff8b1223405604de8ea",
        "X-USER-ID": "WEkXcBCd5WNQiZv4QspWnEyBocT2"
    }

    response = requests.post(url, json=payload, headers=headers)

    json_obj = json.loads(response.text)
    link=json_obj['_links'][2]['href']

    #print(json_obj)

    get_tts(link, name)

    return "success"

@app.post('/clone-voice/{voice_name}/{name}')
def voice_clone(name, voice_name):
    url = "https://play.ht/api/v2/cloned-voices/instant"

    files = { "sample_file": (f"{name}.mp3", open(f"static/audio/{name}.mp3", "rb"), "audio/mpeg") }
    payload = { "voice_name": f"{voice_name}" }
    headers = {
        "accept": "application/json",
        "AUTHORIZATION": "Bearer adfd5353bc934ff8b1223405604de8ea",
        "X-USER-ID": "WEkXcBCd5WNQiZv4QspWnEyBocT2"
    }

    response = requests.post(url, data=payload, files=files, headers=headers)
    json_obj=json.loads(response.text)

    voice_id=str(json_obj['id'])

    print(response.text)
    print('\n <Voice cloned successfully> \n')

    return voice_id

@app.post('/del-voice/')
async def delete_voice(request : Request):
    obj = await request.json()
    print(obj)

    url = "https://play.ht/api/v2/cloned-voices/"

    payload = { "voice_id": obj}
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": "Bearer adfd5353bc934ff8b1223405604de8ea",
        "X-USER-ID": "WEkXcBCd5WNQiZv4QspWnEyBocT2"
    }

    response = requests.delete(url, json=payload, headers=headers)

    print(response.text)
    print('\n <voice deleted successfully> \n')
    return '<voice deleted successfully>'







