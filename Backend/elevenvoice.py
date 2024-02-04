import os
from dotenv import load_dotenv
import time
import elevenlabs
from elevenlabs import generate, play, voices, Voice, set_api_key

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
set_api_key(API_KEY)

def tts(
    text: str,
    voice: str = "none",
    filename: str = "output.mp3"
):
    # Get voice id from the provided list
    voices_list = ["Paddington", "DanDan", "Sally", "Aaryan", "Eleguar", "Readwell", "Knightley"]
    if voice not in voices_list:
        print("Invalid voice id. Please choose from:", voices_list)
        return

    # Find the corresponding voice object
    voice_obj = next((v for v in voices() if v.name == voice), None)
    if not voice_obj:
        print("Voice not found.")
        return

    retry_count = 50  # Number of retries
    while retry_count > 0:
        try:
            print(f'Generating audio for {voice}... {text}')
            audio = generate(text=text, voice=voice_obj, model="eleven_multilingual_v1")
            output_path = os.path.join(filename)
            
            with open(output_path, 'wb') as f:
                f.write(audio)
            print(f"Audio saved to {output_path}")
            break  # Break out of the retry loop if successful
        except elevenlabs.api.error.APIError as e:
            print(f"Error: {e}")
            print("Retrying...")
            time.sleep(5)  # Add a delay before retrying
            retry_count -= 1
            if retry_count == 0:
                print("Maximum retries reached. Skipping this message.")
                break
