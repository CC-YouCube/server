#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Spotify support module
"""

# Built-in modules
from logging import getLogger
from os import getenv
from enum import Enum
from re import match as re_match
from typing import Union

# pip modules
from spotipy import SpotifyClientCredentials, MemoryCacheHandler
from spotipy.client import Spotify


# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

class SpotifyTypes(Enum):
    TRACK = "track"
    ARTIST = "artist"
    ALBUM = "album"
    PLAYLIST = "playlist"
    SHOW = "show"
    EPISODE = "episode"
    USER = "user"


class SpotifyURLProcessor:
    def __init__(self, spotify: Spotify = None, spotify_market: str = "US") -> None:
        self.spotify = spotify
        self.spotify_market = spotify_market

    def spotify_track(self, spotify_id: str) -> str:
        track: dict = self.spotify.track(spotify_id)

        artists = track["artists"][0]["name"]
        name = track["name"]

        return f"{artists} - {name}"

    def spotify_playlist(self, spotify_id: str) -> list:
        playlist_tracks = self.spotify.playlist_items(spotify_id)
        playlist = []
        for item in playlist_tracks["items"]:
            track = item.get("track")
            if track:
                playlist.append(track.get("uri"))

        return playlist

    def spotify_album_tracks(self, spotify_id: str) -> list:
        album_tracks = self.spotify.album_tracks(spotify_id)
        playlist = []

        for track in album_tracks["items"]:
            playlist.append(track.get("uri"))

        return playlist

    def spotify_artist(self, spotify_id: str) -> list:
        top_tracks = self.spotify.artist_top_tracks(spotify_id)
        playlist = []

        for track in top_tracks["tracks"]:
            playlist.append(track.get("uri"))

        return playlist

    def spotify_show(self, spotify_id: str) -> list:
        episodes = self.spotify.show_episodes(
            spotify_id, market=self.spotify_market)
        playlist = []

        for track in episodes["items"]:
            playlist.append(track.get("uri"))

        return playlist

    def spotify_episode(self, spotify_id: str) -> str:
        episode = self.spotify.episode(spotify_id, market=self.spotify_market)

        publisher = episode.get("show").get("publisher")
        name = episode.get("show").get("name")
        episode_name = episode.get("name")

        return f"{publisher} - {name} - {episode_name}"

    def spotify_user(self, spotify_id: str) -> list:
        """
        Get first playlist of user and return all items
        """
        playlists = self.spotify.user_playlists(spotify_id)
        return self.spotify_playlist(playlists.get("items")[0].get("id"))

    # pylint: disable-next=inconsistent-return-statements
    def auto(self, url: str) -> Union[str, list]:
        type_function_map = {
            SpotifyTypes.ALBUM: self.spotify_album_tracks,
            SpotifyTypes.TRACK: self.spotify_track,
            SpotifyTypes.PLAYLIST: self.spotify_playlist,
            SpotifyTypes.ARTIST: self.spotify_artist,
            SpotifyTypes.SHOW: self.spotify_show,
            SpotifyTypes.EPISODE: self.spotify_episode,
            SpotifyTypes.USER: self.spotify_user
        }

        # pylint: disable=protected-access
        for match in [
            re_match(Spotify._regex_spotify_uri, url),
            re_match(Spotify._regex_spotify_url, url)
        ]:
            # pylint: enable=protected-access
            if match:
                group = match.groupdict()

                match_type = group.get("type")
                match_id = group.get("id")

                for spotify_type, func in type_function_map.items():
                    if spotify_type.value == match_type:
                        return func(match_id)


def main() -> None:
    logger = getLogger(__name__)

    # Spotify
    spotify_client_id = getenv("SPOTIPY_CLIENT_ID")
    spotify_client_secret = getenv("SPOTIPY_CLIENT_SECRET")
    spotipy = None

    if spotify_client_id and spotify_client_secret:
        logger.info("Spotipy Enabled")
        spotipy = Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=spotify_client_id,
                client_secret=spotify_client_secret,
                cache_handler=MemoryCacheHandler()
            )
        )
    else:
        logger.info("Spotipy Disabled")
    spotify_url_processor = SpotifyURLProcessor(spotipy)

    test_urls = [
        "https://open.spotify.com/album/2Kh43m04B1UkVcpcRa1Zug",
        "https://42",
        "https://open.spotify.com/playlist/1Ze30K0U9OYtQZsQS1vIPj",
        "https://open.spotify.com/artist/64tJ2EAv1R6UaZqc4iOCyj",
        "https://open.spotify.com/episode/0UCTRy5frRHxD6SktX9dbV",
        "https://open.spotify.com/show/5fA3Ze7Ni75iXAEZaEkJIu",
        "https://open.spotify.com/user/besdkg6w64xf0rt713643tgvt",
        "https://open.spotify.com/playlist/5UrcnHexRYVEprv5DJBPER"
    ]

    # pylint: disable-next=import-outside-toplevel
    from yc_colours import Foreground

    for url in test_urls:
        print(Foreground.BLUE + url + Foreground.WHITE,
              spotify_url_processor.auto(url))


if __name__ == "__main__":
    main()
