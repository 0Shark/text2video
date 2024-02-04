# Text2Video

Create YouTube Shorts without any effort, simply by providing a video topic to talk about.

## Installation

```bash
cd MoneyPrinter/Backend
pip install -r requirements.txt

# Run the backend server
python3 main.py

# Run the frontend server
cd ../Frontend
python3 -m http.server 3000
```

## Usage

1. In `.env` fill in the required values
1. Open `http://localhost:3000` in your browser
1. Enter a topic to talk about
1. Choose a voice ID
1. Click on the "Generate" button
1. Wait for the video to be generated
1. The video's location is `temp/output.mp4`

## Fonts

Add your fonts to the `fonts/` folder, and load them by specifiying the font name on line `124` in `Backend/video.py`.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

See [`LICENSE`](LICENSE) file for more information.
