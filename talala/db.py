import sqlite3

from talala.playlist import Playlist, Video


class DB:

    db_file: str = "data/app.db"
    schema_file: str = "db/structure.sql"

    def __init__(self):
        self.__connection: sqlite3.Connection = None

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _tb):
        self.close()

    @property
    def connection(self):
        if not self.__connection:
            self.__connection = self.__connect()
        return self.__connection

    def close(self):
        if not self.__connection:
            return
        self.__connection.commit()
        self.__connection.close()
        self.__connection = None

    def load_schema(self):
        with open(self.schema_file, mode="r", encoding="utf-8") as file:
            cur = self.connection.cursor()
            cur.executescript(file.read())

    def load_playlist(self) -> Playlist:
        """Loads the default playlist from the database."""
        cur = self.connection.cursor()
        res = cur.execute(
            "SELECT youtube_id, url, title, duration, thumbnail_url FROM tracks"
        )
        items = [
            Video(
                youtube_id=youtube_id,
                url=url,
                title=title,
                thumbnail_url=thumbnail_url,
                duration=duration,
            )
            for (youtube_id, url, title, duration, thumbnail_url) in res.fetchall()
        ]
        return Playlist(items=items)

    def insert_track(self, track: Video) -> Video:
        return self.insert_tracks([track])[0]

    def insert_tracks(
        self, tracks: list[Video], skip_conflicts: bool = False
    ) -> list[Video]:
        cur = self.connection.cursor()

        if skip_conflicts:
            sql_on_conflict = " ON CONFLICT DO NOTHING "
        else:
            sql_on_conflict = " "

        sql = f"INSERT INTO tracks(youtube_id, url, title, duration, thumbnail_url) VALUES (?, ?, ?, ?, ?){sql_on_conflict}"
        cur.executemany(
            sql,
            [
                (
                    track.youtube_id,
                    track.url,
                    track.title,
                    track.duration,
                    track.thumbnail_url,
                )
                for track in tracks
            ],
        )
        self.connection.commit()
        return tracks

    def search_track(self, term: str) -> list[Video]:
        cur = self.connection.cursor()
        res = cur.execute(
            "SELECT youtube_id, url, title, duration, thumbnail_url FROM tracks WHERE title LIKE ? ORDER BY title",
            (f"%{term}%",),
        )

        return [
            Video(
                youtube_id=youtube_id,
                url=url,
                title=title,
                duration=duration,
                thumbnail_url=thumbnail_url,
            )
            for (youtube_id, url, title, duration, thumbnail_url) in res.fetchall()
        ]

    def __connect(self):
        connection = sqlite3.connect(self.db_file)
        connection.execute("PRAGMA foreign_keys = on")
        return connection
