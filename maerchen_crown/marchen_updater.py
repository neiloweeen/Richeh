
import os
import json
from dotenv import load_dotenv
from common.mp_utils import CustoMLoader
from common.b2_utils import upload_to_bucket
from tqdm import tqdm
from urllib.parse import quote
from github import Github


import re

load_dotenv()

def main():
    loader = CustoMLoader()
    series_id = os.getenv('MPLUS_SERIES_ID')
    chapter_id = loader.get_latest_chapter(series_id)
    chapter = loader.download_chapter(chapter_id, series_id)
    
    chapter_number = eval(chapter['chapter_number'].strip("#").split(",")[0].lstrip("0").strip()) 
    series_title = chapter['series_title'].lower().replace(" ", "_")
    uploaded_pages = []
    
    with open("maerchen_crown/Marchen-Crown.json", encoding="utf-8") as f:
        data = json.load(f)
    data['chapters'][chapter_number] = {}
    if data['chapters'].get(str(chapter_number)):
        return print("Chapter already exists.")
    
    
    import threading
    import time
    import requests

    def upload_worker(pages_slice, uploaded_pages, lock):
        for page, page_data in pages_slice:
            page_path = f"{series_title}/fullres/ch{str(chapter_number).zfill(3)}/p{str(page).zfill(3)}.png"
            print(f"Uploading {page_path}...")
            _ = upload_to_bucket(page_path, page_data)
            url = 'https://cubari.onk.moe/' + quote(page_path)
            with lock:
                uploaded_pages.append((page, url))
            time.sleep(0.1)

    pages_items = list(chapter['pages'].items())
    num_threads = 5
    threads = []
    lock = threading.Lock()

    # Split the pages into chunks for each thread, but keep order by assigning in round-robin
    slices = [[] for _ in range(num_threads)]
    for idx, item in enumerate(pages_items):
        slices[idx % num_threads].append(item)

    for i in range(num_threads):
        t = threading.Thread(target=upload_worker, args=(slices[i], uploaded_pages, lock))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Sort uploaded_pages by page number to preserve order
    uploaded_pages.sort(key=lambda x: int(x[0]))
    uploaded_pages = [url for _, url in uploaded_pages]

    
    data['chapters'][chapter_number] = {
        "volume": 1,
        "title": chapter['title'],
        "groups": {
            "MangaPlus": uploaded_pages
        }
    }
    # Get GitHub token from environment
    github_token = os.getenv('GITHUB_ACCESS_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_ACCESS_TOKEN not found in environment variables")
    
    # Get repository name from environment or use default
    repo_name = os.getenv('GITHUB_REPO', 'neiloweeen/Richeh')
    file_path = 'maerchen_crown/Marchen-Crown.json'
    branch = 'main'
    
    # Initialize GitHub client
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    
    # Get the current file from GitHub to get its SHA
    print("Fetching current file from GitHub...")
    github_file = repo.get_contents(file_path, ref=branch)
    
    # Prepare updated content
    updated_content = json.dumps(data, indent=4, ensure_ascii=False)
    
    # Update the file on GitHub
    print("Pushing changes to GitHub...")
    repo.update_file(
        path=github_file.path,
        message=f"Added Chapter {chapter_number}",
        content=updated_content,
        sha=github_file.sha,
        branch=branch
    )
    print("✓ Successfully pushed to GitHub!")

    time.sleep(3)

    # Poll the link up to 7 times, waiting a minute each time, proceed when 200 response
    chapter_link = f'https://cubari.moe/read/gist/cmF3L25laWxvd2VlZW4vUmljaGVoL3JlZnMvaGVhZHMvbWFpbi9tYWVyY2hlbl9jcm93bi9NYXJjaGVuLUNyb3duLmpzb24/{chapter_number}/1/'
    for attempt in range(7):
        try:
            resp = requests.get(chapter_link)
            if resp.status_code == 200:
                print(f"Chapter link is live: {chapter_link}")
                break
            else:
                print(f"Attempt {attempt+1}: Got status {resp.status_code}, retrying in 60s...")
        except Exception as e:
            print(f"Attempt {attempt+1}: Error {e}, retrying in 60s...")
        for _ in trange(60):
            time.sleep(1)
    else:
        print("Chapter link did not become live after 5 attempts.")
        return
            
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    message = {"content": f"Added Chapter {chapter_number}. \nLink: {chapter_link}"}
    try:
        requests.post(discord_webhook_url, json=message)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

if __name__ == "__main__":
    main()
    
# python -m maerchen_crown.marchen_updater