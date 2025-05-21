#!/usr/bin/env python3

import argparse
import re
import yt_dlp
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import sys
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bandcamp_extractor.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def extract_bandcamp_links(video_url: str):
    """Extract Bandcamp links from a YouTube video description."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'skip_download': True,
            'socket_timeout': 30,
            'retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info:
                return None
            
            description = info.get('description', '')
            if not description:
                return None
            
            # Look for Bandcamp links in the description
            bandcamp_links = re.findall(r'https?://[^\s<>"]+?bandcamp\.com[^\s<>"]*', description)
            if bandcamp_links:
                return {
                    'video_title': info.get('title', 'Unknown Title'),
                    'video_url': video_url,
                    'bandcamp_links': bandcamp_links
                }
    except Exception as e:
        print(f"\nError processing {video_url}: {str(e)}", file=sys.stderr)
    return None

def process_playlist(playlist_url: str, output_file: str = None, max_workers: int = 4):
    """Process a YouTube playlist and extract Bandcamp links."""
    # Smart default for output file if none provided
    if not output_file:
        # Extract playlist ID or use current timestamp if not possible
        playlist_id = re.search(r'(?:list=)([^&]+)', playlist_url)
        if playlist_id:
            playlist_id = playlist_id.group(1)
            output_file = f"bandcamp_links_{playlist_id}.csv"
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"bandcamp_links_{timestamp}.csv"
    
    processed_count = 0
    found_count = 0
    error_count = 0
    
    try:
        # Extract playlist information
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'skip_download': True,
            'socket_timeout': 30,
            'retries': 3,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Fetching playlist information...")
            playlist_info = ydl.extract_info(playlist_url, download=False)
            if not playlist_info:
                logger.error("Could not extract playlist information")
                return
            
            videos = playlist_info.get('entries', [])
            if not videos:
                logger.warning("No videos found in playlist")
                return
            
            total_videos = len(videos)
            logger.info(f"Found {total_videos} videos in playlist")
            
            # Create or append to CSV file
            file_exists = os.path.exists(output_file)
            mode = 'a' if file_exists else 'w'
            
            # Process videos in parallel with smaller batches
            batch_size = 50  # Process 50 videos at a time
            
            for i in range(0, total_videos, batch_size):
                batch = videos[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(total_videos + batch_size - 1)//batch_size}")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(extract_bandcamp_links, video['url']): video['url'] 
                        for video in batch
                    }
                    
                    # Create progress bar for this batch
                    with tqdm(total=len(batch), desc="Processing videos") as pbar:
                        for future in as_completed(futures):
                            try:
                                result = future.result()
                                processed_count += 1
                                
                                if result:
                                    found_count += 1
                                    # Create DataFrame for this result
                                    df = pd.DataFrame({
                                        'Video Title': [result['video_title']],
                                        'Video URL': [result['video_url']],
                                        'Bandcamp Links': [', '.join(result['bandcamp_links'])]
                                    })
                                    
                                    # Write to CSV immediately
                                    df.to_csv(output_file, mode=mode, header=not file_exists, index=False)
                                    file_exists = True  # After first write, we're appending
                                    
                                    # Log found links
                                    logger.info(f"Found Bandcamp links in: {result['video_title']}")
                                    for link in result['bandcamp_links']:
                                        logger.info(f"  - {link}")
                            except Exception:
                                error_count += 1
                            
                            # Update progress bar
                            pbar.update(1)
                            pbar.set_postfix({
                                'Processed': processed_count,
                                'Found': found_count,
                                'Errors': error_count
                            })
                
                # Add a small delay between batches to avoid rate limiting
                if i + batch_size < total_videos:
                    time.sleep(2)
            
            logger.info(f"Processing complete.")
            logger.info(f"Processed {processed_count} videos")
            logger.info(f"Found Bandcamp links in {found_count} videos")
            logger.info(f"Encountered {error_count} errors")
            logger.info(f"Results saved to {output_file}")
            
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user. Progress has been saved.")
        logger.info(f"Processed {processed_count} videos")
        logger.info(f"Found Bandcamp links in {found_count} videos")
        logger.info(f"Encountered {error_count} errors")
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Error processing playlist: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Extract Bandcamp links from YouTube playlist descriptions')
    parser.add_argument('playlist_url', help='YouTube playlist URL')
    parser.add_argument('--output', '-o', 
                        help='Output CSV file (default: auto-generated based on playlist ID)')
    parser.add_argument('--workers', '-w', type=int, default=4,
                        help='Number of worker threads (default: 4)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting extraction from playlist: {args.playlist_url}")
    process_playlist(args.playlist_url, args.output, args.workers)

if __name__ == '__main__':
    main()