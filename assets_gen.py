import os
import openai
import json
import random
import requests
from dotenv import load_dotenv
from google.cloud import texttospeech as tts

load_dotenv()

openai.organization = os.getenv("OPENAI_ORGANIZATION_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set up TTS client
tts_client = tts.TextToSpeechClient()

def get_random_string(length):
    letters = "abcdefghijklmnopqrstuvwxyz1234567890"
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def video_setup():
    # Generate video ID
    video_id = get_random_string(15)
    # Save output
    if not os.path.exists("videos/" + video_id):
        os.makedirs("videos/" + video_id)
    else:
        video_id = get_random_string(20)

    # Use loop instead
    for i in range(1, 4):
        os.makedirs("videos/" + video_id + "/p" + str(i) + "/img")
        with open("videos/" + video_id + "/p" + str(i) + "/img/tags.json", "w") as f:
            f.write("[]")

    return video_id


def get_video_script(topic, video_id):
    # Prompt
    prompt = '''
        You are a video script generation machine. I give you a topic and you create 3 paragraphs of video script with an intro and an outro. You should output only in JSON format and separate each paragraph in with a different key "P1", "P2", "P3".  You should also include strings in [] where you should include tags for an image that you find reasonable to display in that moment in time. There should be 10 tags minimum in each such as ["black coat", "dressing room", "wardrobe", "HD", "man"... ]. Make sure to include a variety of these tags in different points in time so that the article images correspond and are abundant.
        Here's a sample of what I'm looking for:
        {
        "P1": "PARGRAPH 1",
        "P2": "PARGRAPH 2",
        "P3": "PARGRAPH 2",
        "p1_img_tags": [...],
        "p2_img_tags": [...],
        "p3_img_tags": [...],
        "outro_img_tags": [...]
        }

        Please stick to the format above. Paragraphs are only text and tags are only strings in []. You can't use special characters.
    '''
    # Completion
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt + "\n Topic: " + topic + "\n",
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


def get_tts_audio(video_id):
    # Voice options
    voices = ["en-GB-Neural2-A", "en-GB-Neural2-B", "en-GB-Neural2-D", "en-GB-Neural2-F"]
    # Read script
    with open("videos/" + video_id + "/script.json", "r") as f:
        script = json.loads(f.read())

    # Get random voice
    voice = random.choice(voices)

    for i in range(1, 4):
        # Generate audio
        synthesis_input = tts.SynthesisInput(ssml="<speak>" + script["P" + str(i)] + "</speak>")
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


def get_stock_assets(video_id):
    # Read tags from script.json
    with open("videos/" + video_id + "/script.json", "r") as f:
        script = json.loads(f.read())

    # Get P1 tags
    p1_tags = script["p1_img_tags"]
    # Get P2 tags
    p2_tags = script["p2_img_tags"]
    # Get P3 tags
    p3_tags = script["p3_img_tags"]
    # Get outro tags
    outro_tags = script["outro_img_tags"]


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
    # get_stock_assets(video_id)
