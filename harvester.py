import requests
from bs4 import BeautifulSoup
import json
import time
import os
import random

ARTIST_ID = 342499 # Element of Crime
API_BASE = "https://genius.com/api"
DATA_FILE = "lyrics.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_all_songs():
    songs = []
    page = 1
    while page:
        print(f"Fetching song list page {page}...")
        url = f"{API_BASE}/artists/{ARTIST_ID}/songs?page={page}&sort=popularity"
        try:
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code != 200:
                print(f"Failed to fetch page {page}: {resp.status_code}")
                break
            
            data = resp.json()
            song_list = data['response']['songs']
            for song in song_list:
                songs.append({
                    "id": song['id'],
                    "title": song['title'],
                    "url": song['url']
                })
            
            page = data['response']['next_page']
            time.sleep(0.5) # Be nice to the API
            
        except Exception as e:
            print(f"Error fetching song list: {e}")
            break
            
    print(f"Found {len(songs)} songs total.")
    return songs

def get_lyrics_from_url(url):
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # Genius lyrics are often in multiple containers with this attribute
        containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        
        if not containers:
            return None
            
        lyrics_text = ""
        for container in containers:
            # Remove non-lyric elements like "3 Contributors" or "You might also like"
            for excluded in container.find_all(attrs={"data-exclude-from-selection": "true"}):
                excluded.decompose()
            
            # Replace <br> with newlines
            for br in container.find_all("br"):
                br.replace_with("\n")
            
            # Get text and clean it
            chunk = container.get_text(separator="\n").strip()
            lyrics_text += chunk + "\n\n"
            
        return lyrics_text.strip()
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def harvest():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            all_lyrics = json.load(f)
    else:
        all_lyrics = {}
    
    songs = get_all_songs()
    
    for i, song in enumerate(songs):
        song_id = str(song['id'])
        if song_id in all_lyrics:
            continue
            
        print(f"[{i+1}/{len(songs)}] Scraping '{song['title']}'...")
        lyrics = get_lyrics_from_url(song['url'])
        
        if lyrics:
            all_lyrics[song_id] = {
                "title": song['title'],
                "url": song['url'],
                "lyrics": lyrics
            }
            # Save incrementally
            with open(DATA_FILE, 'w') as f:
                json.dump(all_lyrics, f, indent=2, ensure_ascii=False)
        else:
            print(f"  -> No lyrics found.")
        
        # Random delay to avoid blocking
        time.sleep(random.uniform(1.0, 2.5))

if __name__ == "__main__":
    harvest()