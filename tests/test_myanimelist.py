import pytest

from myanimebot.myanimelist import break_rss_description_string, get_thumbnail
from myanimebot.utils import MediaStatus

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


def test_break_rss_description_string():

    status, progress, episodes = break_rss_description_string('Completed - 12 of 12 episodes')
    assert status == MediaStatus.COMPLETED
    assert progress == '12'
    assert episodes == '12'

    status, progress, episodes = break_rss_description_string('Completed - 192 of 192 chapters')
    assert status == MediaStatus.COMPLETED
    assert progress == '192'
    assert episodes == '192'

    status, progress, episodes = break_rss_description_string('Paused - 24 of 192 chapters')
    assert status == MediaStatus.PAUSED
    assert progress == '24'
    assert episodes == '192'

    status, progress, episodes = break_rss_description_string('On-hold - 23 of 27 episodes')
    assert status == MediaStatus.PAUSED
    assert progress == '23'
    assert episodes == '27'

    status, progress, episodes = break_rss_description_string('Dropped - 17 of 11 episodes')
    assert status == MediaStatus.DROPPED
    assert progress == '17'
    assert episodes == '11'

    status, progress, episodes = break_rss_description_string('Watching - 1 of 2 episodes')
    assert status == MediaStatus.CURRENT
    assert progress == '1'
    assert episodes == '2'

    status, progress, episodes = break_rss_description_string('Reading - 192 of ? chapters')
    assert status == MediaStatus.CURRENT
    assert progress == '192'
    assert episodes == '?'

    status, progress, episodes = break_rss_description_string('Rewatching - 0 of 1 episodes')
    assert status == MediaStatus.REPEATING
    assert progress == '0'
    assert episodes == '1'

    # Incorrect cases
    status, progress, episodes = break_rss_description_string('Toto')
    assert status == None and progress == None and episodes == None

    status, progress, episodes = break_rss_description_string('Completed - blabla')
    assert status == None and progress == None and episodes == None

    status, progress, episodes = break_rss_description_string('Completed - 24 of 32')
    assert status == None and progress == None and episodes == None

    with pytest.raises(NotImplementedError):
        break_rss_description_string('Toto - 24 of 32 episodes')
