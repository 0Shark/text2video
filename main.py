import pyfiglet
from os import startfile
from assets_gen import assets_gen
from video_gen import video_gen

# Welcome message
ascii_banner = pyfiglet.figlet_format("Text2Video")
print(ascii_banner)
print("""
Version: 0.1

Welcome to Text2Video!
You just need to enter a topic and the program will generate a video for you.

Developed by: Juled Zaganjori
""")

# Get topic
topic = input("Enter a topic: ")

# Generate assets
video_id = assets_gen(topic)

# Generate video
video_path = video_gen(video_id)

# Display video
startfile(video_path)