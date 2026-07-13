from conftest import FakeTrack

from rkb_lib.genres import get_all_genres, get_mapped_genres


class FakeDB:
    def __init__(self, tracks):
        self._tracks = tracks

    def get_content(self):
        return self._tracks


def test_get_all_genres_counts_and_examples():
    """
    Given six tracks with a mix of genres, an ignored genre, and no genre,
    when get_all_genres runs,
    then it counts only non-ignored genres and caps examples at 3.
    """
    db = FakeDB(
        [
            FakeTrack(1, "Deep House", title="A"),
            FakeTrack(2, "Deep House", title="B"),
            FakeTrack(3, "Deep House", title="C"),
            FakeTrack(4, "Deep House", title="D"),
            FakeTrack(5, "Remix", title="E"),
            FakeTrack(6, None),
        ]
    )

    counts, examples = get_all_genres(db, ignored={"Remix"})

    assert counts == {"Deep House": 4}
    assert examples == {"Deep House": ["A", "B", "C"]}


def test_get_mapped_genres_flattens_and_lowercases():
    """
    Given a structure with genres nested under multiple playlists,
    when get_mapped_genres runs,
    then it returns one flat lowercase set.
    """
    structure = {
        "ROOT": {
            "Playlist A": ["Deep House", "Techno"],
            "Playlist B": ["Trap"],
        }
    }

    assert get_mapped_genres(structure) == {"deep house", "techno", "trap"}
