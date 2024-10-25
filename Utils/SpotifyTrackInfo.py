import lxml.html
import aiohttp


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

        # The first 9 chars are "Artist · " and the last 18 are " monthly listeners."
        monthly_listeners = html.xpath('//meta[@property="og:description"]')[0].attrib[
            "content"
        ][9:-19]

        return access_token, monthly_listeners

    async def __get_artist_page(self, artist_id: str) -> str:
        url = self.artist_url.format(artist_id=artist_id)

        async with self.session.get(url) as resp:
            return await resp.text()

    async def __get_track_info(
        self,
        spotify_track: str,
        bearer_token: str,
    ) -> bytes:
        """Fetches the track info from the Spotify API. Usually this payload is huge, but we only aproximatapproximately the first 900 bytes. Im still getting the first 1024 just to be sure that songs with long titles are covered.

        Args:
            spotify_track (str): The Spotify track ID.
            bearer_token (str): The Spotify access token.

        Returns:
            bytes: The first 1024 bytes of the response.
        """
        url = self.api_partner_url.format(spotify_track=spotify_track)
        async with self.session.get(
            url, headers={"authorization": f"Bearer {bearer_token}"}
        ) as resp:
            return await resp.content.read(1024)

    def __parse_partial_response(self, data: bytes) -> tuple[str, str, bool]:
        """Parses the partial response from the Spotify API.

        Args:
            data (bytes): The first 1024 bytes of the response.

        Returns:
            tuple[str, str, bool]: The playcount, release date and content rating. The content rating is a boolean. True if the track is explicit, False if it's not and None if it's unknown.
        """
        explicit = data[70] == 69  # 69 is the ascii code for E (EXPLICIT)

        playcount = []
        date = []
        current = 159  # 159 is the index of the first byte of the name which is the first "dynamic" field
        left_brackets = 0
        done_playcount = False
        while True:
            if data[current] == 123:  # Count left brackets
                left_brackets += 1

            if (
                left_brackets == 1 and not done_playcount
            ):  # the playcount is 51 bytes after the first left bracket
                current += 51

                while data[current] != 34:
                    playcount.append(chr(data[current]))
                    current += 1
                current += 266  # 266 is the max number of "static" bytes between the playcount and the release date this puts the index at the first byte of the copyright text
                done_playcount = True

            if data[current] == 90:  # 90 is the ascii code for Z
                current -= 19  # the Z represents the end of the timestamp, so we go back 19 bytes to get the full date
                for _ in range(20):
                    date.append(chr(data[current]))
                    current += 1
                break
            current += 1

        playcount = "".join(playcount)
        release_date = "".join(date)

        return playcount, release_date, explicit

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
        response = await self.__get_track_info(spotify_track, bearer_token)

        return (
            monthly_listeners,
            *self.__parse_partial_response(response),
        )


if __name__ == "__main__":
    import uvloop

    async def main() -> None:
        artist_id = "5K4W6rqBFWDnAN6FQUkS6x"
        spotify_track = "4zfgnW5p7C2QAFauTn09Mh"

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
