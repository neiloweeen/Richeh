
import os
import json
from dotenv import load_dotenv
from common.mp_utils import CustoMLoader
from common.gh_utils import GithubHandler
from common.b2_utils import upload_to_bucket
from tqdm import tqdm
from urllib.parse import quote
import subprocess


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
    
    
    for page, page_data in tqdm(list(chapter['pages'].items())):
        page_path = f"{series_title}/fullres/ch{str(chapter_number).zfill(3)}/p{str(page).zfill(3)}.png"
        print(f"Uploading {page_path}...")
        _ = upload_to_bucket(page_path, page_data)
        url = 'https://cubari.onk.moe/' + quote(page_path)
        uploaded_pages.append(url)

    
    data['chapters'][chapter_number] = {
        "volume": 1,
        "title": chapter['title'],
        "groups": {
            "MangaPlus": uploaded_pages
        }
    }
    subprocess.run(["git", "pull"], check=True)
    with open("maerchen_crown/Marchen-Crown.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        git_commands = [
            ["git", "config", "--local", "user.name", "fenixer"],
            ["git", "config", "--local", "user.email", "143337992+Fenixer@users.noreply.github.com"],
            ["git", "add", "maerchen_crown/Marchen-Crown.json"],
            ["git", "commit", "-m", f"Added Chapter {chapter_number}"],
            ["git", "push"]
        ]

        for command in git_commands:
            subprocess.run(command, check=True)

if __name__ == "__main__":
    main()
    
# python -m maerchen_crown.marchen_updater