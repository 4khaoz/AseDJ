BEGIN EXCLUSIVE TRANSACTION;

CREATE TABLE IF NOT EXISTS tracks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    duration INTEGER,
    thumbnail_url VARCHAR(255),
    youtube_id VARCHAR(255) NOT NULL,
    UNIQUE(url),
    UNIQUE(youtube_id)
);

CREATE TABLE IF NOT EXISTS playlists(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    thumbnail_url VARCHAR(255),
    youtube_id VARCHAR(255) NOT NULL,
    UNIQUE(url),
    UNIQUE(youtube_id)
);

CREATE TABLE IF NOT EXISTS playlist_tracks(
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE CASCADE,
    UNIQUE(playlist_id, track_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS tracks_youtube_id_index ON tracks(youtube_id);
CREATE UNIQUE INDEX IF NOT EXISTS playlists_youtube_id_index ON playlists(youtube_id);

COMMIT TRANSACTION;