__author__ = "Ernesto"
__email__ = "ernestondieki12@gmail.com"
__version__ = "4.2"



from youtubesearchpython import VideosSearch
import ctypes
from locale import windows_locale
from typing import Optional


class Settings():
    __slots__ = ()

    limit = 30
    LANG = windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]

class Stream(Settings):
    __slots__ = "status"

    def __init__(self):
        self.status = 0

    def search(self, query_str) -> Optional[dict]:
        """ get video metadata; return a simpler dict, {title: id combination}"""

        null = None
        title_link = {}
        try:
            response = VideosSearch(query_str, language=self.LANG, limit=self.limit)
            results = response.result()
            for item in results.get("result", ()):
                title, link = item.get("title"), item.get("id")
                if title and link:
                    title_link.setdefault(title, link)
            self.status = 1
            return title_link

        except Exception as e:
            return

