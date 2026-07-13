class FakeGenre:
    def __init__(self, name):
        self.Name = name


class FakeTrack:
    def __init__(self, track_id, genre_name, title=None):
        self.ID = track_id
        self.Genre = FakeGenre(genre_name) if genre_name is not None else None
        self.Title = title or f"Track {track_id}"
