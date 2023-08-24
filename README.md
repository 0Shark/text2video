# Text2Video

This is a simple script that creates a video from a topic that you provide. It uses the OpenAI GPT-3 API to generate text, the Azure Cloud Text-to-Speech API to convert the text to speech, grabs tagged images from Pexels, and then uses MoviePy to create a video.

### Tools Used
* [OpenAI GPT-3 API](https://openai.com/blog/openai-api/)
* [Azure Text-to-Speech API](https://azure.microsoft.com/en-us/products/ai-services/text-to-speech)
* [Pexels API](https://www.pexels.com/api/)
* [MoviePy](https://zulko.github.io/moviepy/)

### How to Use
1. Clone the repository
2. Create a virtual environment and install the requirements
3. Create an Azure Cloud account and enable the Text-to-Speech API
4. Create a Pexels account and get an API key
5. Create an OpenAI account and get an API key
6. Create a .env file and add the following variables:
    * AZURE_SPEECH_KEY = your Azure Speech API key
    * AZURE_SPEECH_REGION = your Azure resource region
    * PEXELS_API_KEY = your Pexels API key
    * OPENAI_API_KEY = your OpenAI API key
    * OPENAI_ORGANIZATION_ID = your OpenAI organization ID
7. Run main.py and provide the topic you want to create a video for
