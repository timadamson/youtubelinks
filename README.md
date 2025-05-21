# YouTube Playlist Bandcamp Link Extractor

This CLI tool extracts Bandcamp links from YouTube playlist videos and saves them to a CSV file.

## Requirements

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script with a YouTube playlist URL:

```bash
python bandcamp_extractor.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

Optional arguments:
- `--output` or `-o`: Specify a custom output CSV file name (default: bandcamp_links.csv)

Example:
```bash
python bandcamp_extractor.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID" --output my_links.csv
```

## Output

The script generates a CSV file containing:
- Video Title
- Bandcamp URL

## Notes

- The script processes public YouTube playlists only
- It extracts Bandcamp links from video descriptions
- The output is saved in CSV format with proper quoting to handle special characters 