import pytest

from myanimebot.myanimelist import get_thumbnail

def test_get_thumbnail():
    # Test manga
    try:
        link = "https://myanimelist.net/manga/103890/Bokutachi_wa_Benkyou_ga_Dekinai"
        expected_thumbnail = "https://cdn.myanimelist.net/images/manga/3/197080.jpg"
        assert get_thumbnail(link) == expected_thumbnail
    except Exception:
        pytest.fail("Should not raise Exception")

    # Test anime
    try:
        link = "https://myanimelist.net/anime/40028/Shingeki_no_Kyojin__The_Final_Season"
        expected_thumbnail = "https://cdn.myanimelist.net/images/anime/1000/110531.jpg"
        assert get_thumbnail(link) == expected_thumbnail
    except Exception:
        pytest.fail("Should not raise Exception")

    # Test anime 2
    try:
        link = "https://myanimelist.net/anime/40028"
        expected_thumbnail = "https://cdn.myanimelist.net/images/anime/1000/110531.jpg"
        assert get_thumbnail(link) == expected_thumbnail
    except Exception:
        pytest.fail("Should not raise Exception")

    # Test fail
    with pytest.raises(Exception):
        get_thumbnail('')

    with pytest.raises(Exception):
        get_thumbnail('https://myanimelist.net/anime/test/')
        
    with pytest.raises(Exception):
        get_thumbnail('https://anilist.co/anime/110277/Attack-on-Titan-Final-Season/')

