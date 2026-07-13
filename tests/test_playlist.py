from conftest import FakeTrack

from rkb_lib.playlist import (
    build_genre_index,
    find_tracks_for_genres,
    get_unmapped_tracks,
)


class FakeDB:
    def __init__(self, tracks):
        self._tracks = tracks

    def get_content(self):
        return self._tracks


def test_build_genre_index_groups_case_insensitively():
    """Given tracks with genres differing only by case, when build_genre_index runs, then they land under the same lowercase key."""
    db = FakeDB(
        [
            FakeTrack(1, "Deep House"),
            FakeTrack(2, "deep house"),
            FakeTrack(3, "Techno"),
        ]
    )

    index = build_genre_index(db, ignored=set())

    assert {t.ID for t in index["deep house"]} == {1, 2}
    assert {t.ID for t in index["techno"]} == {3}


def test_build_genre_index_skips_none_and_ignored():
    """Given a track with no genre and one with an ignored genre, when build_genre_index runs, then only remaining genres appear."""
    db = FakeDB(
        [
            FakeTrack(1, None),
            FakeTrack(2, "Remix"),
            FakeTrack(3, "Techno"),
        ]
    )

    index = build_genre_index(db, ignored={"Remix"})

    assert list(index.keys()) == ["techno"]


def test_find_tracks_for_genres_dedupes_across_genres():
    """Given a track indexed under two requested genres, when find_tracks_for_genres runs, then the track appears once."""
    index = {
        "deep house": [FakeTrack(1, "Deep House")],
        "house": [FakeTrack(1, "Deep House"), FakeTrack(2, "House")],
    }

    tracks = find_tracks_for_genres(index, ["Deep House", "House"])

    assert [t.ID for t in tracks] == [1, 2]


def test_get_unmapped_tracks_only_returns_genres_absent_from_structure():
    """Given one genre mapped in the structure and one not, when get_unmapped_tracks runs, then only the unmapped genre's tracks are returned."""
    index = {
        "deep house": [FakeTrack(1, "Deep House")],
        "trap": [FakeTrack(2, "Trap")],
    }
    structure = {"ROOT": {"Deep": ["Deep House"]}}

    tracks, unmapped_genres = get_unmapped_tracks(index, structure)

    assert [t.ID for t in tracks] == [2]
    assert unmapped_genres == ["Trap"]
