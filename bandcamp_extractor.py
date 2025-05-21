#!/usr/bin/env python3

import argparse
import csv
import re
from typing import List, Tuple, Dict
import yt_dlp
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from tqdm import tqdm
import time

def extract_bandcamp_links(text: str) -> List[str]:
    """Extract Bandcamp links from text."""
    # Regular expression for Bandcamp URLs
    bandcamp_pattern = r'https?://[^/]*\.bandcamp\.com/[^\s<>"]+'
    return re.findall(bandcamp_pattern, text)

def is_private_video(entry: Dict) -> bool:
    """Check if a video is private or unavailable."""
    if not entry:
        return True
    title = entry.get('title', '').lower()
    return 'private video' in title or 'unavailable' in title

def process_video(ydl: yt_dlp.YoutubeDL, entry: dict, timeout: int = 30) -> List[Tuple[str, str]]:
    """Process a single video and return any found Bandcamp links."""
    if not entry or is_private_video(entry):
        return []
        
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    title = entry.get('title', 'Unknown Title')
    
    try:
        # Set a timeout for the video info extraction
        start_time = time.time()
        video_info = ydl.extract_info(video_url, download=False)
        
        # Check if we've exceeded the timeout
        if time.time() - start_time > timeout:
            print(f"\nTimeout processing video: {title}")
            return []
            
        if not video_info:
            return []
            
        description = video_info.get('description', '')
        bandcamp_links = extract_bandcamp_links(description)
        
        return [(title, link) for link in bandcamp_links]
    except Exception as e:
        if "Private video" in str(e):
            print(f"\nSkipping private video: {title}")
        elif "Video unavailable" in str(e):
            print(f"\nSkipping unavailable video: {title}")
        else:
            print(f"\nError processing video {title}: {str(e)}")
        return []

def get_video_info(playlist_url: str, timeout: int = 30) -> List[Tuple[str, str]]:
    """Get video information from a YouTube playlist using parallel processing."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'ignoreerrors': True,
        'no_warnings': True,
        'socket_timeout': timeout,
        'retries': 3  # Add retries for failed requests
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("Fetching playlist information...")
            playlist_info = ydl.extract_info(playlist_url, download=False)
            if not playlist_info:
                raise Exception("Could not extract playlist information")
            
            # Filter out private videos before processing
            entries = [entry for entry in playlist_info['entries'] if not is_private_video(entry)]
            total_videos = len(entries)
            
            if total_videos == 0:
                print("No accessible videos found in playlist")
                return []
                
            print(f"Found {total_videos} accessible videos in playlist")
            
            results = []
            # Use a more conservative number of workers
            max_workers = min(3, total_videos)  # Reduced from 5 to 3
            
            # Process videos in smaller batches
            batch_size = 5
            for i in range(0, total_videos, batch_size):
                batch = entries[i:i + batch_size]
                print(f"\nProcessing batch {i//batch_size + 1}/{(total_videos + batch_size - 1)//batch_size}")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    with tqdm(total=len(batch), desc="Processing videos") as pbar:
                        future_to_video = {
                            executor.submit(process_video, ydl, entry, timeout): entry 
                            for entry in batch
                        }
                        
                        for future in as_completed(future_to_video):
                            try:
                                video_results = future.result(timeout=timeout)
                                results.extend(video_results)
                            except TimeoutError:
                                print("\nTask timed out, skipping...")
                            except Exception as e:
                                print(f"\nError in task: {str(e)}")
                            finally:
                                pbar.update(1)
                
                # Add a small delay between batches to avoid rate limiting
                if i + batch_size < total_videos:
                    time.sleep(2)
            
            return results
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

def save_to_csv(results: List[Tuple[str, str]], output_file: str):
    """Save results to a CSV file."""
    df = pd.DataFrame(results, columns=['Video Title', 'Bandcamp URL'])
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    print(f"\nResults saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Extract Bandcamp links from YouTube playlist videos')
    parser.add_argument('playlist_url', help='URL of the YouTube playlist')
    parser.add_argument('--output', '-o', default='bandcamp_links.csv',
                      help='Output CSV file name (default: bandcamp_links.csv)')
    parser.add_argument('--workers', '-w', type=int, default=3,
                      help='Number of worker threads (default: 3)')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                      help='Timeout in seconds for each video (default: 30)')
    
    args = parser.parse_args()
    
    print(f"Processing playlist: {args.playlist_url}")
    results = get_video_info(args.playlist_url, args.timeout)
    
    if results:
        save_to_csv(results, args.output)
        print(f"Found {len(results)} Bandcamp links")
    else:
        print("No Bandcamp links found")

if __name__ == '__main__':
    main() 