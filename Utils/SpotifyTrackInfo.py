import lxml.html
import aiohttp
import orjson


class SpotifyTrackInfo:
    """This class is used to get the monthly listeners, playcount, release date and content rating of a Spotify track.

    It is a reverse-engineering of the Spotify website and API.
    This is because the official Spotify API doesn't provide the monthly listeners of an artist nor the total play count of a track.
    """

    __slots__ = ("session", "artist_url", "api_partner_url")

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session
        self.artist_url = "https://open.spotify.com/artist/{artist_id}"
        self.api_partner_url = 'https://api-partner.spotify.com/pathfinder/v1/query?operationName=getTrack&variables={{"uri":"spotify:track:{spotify_track}"}}&extensions={{"persistedQuery":{{"version":1,"sha256Hash":"ae85b52abb74d20a4c331d4143d4772c95f34757bfa8c625474b912b9055b5c0"}}}}'

    @staticmethod
    def __extract_access_token_and_monthly_listeners(text: str) -> tuple[str, str]:
        html = lxml.html.fromstring(text)

        script_content = html.xpath(
            '//script[@id="session" and @data-testid="session"]'
        )[0].text_content()

        # The token is 115 chars long and ignore the first 16 chars because they are the '{"accessToken":"' part
        access_token = script_content[16:131]

        monthly_listeners = html.xpath('//div[@data-testid="monthly-listeners-label"]')[
            0
        ].text_content()[:-18]  # Remove the " monthly listeners" part

        monthly_listeners = monthly_listeners.replace(",", "")

        return access_token, monthly_listeners

    async def __get_artist_page(self, artist_id: str) -> str:
        url = self.artist_url.format(artist_id=artist_id)

        async with self.session.get(url) as resp:
            return await resp.text()

    async def __get_track_info(
        self, spotify_track: str, bearer_token: str
    ) -> tuple[str, str, bool]:
        """Get the playcount, release date and content rating of a Spotify track.

        Args:
            spotify_track (str): The Spotify track ID.
            bearer_token (str): The bearer token scraped from the website.

        Returns:
            tuple[str, str, bool]: The playcount, release date and content rating. The content rating is a boolean. True if the track is explicit, False if it's not and None if it's unknown.
        """
        url = self.api_partner_url.format(spotify_track=spotify_track)

        async with self.session.get(
            url, headers={"authorization": f"Bearer {bearer_token}"}
        ) as resp:
            json = await resp.json(loads=orjson.loads)

        content_rating = None
        match json["data"]["trackUnion"]["contentRating"]["label"]:
            case "EXPLICIT":
                content_rating = True
            case "NONE":
                content_rating = False

        return (
            json["data"]["trackUnion"]["playcount"],
            json["data"]["trackUnion"]["albumOfTrack"]["date"]["isoString"],
            content_rating,
        )

    async def get_info(
        self, artist_id: str, spotify_track: str
    ) -> tuple[str, str, str, bool]:
        """Get the monthly listeners, playcount, release date and content rating of a Spotify track.

        Args:
            artist_id (str): The Spotify artist ID.
            spotify_track (str): The Spotify track ID.

        Returns:
            tuple[str, str, str, bool]: The monthly listeners, playcount, release date and content rating. The content rating is a boolean. True if the track is explicit, False if it's not and None if it's unknown.
        """
        text = await self.__get_artist_page(artist_id)

        bearer_token, monthly_listeners = (
            self.__extract_access_token_and_monthly_listeners(text)
        )

        return (
            monthly_listeners,
            *await self.__get_track_info(spotify_track, bearer_token),
        )


if __name__ == "__main__":
    import uvloop

    async def main() -> None:
        spotify_track = "7soCc4TpT99bOhJoCiMqFN"
        artist_id = "2wpWOzQE5TpA0dVnh5YD08"

        async with aiohttp.ClientSession() as session:
            spotify_track_info = SpotifyTrackInfo(session)

            (
                monthly_listeners,
                playcount,
                release_date,
                content_rating,
            ) = await spotify_track_info.get_info(artist_id, spotify_track)

            print(f"Monthly Listeners: {monthly_listeners}")
            print(f"Playcount: {playcount}")
            print(f"Release Date: {release_date}")
            print(f"Is explicit?: {content_rating}")

    uvloop.run(main())
