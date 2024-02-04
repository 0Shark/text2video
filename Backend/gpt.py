import re
import g4f
import json

from typing import List
from termcolor import colored

def generate_script(video_subject: str) -> str:
    """
    Generate a script for a video, depending on the subject of the video.

    Args:
        video_subject (str): The subject of the video.

    Returns:
        str: The script for the video.
    """

    # Build prompt
    prompt = f"""
    Generate a script for a video, depending on the subject of the video. The video has to be short and straight to the point.
    Similar to a TikTok video or a Instagram Reel.
    
    Subject: {video_subject}

    The script is to be returned as a string, no markdown or anything else. NEVER use any special characters like **, #, etc or any links or emojis.

    Here is an example of a string:
    "This is an example string."

    Do not under any circumstance refernce this prompt in your response.

    Get straight to the point, don't start with unnecessary things like, "welcome to this video".

    Obviously, the script should be related to the subject of the video.

    ONLY RETURN THE RAW SCRIPT. DO NOT RETURN ANYTHING ELSE. NO MARKDOWN, NO LINKS, NO EMOJIS OR SPECIAL CHARACTERS OR ELSE YOUR RESPONSE WILL BE REJECTED AND YOU WILL BE BANNED.
    """

    # Generate script
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_35_turbo_16k_0613,
        messages=[{"role": "user", "content": prompt}],
    )

    print(colored(response, "cyan"))

    # Return the generated script
    if response:
        return response + " "
    else:
        print(colored("[-] GPT returned an empty response.", "red"))
        return None

def get_search_terms(video_subject: str, amount: int, script: str) -> List[str]:
    """
    Generate a JSON-Array of search terms for stock videos,
    depending on the subject of a video.

    Args:
        video_subject (str): The subject of the video.
        amount (int): The amount of search terms to generate.
        script (str): The script of the video.

    Returns:
        List[str]: The search terms for the video subject.
    """
    
    # Build prompt
    prompt = f"""
    Generate {amount} search terms for stock videos,
    depending on the subject of a video. Only stick to the subject of the video and don't go off-topic.
    For example, if the video is about "How to make a cake", the search terms should be "cake", "baking", "cooking", etc.
    They need to be single words or short phrases.
    Subject: {video_subject}

    The search terms are to be returned as
    a JSON-Array of strings.

    Each search term should consist of 1-3 words, 
    always add the main subject of the video.

    Here is an example of a JSON-Array of strings:
    ["search term 1", "search term 2", "search term 3"]

    Obviously, the search terms should be related
    to the subject of the video.

    ONLY RETURN THE JSON-ARRAY OF STRINGS.
    DO NOT RETURN ANYTHING ELSE.

    For context, here is the full text:
    {script}
    """

    # Generate search terms
    response = g4f.ChatCompletion.create(
        model=g4f.models.gpt_35_turbo_16k_0613,
        messages=[{"role": "user", "content": prompt}],
    )

    print(response)

    # Load response into JSON-Array
    try:
        search_terms = json.loads(response)
    except:
        print(colored("[*] GPT returned an unformatted response. Attempting to clean...", "yellow"))

        

        # Load the array into a JSON-Array and check if it's valid else repeat the process
        try:
            # Use Regex to get the array ("[" is the first character of the array)
            search_terms = re.search(r"\[(.*?)\]", response)
            search_terms = search_terms.group(0)
            search_terms = json.loads(search_terms)
        except:
            print(colored("[*] Could not clean the response. Attempting to generate search terms again...", "yellow"))
            return get_search_terms(video_subject, amount, script)

    # Let user know
    print(colored(f"\nGenerated {amount} search terms: {', '.join(search_terms)}", "cyan"))

    # Return search terms
    return search_terms