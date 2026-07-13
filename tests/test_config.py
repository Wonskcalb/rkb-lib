import pytest

from rkb_lib import config


def test_find_config_env_var(tmp_path, monkeypatch):
    """
    Given RKB_STRUCTURE points to an existing file,
    when find_config runs,
    then it returns that path.
    """
    cfg = tmp_path / "custom.toml"
    cfg.write_text("")
    monkeypatch.setenv("RKB_STRUCTURE", str(cfg))

    assert config.find_config() == cfg


def test_find_config_env_var_missing(tmp_path, monkeypatch):
    """
    Given RKB_STRUCTURE points to a missing file,
    when find_config runs,
    then it raises FileNotFoundError.
    """
    monkeypatch.setenv("RKB_STRUCTURE", str(tmp_path / "missing.toml"))

    with pytest.raises(FileNotFoundError):
        config.find_config()


def test_find_config_local(tmp_path, monkeypatch):
    """
    Given no env var and a local structure.toml,
    when find_config runs,
    then it returns the local path.
    """
    monkeypatch.delenv("RKB_STRUCTURE", raising=False)
    local = tmp_path / "structure.toml"
    local.write_text("")
    monkeypatch.setattr(config, "_LOCAL_CONFIG", local)
    monkeypatch.setattr(
        config, "_DEFAULT_CONFIG", tmp_path / "unused" / "structure.toml"
    )

    assert config.find_config() == local


def test_find_config_default_fallback(tmp_path, monkeypatch):
    """
    Given no env var and no local config,
    when a default config exists,
    then find_config returns the default path.
    """
    monkeypatch.delenv("RKB_STRUCTURE", raising=False)
    default = tmp_path / "default" / "structure.toml"
    default.parent.mkdir()
    default.write_text("")
    monkeypatch.setattr(config, "_LOCAL_CONFIG", tmp_path / "no-such-local.toml")
    monkeypatch.setattr(config, "_DEFAULT_CONFIG", default)

    assert config.find_config() == default


def test_find_config_none_found(tmp_path, monkeypatch):
    """
    Given no env var, no local config, and no default config,
    when find_config runs,
    then it raises FileNotFoundError.
    """
    monkeypatch.delenv("RKB_STRUCTURE", raising=False)
    monkeypatch.setattr(config, "_LOCAL_CONFIG", tmp_path / "no-local.toml")
    monkeypatch.setattr(config, "_DEFAULT_CONFIG", tmp_path / "no-default.toml")

    with pytest.raises(FileNotFoundError):
        config.find_config()


def test_load_structure(tmp_path, monkeypatch):
    """
    Given a structure.toml with playlists and ignored genres,
    when load_structure runs,
    then it returns the parsed structure and ignored set, dropping malformed paths.
    """
    cfg = tmp_path / "structure.toml"
    cfg.write_text(
        """
        [ignored_genres]
        genres = ["Loop Samples", "Remix"]

        [[playlist]]
        path = ["ROOT", "Playlist A"]
        genres = ["Genre 1", "Genre 2"]

        [[playlist]]
        path = ["ROOT", "Playlist B"]
        genres = []

        [[playlist]]
        path = ["TOO", "MANY", "PARTS"]
        genres = ["Ignored Entry"]
        """
    )
    monkeypatch.setenv("RKB_STRUCTURE", str(cfg))

    structure, ignored = config.load_structure()

    assert ignored == {"Loop Samples", "Remix"}
    assert structure == {
        "ROOT": {
            "Playlist A": ["Genre 1", "Genre 2"],
            "Playlist B": [],
        }
    }
