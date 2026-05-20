from mloader.loader import MangaLoader
from mloader.exporter import RawExporter
from functools import partial
from itertools import count
from tqdm.auto import tqdm
from requests import Response
from typing import Any
import requests
import time
import uuid


class CustomSession(requests.Session):
    def __init__(
        self,
        max_retries: int = 3,
        min_backoff: int = 4,
        timeout: int = 10,
    ) -> None:
        super().__init__()
        self.max_retries = max_retries
        self.min_backoff = min_backoff
        self.timeout = timeout
        token = str(uuid.uuid1())
        self.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "Session-Token": token,
            }
        )

    def request(self, method: str | bytes, url: str | bytes, **kwargs: Any) -> Response:  # pyright: ignore[reportIncompatibleMethodOverride]
        kwargs.setdefault("timeout", self.timeout)
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = super().request(method, url, **kwargs)
            except requests.RequestException as exc:
                last_exception = exc
                if attempt == self.max_retries:
                    raise

                time.sleep(max(4, self.min_backoff * (2**attempt)))
                continue

            if response.status_code != 429 and response.status_code < 500:
                return response

            if attempt == self.max_retries:
                return response

            response.close()
            time.sleep(max(4, self.min_backoff * (2**attempt)))

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("unreachable")


class CustoMLoader(MangaLoader):
    
    def __init__(self) -> None:
        exporter = partial(
            RawExporter, destination="output", add_chapter_title=True, add_chapter_subdir=None
        )
        super().__init__(exporter)
        self.session = CustomSession()        
        
    def get_latest_chapter(self, series_id: ...):
        title = self._get_title_details(series_id)
        chapter = self._normalize_ids(
            title_ids=[series_id],
            min_chapter=0,
            max_chapter=10000,
            last_chapter=True,
            chapter_ids=None,
        )
        chapter_id = next(iter(chapter.get(series_id, {})), None)
        return chapter_id

    def download_chapter(self, chapter_id: ..., series_id: ...):
        viewer = self._load_pages(chapter_id)
        chapter = viewer.pages[-1].last_page.current_chapter
        next_chapter = viewer.pages[-1].last_page.next_chapter
        next_chapter = next_chapter if next_chapter.chapter_id != 0 else None
        chapter_name = viewer.chapter_name
        title = self._get_title_details(series_id).title
        exporter = self.exporter(title=title, chapter=chapter, next_chapter=next_chapter)
        pages = [p.manga_page for p in viewer.pages if p.manga_page.image_url]
        page_counter = count()
        chapter_info = {
            "title": chapter.sub_title,
            "chapter_id": chapter_id,
            "series_id": series_id,
            "series_title": title.name,
            "chapter_number": chapter_name,
            "pages": {}
        }
        page_data = {}
        print(f"Downloading {chapter.sub_title} - {chapter_name}")
        for index, page in tqdm(zip(page_counter, pages), total=len(pages), desc="Downloading pages"):
            if not exporter.skip_image(index):
                image_blob = self._decrypt_image(page.image_url, page.encryption_key)

                page_data[index+1] = image_blob
        chapter_info["pages"] = page_data
        return chapter_info