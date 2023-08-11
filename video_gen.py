'''
    video_gen.py

    - This script generates the video from the assets we got from Pexels API and the TTS audio (script, audio, images, videos)

    Author: Juled Zaganjori    
'''

from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips, vfx
import os
import json
import requests
import random
import proglog
import librosa
from tabulate import tabulate
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
    return librosa.get_duration(path=audio_path)


def calculate_video_length(audio_lengths):
    total_length = 0
    for audio_length in audio_lengths:
        total_length += audio_length
    return total_length


# Create the video segments
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

        audio_path = os.path.join(paragraph, "audio.wav")
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
            print("Remaining Video Length:", remaining_video_length)

            # Exit the loop if there is no time remaining
            if remaining_video_length <= audio_length:
                break

        # Subtract the audio duration from the remaining video length
        remaining_video_length -= audio_length
        print("Remaining Video Length after Audio:", remaining_video_length)

        # Exit the loop if there is no time remaining
        if remaining_video_length <= audio_length:
            break

    return video_segments


# Movipy animations
def zoom_in(image_clip):
    return image_clip.fx(vfx.zoom, 1.5, 1.5)


# Animate the video segments
def animate_video_segments(video_segments):
    pass


# Create the video from the video segments
def render_video(video_id, video_segments, audios):
    # Extract the video clips
    videos = [video_segment[0] for video_segment in video_segments]

    # Concatenate the video clips
    video = concatenate_videoclips(videos)

    # Calculate the total duration of the video segments
    total_video_duration = sum([video_segment[2] for video_segment in video_segments])

    # Trim or extend the video duration to match the audio duration
    audio_duration = sum([audio.duration for audio in audios])
    if total_video_duration < audio_duration:
        # Extend the video duration by looping it
        video = video.fx(vfx.loop, duration=audio_duration)
    elif total_video_duration > audio_duration:
        # Trim the video duration to match the audio duration
        video = video.subclip(0, audio_duration)

    # Concatenate the audio clips
    audio = concatenate_audioclips(audios)

    # Set the audio for the video
    video = video.set_audio(audio)

    # Resize the video
    video = video.resize(video_size)

    # Write the video file
    video.write_videofile(
        os.path.join("videos", video_id, "video.mp4"),
        fps=video_fps,
        logger=proglog.TqdmProgressBarLogger(print_messages=False)
    )
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
            "videos", video_id, "p" + str(i), "audio.wav"))

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
            "videos", video_id, "p" + str(i), "audio.wav"))

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
