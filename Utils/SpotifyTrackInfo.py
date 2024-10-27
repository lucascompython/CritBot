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

    async def __get_artist_page(self, artist_id: str) -> bytes:
        """Fetches the artist page from Spotify. This page is huge, we only need the first 27648 bytes.
        The monthly listeners are in beggining of the page and the access token is in the 26000+ bytes of the page.

        Args:
            artist_id (str): The Spotify artist ID.

        Returns:
            bytes: The first 27648 bytes of the response.
        """
        url = self.artist_url.format(artist_id=artist_id)
        async with self.session.get(url) as resp:
            # The access_token is in the 26000+ bytes
            data = bytearray()
            async for chunk in resp.content.iter_chunked(1024):
                data.extend(chunk)
                if len(data) >= 27648:
                    return bytes(data)

    def __parse_partial_artist_page(self, data: bytes) -> tuple[str, str]:
        monthly_listeners = []
        current = 1700  # 1700 is approximately a good index to start looking for the monthly listeners

        # doing this is almost 3 times faster than using lxml
        while True:
            if data[current] == 183:  # 183 is the ascii code for ·
                current += 2
                while (
                    data[current] != 32
                ):  # 32 is the ascii code for space, meaning the monthly listeners are over
                    monthly_listeners.append(chr(data[current]))
                    current += 1
                break
            current += 1
        monthly_listeners = "".join(monthly_listeners)

        html = lxml.html.fromstring(
            data[26000:]
        )  # the token is in the 26000+ bytes so we can skip the first 26000 bytes

        script_content = html.xpath('//script[@id="session"]')[0].text_content()

        # The token is 115 chars long and ignore the first 16 chars because they are the '{"accessToken":"' part
        access_token = script_content[16:131]

        return access_token, monthly_listeners

    async def __get_track_info(
        self,
        spotify_track: str,
        bearer_token: str,
    ) -> bytes:
        """Fetches the track info from the Spotify API. Usually this payload is huge, but we only need approximately the first 900 bytes. Im still getting the first 1024 just to be sure that songs with long titles are covered.

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
        done_playcount = False
        while True:
            if (
                data[current] == 123 and not done_playcount
            ):  # 123 is the ascii for '{', the playcount is 51 bytes after the first left bracket
                current += 51

                while data[current] != 34:  # while the byte is not a double quote
                    playcount.append(chr(data[current]))
                    current += 1

                current += 266  # 266 is the max number of "static" bytes between the playcount and the release date this puts the index at the first byte of the copyright text
                done_playcount = True

            if (
                data[current] == 90 and data[current - 3] == 58
            ):  # 90 is the ascii code for Z and the 58 is the ascii code for :, we check the Z because it's the last byte of the timestamp and the : because it's a good indicator that we are actually looking at the release date
                current -= 19  # the Z represents the end of the timestamp, so we go back 19 bytes to get the full date
                for _ in range(10):  # only get the date not the time
                    date.append(chr(data[current]))
                    current += 1
                break
            current += 1

        playcount = "".join(playcount)
        release_date = "".join(date)
        release_date = f"{release_date[8:10]}-{release_date[5:7]}-{release_date[:4]}"  # format the date to dd-mm-yyyy

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
        artist_page = await self.__get_artist_page(artist_id)

        bearer_token, monthly_listeners = self.__parse_partial_artist_page(artist_page)
        response = await self.__get_track_info(spotify_track, bearer_token)

        return (
            monthly_listeners,
            *self.__parse_partial_response(response),
        )


if __name__ == "__main__":
    import uvloop

    async def main() -> None:
        artist_id = "3qiHUAX7zY4Qnjx8TNUzVx"
        spotify_track = "2ph0vvxsYbMZXN5rjfRRWf"

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
