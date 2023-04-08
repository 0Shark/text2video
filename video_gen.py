'''
    video_gen.py

    - This script generates the video from the assets we got from Pexels API and the TTS audio (script, audio, images, videos)

    Author: Juled Zaganjori    
'''

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
import os
import json
import requests
import random
import proglog
from tabulate import tabulate
from mutagen.mp3 import MP3
from assets_gen import min_stock_video_length, min_stock_image_length, max_stock_video_length, max_stock_image_length, max_paragraphs, orientation, asset_size

# Global variables
video_fps = 30
audio_fps = 44100
video_width = 1920
video_height = 1080
video_size = (video_width, video_height)


def get_image_clip(image_path, duration):
    return ImageClip(image_path).set_duration(duration)


def get_video_clip(video_path, duration):
    return VideoFileClip(video_path).set_duration(duration)


def get_audio_clip(audio_path):
    return AudioFileClip(audio_path)


def get_audio_length(audio_path):
    audio = MP3(audio_path)
    return audio.info.length


def calculate_video_length(audio_lengths):
    total_length = 0
    for audio_length in audio_lengths:
        total_length += audio_length
    return total_length

# Create video segments will create a table of path and duration for each video segment that will be random.
# The paths should be unique and the duration should be random and should not exceed the total video length.
# Videos have a minimum length of min_stock_video_length and images have a minimum length of min_stock_image_length.
# Videos have a maximum length of max_stock_video_length and images have a maximum length of max_stock_image_length.
# The total duration in the table should not exceed the total video length.
# Start from the first paragraph and go to the last paragraph. Don't use paragraph 2 assets for paragraph 1 and such.
# Create an algorithm that will calculate the duration needed for each segment so that the total duration is equal to the total video length.
# The algorithm should also make sure that the duration of each segment is not larger than the actual duration of the asset.


def create_video_segments(video_id, total_video_length):
    # Get the path for the assets of each paragraph
    paragraphs_path = os.path.join("videos", video_id)
    paragraphs = [f.path for f in os.scandir(paragraphs_path) if f.is_dir()]

    video_segments = []

    # Initialize the remaining video length to be the total video length
    remaining_video_length = total_video_length

    for paragraph in paragraphs:
        assets = [f.path for f in os.scandir(
            os.path.join(paragraph, "img")) if f.is_file()]
        assets += [f.path for f in os.scandir(
            os.path.join(paragraph, "video")) if f.is_file()]

        audio_path = os.path.join(paragraph, "audio.mp3")
        audio_length = get_audio_length(audio_path)

        # maximum available duration
        available_duration = min(remaining_video_length, audio_length)
        # maximum number of assets
        max_assets = min(len(assets), max_paragraphs)
        # Calculate the maximum available duration for each asset
        max_duration_per_asset = min_stock_image_length
        if max_assets > 1:
            max_duration_per_asset = min(
                available_duration / max_assets, max_stock_image_length)

        # Shuffle the assets
        random.shuffle(assets)
        selected_assets = assets[:max_assets]

        # Generate video segments for each asset
        for asset_path in selected_assets:
            if os.path.splitext(asset_path)[1] == ".jpg":
                asset_duration = random.uniform(
                    min_stock_image_length, max_duration_per_asset)
                video_segments.append([
                    get_image_clip(asset_path, asset_duration), asset_path, asset_duration, "image"])
            else:
                asset_duration = random.uniform(
                    min_stock_video_length, max_duration_per_asset)
                video_segments.append([
                    get_video_clip(asset_path, asset_duration), asset_path, asset_duration, "video"])

            # Subtract the asset duration from the remaining video length
            remaining_video_length -= asset_duration

            # Exit the loop if there is no time remaining
            if remaining_video_length <= 0:
                break

        # Subtract the audio duration from the remaining video length
        remaining_video_length -= audio_length

        # Exit the loop if there is no time remaining
        if remaining_video_length <= 0:
            break

    return video_segments


# Create the video from the video segments
def render_video(video_id, video_segments, audios):
    videos = [video_segment[0] for video_segment in video_segments]

    video = concatenate_videoclips(videos)
    audio = concatenate_audioclips(audios)

    video = video.set_audio(audio)
    # Resize
    video = video.resize(video_size)
    # Write
    video.write_videofile(os.path.join("videos", video_id, "video.mp4"),
                          fps=video_fps, logger=proglog.TqdmProgressBarLogger(print_messages=False))
    video.close()


def display_segments_stats(video_segments, total_video_length):
    print("\n")
    print(tabulate(video_segments, headers=[
        "Video Segment", "Path", "Duration", "Type"]))
    print("\nTotal Video Length: " +
          str(total_video_length) + " seconds")
    
    # Print the image to video ratio
    images = [video_segment for video_segment in video_segments if video_segment[3] == "image"]
    videos = [video_segment for video_segment in video_segments if video_segment[3] == "video"]
    print("\nImage percentage: " + str(len(images) / len(video_segments) * 100) + "%")
    print("Video percentage: " + str(len(videos) / len(video_segments) * 100) + "%")


def video_gen(video_id):
    # Get audio paths
    audio_paths = []
    for i in range(0, max_paragraphs):
        audio_paths.append(os.path.join(
            "videos", video_id, "p" + str(i), "audio.mp3"))

    # Get audio clips
    audios = []
    for audio_path in audio_paths:
        audios.append(get_audio_clip(audio_path))

    # Get audio lengths
    audio_lengths = []
    for audio_path in audio_paths:
        audio_lengths.append(get_audio_length(audio_path))

    # Calculate the total video length
    total_video_length = calculate_video_length(audio_lengths)

    # Create the video segments
    video_segments = create_video_segments(video_id, total_video_length)

    display_segments_stats(video_segments, total_video_length)

    readyToRender = False
    while not readyToRender:
        readyToRender = input(
            "Are you ready to render the video with this segment configuration? (y/n) ") == "y"
        if not readyToRender:
            video_segments = create_video_segments(
                video_id, total_video_length)
            display_segments_stats(video_segments)

    # Create the video
    render_video(video_id, video_segments, audios)

    print("Video generated successfully!")

    return os.path.join("videos", video_id, "video.mp4")


# Direct run
if __name__ == "__main__":
    # Get the video id
    video_id = input("Enter the video id: ")

    # Get audio paths
    audio_paths = []
    for i in range(0, max_paragraphs):
        audio_paths.append(os.path.join(
            "videos", video_id, "p" + str(i), "audio.mp3"))

    # Get audio clips
    audios = []
    for audio_path in audio_paths:
        audios.append(get_audio_clip(audio_path))

    # Get audio lengths
    audio_lengths = []
    for audio_path in audio_paths:
        audio_lengths.append(get_audio_length(audio_path))

    # Calculate the total video length
    total_video_length = calculate_video_length(audio_lengths)

    # Create the video segments
    video_segments = create_video_segments(video_id, total_video_length)

    display_segments_stats(video_segments)

    readyToRender = False
    while not readyToRender:
        readyToRender = input(
            "Are you ready to render the video with this segment configuration? (y/n) ") == "y"
        if not readyToRender:
            video_segments = create_video_segments(
                video_id, total_video_length)
            display_segments_stats(video_segments)

    # Create the video
    render_video(video_id, video_segments, audios)
