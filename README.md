# YouTube Bandcamp Link Extractor

A Python script that extracts Bandcamp links from YouTube playlist video descriptions. This tool is useful for finding Bandcamp pages of artists featured in YouTube playlists.

## Features

- Extracts Bandcamp links from YouTube video descriptions
- Processes playlists in parallel for faster extraction
- Handles large playlists by processing in batches
- Real-time progress display with video counts
- Continuous saving of results to CSV
- Detailed logging of found links and errors
- Smart output file naming based on playlist ID
- Graceful handling of:
  - Age-restricted videos
  - Copyright-blocked videos
  - Private videos
  - Network errors

## Requirements

- Python 3.6+
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtubelinks.git
cd youtubelinks
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python bandcamp_extractor.py "YOUR_PLAYLIST_URL"
```

With options:
```bash
python bandcamp_extractor.py "YOUR_PLAYLIST_URL" --output custom_output.csv --workers 8
```

### Arguments

- `playlist_url`: YouTube playlist URL (required)
- `--output`, `-o`: Output CSV file (optional, defaults to auto-generated name)
- `--workers`, `-w`: Number of worker threads (default: 4)

### Output

The script generates:
1. A CSV file containing:
   - Video Title
   - Video URL
   - Bandcamp Links
2. A log file (`bandcamp_extractor.log`) with detailed processing information

## Example

```bash
python bandcamp_extractor.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

## Notes

- The script processes videos in batches of 50 to manage memory usage
- Results are saved continuously, so you can safely interrupt the script
- Some videos may be skipped due to:
  - Age restrictions
  - Copyright claims
  - Private status
  - Network issues
- All errors are logged for troubleshooting

## License

MIT License 