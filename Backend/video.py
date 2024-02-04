import os
import uuid
import requests
import srt_equalizer
import assemblyai as aai

from typing import List
from moviepy.editor import *
from termcolor import colored
from dotenv import load_dotenv
from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip

load_dotenv("../.env")

ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")

def save_video(video_url: str, directory: str = "../temp") -> str:
    """
    Saves a video from a given URL and returns the path to the video.

    Args:
        video_url (str): The URL of the video to save.

    Returns:
        str: The path to the saved video.
    """
    video_id = uuid.uuid4()
    video_path = f"{directory}/{video_id}.mp4"
    with open(video_path, "wb") as f:
        f.write(requests.get(video_url).content)

    return video_path

def generate_subtitles(audio_path: str) -> str:
    """
    Generates subtitles from a given audio file and returns the path to the subtitles.

    Args:
        audio_path (str): The path to the audio file to generate subtitles from.

    Returns:
        str: The path to the generated subtitles.
    """
    def equalize_subtitles(srt_path: str, max_chars: int = 10) -> None:
      # Equalize subtitles
      srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)

    aai.settings.api_key = ASSEMBLY_AI_API_KEY

    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(audio_path)

    # Save subtitles
    subtitles_path = f"../subtitles/{uuid.uuid4()}.srt"

    subtitles = transcript.export_subtitles_srt()

    with open(subtitles_path, "w") as f:
        f.write(subtitles)

    # Equalize subtitles
    equalize_subtitles(subtitles_path)

    print(colored("[+] Subtitles generated.", "green"))

    return subtitles_path



def combine_videos(video_paths: List[str], max_duration: int) -> str:
    """
    Combines a list of videos into one video and returns the path to the combined video.

    Args:
        video_paths (list): A list of paths to the videos to combine.
        max_duration (int): The maximum duration of the combined video.

    Returns:
        str: The path to the combined video.
    """
    video_id = uuid.uuid4()
    combined_video_path = f"../temp/{video_id}.mp4"

    print(colored("[+] Combining videos...", "blue"))
    print(colored(f"[+] Each video will be {max_duration / len(video_paths)} seconds long.", "blue"))

    clips = []
    for video_path in video_paths:
        clip = VideoFileClip(video_path)
        clip = clip.without_audio()
        clip = clip.subclip(0, max_duration / len(video_paths))
        clip = clip.set_fps(30)

        # Not all videos are same size,
        # so we need to resize them
        clip = crop(clip, width=1080, height=1920, \
                    x_center=clip.w / 2, \
                        y_center=clip.h / 2)
        clip = clip.resize((1080, 1920))

        clips.append(clip)

    final_clip = concatenate_videoclips(clips)
    final_clip = final_clip.set_fps(30)
    final_clip.write_videofile(combined_video_path, threads=3)

    return combined_video_path

def generate_video(combined_video_path: str, tts_path: str, subtitles_path: str) -> str:
    """
    This function creates the final video, with subtitles and audio.

    Args:
        combined_video_path (str): The path to the combined video.
        tts_path (str): The path to the text-to-speech audio.
        subtitles_path (str): The path to the subtitles.

    Returns:
        str: The path to the final video.
    """
    # Make a generator that returns a TextClip when called with consecutive
    generator = lambda txt: TextClip(txt, font=f"../fonts/bold_font.ttf", fontsize=100, color="#FFFF00",
    stroke_color="black", stroke_width=5)

    # Burn the subtitles into the video
    subtitles = SubtitlesClip(subtitles_path, generator)
    result = CompositeVideoClip([
        VideoFileClip(combined_video_path),
        subtitles.set_pos(("center", "center"))
    ])

    # Add the audio
    audio = AudioFileClip(tts_path)
    result = result.set_audio(audio)
    
    # Create videos directory if it doesn't exist
    if not os.path.exists("../Frontend/public/videos"):
        os.makedirs("../Frontend/public/videos")

    filename = f"/public/videos/{uuid.uuid4()}.mp4"
    result.write_videofile(f"../Frontend{filename}", threads=3)

    return filename
