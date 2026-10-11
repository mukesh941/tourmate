import asyncio
from app.services.ai_service import generate_tts_audio

async def test_tts():
    print("Testing English TTS (Should fall back to None/browser)")
    en_audio = await generate_tts_audio("Hello world", "en-US")
    print(f"English audio bytes: {len(en_audio) if en_audio else 'None'}")
    
    print("Testing Hindi TTS (Should use Piper)")
    hi_audio = await generate_tts_audio("नमस्ते दुनिया", "hi-IN")
    print(f"Hindi audio bytes: {len(hi_audio) if hi_audio else 'None'}")
    
    if hi_audio:
        with open("test_hindi.wav", "wb") as f:
            f.write(hi_audio)
        print("Saved test_hindi.wav")

if __name__ == "__main__":
    asyncio.run(test_tts())
