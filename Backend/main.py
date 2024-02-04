import os
import random
from gpt import *
from video import *
from utils import *
from search import *
from uuid import uuid4
from tiktokvoice import tts as tiktok_tts
from elevenvoice import tts as eleven_tts
from flask_cors import CORS
from termcolor import colored
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from moviepy.config import change_settings

load_dotenv("../.env")

SESSION_ID = os.getenv("TIKTOK_SESSION_ID")

change_settings({"IMAGEMAGICK_BINARY": os.getenv("IMAGEMAGICK_BINARY")})

app = Flask(__name__)
CORS(app)

HOST = "0.0.0.0"
PORT = 8080
AMOUNT_OF_STOCK_VIDEOS = 5


# Generation Endpoint
@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        # Clean
        clean_dir("../temp/")
        clean_dir("../subtitles/")

        # Parse JSON
        data = request.get_json()

        # Print little information about the video which is to be generated
        print(colored("[Video to be generated]", "blue"))
        print(colored("   Subject: " + data["videoSubject"], "blue"))
        print(colored("   Voice: " + data["voice"], "blue"))
        
        # Get voice
        eleven_voices = ["Paddington", "DanDan", "Sally", "Aaryan", "Eleguar", "Readwell", "Knightley"]
        eleven_voice = data["voice"]
        if eleven_voice not in eleven_voices:
            print(colored("[-] Invalid voice.", "red"))
            return jsonify(
                {
                    "status": "error",
                    "message": "Invalid voice.",
                    "data": [],
                }
            )

        # Generate a script
        script = generate_script(data["videoSubject"])
        
        # Remove *, #, and other special characters from the script
        script = remove_special_characters(script)

        # Generate search terms
        search_terms = get_search_terms(
            data["videoSubject"], AMOUNT_OF_STOCK_VIDEOS, script
        )

        # Search for a video of the given search term
        video_urls = []

        # Loop through all search terms,
        # and search for a video of the given search term
        for search_term in search_terms:
            found_url = search_for_stock_videos(
                search_term, os.getenv("PEXELS_API_KEY")
            )

            if found_url != None and found_url not in video_urls and found_url != "":
                video_urls.append(found_url)

        # Define video_paths
        video_paths = []

        # Let user know
        print(colored("[+] Downloading videos...", "blue"))

        # Save the videos
        for video_url in video_urls:
            try:
                saved_video_path = save_video(video_url)
                video_paths.append(saved_video_path)
            except:
                print(colored("[-] Could not download video: " + video_url, "red"))

        # Let user know
        print(colored("[+] Videos downloaded!", "green"))

        # Let user know
        print(colored("[+] Script generated!\n\n", "green"))

        print(colored(f"\t{script}", "light_cyan"))

        # Split script into sentences
        sentences = script.split(". ")
        # Remove empty strings
        sentences = list(filter(lambda x: x != "", sentences))
        paths = []
        # Generate TTS for every sentence
        for sentence in sentences:
            current_tts_path = f"../temp/{uuid4()}.mp3"
            
            eleven_tts(sentence, 
                        voice=eleven_voice,
                       filename=current_tts_path)
            
            # tiktok_tts(sentence,
            #            voice="en_us_006",
            #            filename=current_tts_path)
            
            audio_clip = AudioFileClip(current_tts_path)
            paths.append(audio_clip)
            

        # Combine all TTS files using moviepy
        final_audio = concatenate_audioclips(paths)
        tts_path = f"../temp/{uuid4()}.mp3"
        final_audio.write_audiofile(tts_path)
        audio_clip.close()

        # Generate subtitles
        subtitles_path = generate_subtitles(tts_path)

        # Concatenate videos
        temp_audio = AudioFileClip(tts_path)
        combined_video_path = combine_videos(video_paths, temp_audio.duration)
        temp_audio.close()
        
        # Put everything together
        final_video_path = generate_video(combined_video_path, tts_path, subtitles_path)

        # Let user know
        print(colored("[+] Video generated!", "green"))

        print(colored(f"[+] Path: {final_video_path}", "green"))

        # Return JSON
        return jsonify(
            {
                "status": "success",
                "message": "Video generated!",
                "videoUrl": final_video_path,
            }
        )
    except Exception as err:
        print(colored("[-] Error: " + str(err), "red"))
        return jsonify(
            {
                "status": "error",
                "message": f"Could not generate video: {str(err)}",
                "videoUrl": [],
            }
        )
        
    
def remove_special_characters(script: str) -> str:
    """
    Remove special characters from a script.

    Args:
        script (str): The script to clean.

    Returns:
        str: The cleaned script.
    """
    return script.replace("*", "").replace("#", "")

if __name__ == "__main__":
    app.run(debug=True, host=HOST, port=PORT)
