'''
    assets_gen.py

    - This script generates the assets for the video (script, audio, images, videos)

    Author: Juled Zaganjori    
'''

import os
import openai
import json
import random
import requests
from dotenv import load_dotenv
from mutagen.mp3 import MP3
from google.cloud import texttospeech as tts

load_dotenv()

openai.organization = os.getenv("OPENAI_ORGANIZATION_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up TTS client
tts_client = tts.TextToSpeechClient()

# Global variables
min_stock_video_length = 5  # seconds
min_stock_image_length = 3  # seconds
max_stock_video_length = 10  # seconds
max_stock_image_length = 5  # seconds
max_paragraphs = 3
orientation = "landscape"
asset_size = "medium"

# Generate random string
def get_random_string(length):
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


# Setup video directory
def video_setup():
    global max_paragraphs
    # Generate video ID
    video_id = get_random_string(15)
    if not os.path.exists("videos"):
        os.makedirs("videos")
    # Save output
    if not os.path.exists("videos/" + video_id):
        os.makedirs("videos/" + video_id)
    else:
        video_id = get_random_string(20)

    for i in range(0, max_paragraphs):
        os.makedirs("videos/" + video_id + "/p" + str(i) + "/img")
    
    for i in range(0, max_paragraphs):
        os.makedirs("videos/" + video_id + "/p" + str(i) + "/video")

    return video_id


# Video script from OpenAI
def get_video_script(topic, video_id):
    global max_paragraphs

    # Prompt
    prompt = '''
        You are a video script generation machine. I give you a topic and you create 3 paragraphs of video script with an intro and an outro. You should output only in JSON format and separate each paragraph in with a different key "P1", "P2", "P3".  You should also include strings in [] where you should include tags for an image that you find reasonable to display in that moment in time. There should be 10 tags minimum in each such as ["black coat", "dressing room", "wardrobe", "HD", "man"... ]. Make sure to include a variety of these tags in different points in time so that the article images correspond and are abundant.
        Please stick to the format. Paragraphs are only text and tags are only strings in []. You can't use special characters. DON'T ADD ANYTHING ELSE TO THE RESPONSE. ONLY THE JSON FORMAT BELOW.
        Here's a sample of what I'm looking for:
        {
            "topic": " '''+topic+''' ",
    '''

    # Create a prompt sample as the one above but as many max_paragraphs value
    for i in range(0, max_paragraphs):
        prompt += '''
                "p''' + str(i) + '''": "paragraph text",
                "p''' + str(i) + '''_img_tags": [...],
        '''

    prompt += '''
        }
    '''

    # Completion
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt + "\n"+"Topic: " + topic,
        temperature=0.5,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    # Validate output
    try:
        json.loads(response.choices[0].text)
        with open("videos/" + video_id + "/script.json", "w") as f:
            f.write(response.choices[0].text)

        return True

    except ValueError:
        return False


# TTS audio from Google Cloud
def get_tts_audio(video_id):
    global max_paragraphs
    # Voice options
    voices = ["en-GB-Neural2-A", "en-GB-Neural2-B",
              "en-GB-Neural2-D", "en-GB-Neural2-F"]
    # Read script
    with open("videos/" + video_id + "/script.json", "r") as f:
        script = json.loads(f.read())

    # Get random voice
    voice = random.choice(voices)

    for i in range(0, max_paragraphs):
        # Generate audio
        synthesis_input = tts.SynthesisInput(
            ssml="<speak>" + script["p" + str(i)] + "</speak>")
        voice_params = tts.VoiceSelectionParams(
            language_code="en-GB",
            name=voice
        )
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3
        )

        # Get audio
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        # Save audio to file
        with open("videos/" + video_id + "/p" + str(i) + "/audio.mp3", "wb") as out:
            out.write(response.audio_content)

    return True


# Photo and video assets
def get_stock_images(video_id, part_number, part_tags, image_count, orientation, asset_size):
    api_key = os.getenv("PEXELS_API_KEY")
    # Perform search with the tags joined by a + sign
    response = requests.get("https://api.pexels.com/v1/search?query=" + "+".join(part_tags) + "&per_page=" +
                            str(image_count) + "&orientation=" + orientation + "&size=" + str(asset_size),
                            headers={"Authorization": api_key})
    # Get images
    images = response.json()["photos"]
    # Get image URLs
    image_urls = [image["src"]["original"] for image in images]
    # Download images
    for i in range(0, len(image_urls)):
        # Get image
        image = requests.get(image_urls[i])
        # Save image
        with open("videos/" + video_id + "/p" + str(part_number) + "/img/" + str(i) + ".jpg", "wb") as f:
            f.write(image.content)


def get_stock_videos(video_id, part_number, part_tags, video_count, orientation, asset_size):

    api_key = os.getenv("PEXELS_API_KEY")

    response = requests.get("https://api.pexels.com/videos/search?query=" + "+".join(
        part_tags) + "&orientation=" + orientation + "&size=" + str(asset_size) + "&per_page=" + str(video_count),
        headers={"Authorization": api_key})
    # Get videos
    videos = response.json()["videos"]
    
    # Get video URLs
    video_urls = [video["video_files"][0]["link"] for video in videos]

    # Download videos
    for i in range(0, video_count):
        # Get video
        video = requests.get(video_urls[i])
        # Save video
        with open("videos/" + video_id + "/p" + str(part_number) + "/video/" + str(i) + ".mp4", "wb") as f:
            f.write(video.content)


# Setup stock assets
def get_part_stock_assets(video_id, part_num, part_len):
    global orientation, asset_size

    # Read tags from script.json
    with open("videos/" + video_id + "/script.json", "r") as f:
        script = json.loads(f.read())

    # Get tags
    part_tags = script["p" + str(part_num) + "_img_tags"]

    img_count = int(part_len / min_stock_image_length)
    video_count = int(part_len / min_stock_video_length)

    get_stock_images(video_id, part_num, part_tags, img_count, orientation, asset_size)
    get_stock_videos(video_id, part_num, part_tags, video_count, orientation, asset_size)


def get_stock_assets(video_id):
    global max_paragraphs
    # Read script.json
    with open("videos/" + video_id + "/script.json", "r") as f:
        script = json.loads(f.read())

    # Calculate part lengths from the audios
    part_lengths = []
    for i in range(0, max_paragraphs):
        # Get audio length
        audio = MP3("videos/" + video_id + "/p" + str(i) + "/audio.mp3")
        audio_length = audio.info.length
        part_lengths.append(audio_length)

    # Get stock assets for each part
    for i in range(0, len(part_lengths)):
        get_part_stock_assets(video_id, i, part_lengths[i])

    return True


def assets_gen(topic, custom_orientation="landscape", custom_asset_size="medium"):
    global orientation, asset_size
    orientation = custom_orientation
    asset_size = custom_asset_size

    # Setup video
    video_id = video_setup()
    # Get video script
    if get_video_script(topic, video_id):
        print("Video script generated!")
    else:
        print("Video script generation failed!")
    # Get TTS audio
    if get_tts_audio(video_id):
        print("TTS audio generated!")
    else:
        print("TTS audio generation failed!")
    # Get stock assets
    if get_stock_assets(video_id):
        print("Stock assets generated!")
    else:
        print("Stock assets generation failed!")

    return video_id


if __name__ == "__main__":
    # Get topic
    topic = input("Enter a topic: ")
    # Setup video
    video_id = video_setup()
    # Get video script
    if get_video_script(topic, video_id):
        print("Video script generated!")
    else:
        print("Video script generation failed!")
    # Get TTS audio
    if get_tts_audio(video_id):
        print("TTS audio generated!")
    else:
        print("TTS audio generation failed!")
    # Get stock assets
    if get_stock_assets(video_id):
        print("Stock assets generated!")
    else:
        print("Stock assets generation failed!")
