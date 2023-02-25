import lxml.html


class SongNotFound(Exception):
    pass


class GeniusLyrics():
    __slots__ = ("access_token", "session")
    def __init__(self, access_token: str, session):
        self.access_token = access_token
        self.session = session

    async def _get_path(self, query: str) -> str | None:

        async with self.session.get(f"https://api.genius.com/search?q={query}&access_token={self.access_token}&per_page=1") as resp:
            json = await resp.json()
            try:
                return json["response"]["hits"][0]["result"]["path"]
            except IndexError:
                return None


    async def _get_page(self, path: str) -> tuple[str, str]:
        full_path = "https://genius.com" + path
        async with self.session.get(full_path) as resp:
            return (await resp.text(), full_path)
    

    async def get_lyrics(self, query: str) -> tuple[str, str] | None:


        path = await self._get_path(query)
        if path is None:
            raise SongNotFound(f"Could not get {query} from genius.com.")
        page, lyrics_url = await self._get_page(path)


        tree = lxml.html.fromstring(page)
        for br in tree.xpath("//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        

        div = tree.xpath('//div[contains(@class, "lyrics") or contains(@class, "Lyrics__Root")]')
        if not div:
            return None
            
        lyrics = str(div[0].text_content())
        lyrics = lyrics[1:-1] 

        thing = "You might also like"
        index = lyrics.find(thing)

        lyrics = lyrics[:index]
        index = lyrics.find("Lyrics")
        lyrics = lyrics[index + 6:]
        return lyrics, lyrics_url



        
    
    



