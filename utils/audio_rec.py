import asyncio
from shazamio import Shazam

async def recognize_audio(file_path):
    shazam = Shazam()
    out = await shazam.recognize(file_path)
    if 'track' in out:
        title = out['track']['title']
        subtitle = out['track']['subtitle']
        return f"{title} - {subtitle}"
    return None

def run_audio_recognition(file_path):
    # 在同步的 Streamlit 環境中執行非步函數
    return asyncio.run(recognize_audio(file_path))