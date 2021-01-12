import pytest

from myanimebot.utils import Media, MediaStatus, MediaType, Service, filter_name, replace_all, truncate_end_show
from myanimebot.globals import SERVICE_MAL, SERVICE_ANILIST

def test_MediaType_from_str():
    try:
        # Testing for ANIME
        assert MediaType.ANIME == MediaType.from_str('ANIME')
        assert MediaType.ANIME == MediaType.from_str('anime')
        assert MediaType.ANIME == MediaType.from_str('ANiMe')
        assert MediaType.ANIME == MediaType.from_str('anime_list')
        assert MediaType.ANIME == MediaType.from_str('ANIME_LIST')
        assert MediaType.ANIME == MediaType.from_str('ANiMe_LiST')

        # Testing for MANGA
        assert MediaType.MANGA == MediaType.from_str('MANGA')
        assert MediaType.MANGA == MediaType.from_str('manga')
        assert MediaType.MANGA == MediaType.from_str('ManGA')
        assert MediaType.MANGA == MediaType.from_str('manga_list')
        assert MediaType.MANGA == MediaType.from_str('MANGA_LIST')
        assert MediaType.MANGA == MediaType.from_str('ManGA_LiSt')
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    # Testing incorrect MediaType
    with pytest.raises(NotImplementedError, match='Cannot convert "TEST_LIST" to a MediaType'):
        MediaType.from_str('TEST_LIST')
    with pytest.raises(NotImplementedError, match='Cannot convert "Blabla" to a MediaType'):
        MediaType.from_str('Blabla')
    with pytest.raises(NotImplementedError, match='Cannot convert "Toto" to a MediaType'):
        MediaType.from_str('Toto')
    with pytest.raises(NotImplementedError, match='Cannot convert "ANIMU" to a MediaType'):
        MediaType.from_str('ANIMU')
    with pytest.raises(NotImplementedError, match='Cannot convert "mango" to a MediaType'):
        MediaType.from_str('mango')
    with pytest.raises(NotImplementedError):
        MediaType.from_str('')
    with pytest.raises(TypeError):
        MediaType.from_str(None)


def test_Service_from_str():
    try:
        # Testing for MAL
        assert Service.MAL == Service.from_str('MAL')
        assert Service.MAL == Service.from_str('MYANIMELIST')
        assert Service.MAL == Service.from_str(SERVICE_MAL)
        assert Service.MAL == Service.from_str('MaL')
        assert Service.MAL == Service.from_str('mal')
        assert Service.MAL == Service.from_str('myanimelist')
        assert Service.MAL == Service.from_str('mYANimEliST')

        # Testing for Anilist
        assert Service.ANILIST == Service.from_str('AniList')
        assert Service.ANILIST == Service.from_str('AL')
        assert Service.ANILIST == Service.from_str(SERVICE_ANILIST)
        assert Service.ANILIST == Service.from_str('ANILIST')
        assert Service.ANILIST == Service.from_str('anilist')
        assert Service.ANILIST == Service.from_str('al')
        assert Service.ANILIST == Service.from_str('Al')
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    # Testing incorrect Services
    with pytest.raises(NotImplementedError, match='Cannot convert "Kitsu" to a Service'):
        Service.from_str('Kitsu')
    with pytest.raises(NotImplementedError, match='Cannot convert "toto" to a Service'):
        Service.from_str('toto')
    with pytest.raises(NotImplementedError, match='Cannot convert "ani list" to a Service'):
        Service.from_str('ani list')
    with pytest.raises(NotImplementedError, match='Cannot convert "mla" to a Service'):
        Service.from_str('mla')
    with pytest.raises(TypeError):
        Service.from_str(None)


def test_replace_all():
    with pytest.raises(AttributeError):
        replace_all("texte", [])

    assert replace_all(None, {}) == None
    assert replace_all("toto", None) == "toto"

    assert replace_all("texte", {}) == "texte"
    assert replace_all("I is a string", {"is": "am"}) == "I am a string"
    assert replace_all("abcdef abcdef 123", {
        "a": "z",
        "2": "5",
        "c": "-"
        }) == "zb-def zb-def 153"

    assert replace_all("toto", {
        "to": "ta",
        "z": "ZUUU"
        }) == "tata"
    assert replace_all("", {
        "to": "ta",
        "z": "ZUUU"
        }) == ""
    assert replace_all("abcdcba", {
        "a": "0",
        "b": "1",
        "0": "z"
        }) == "z1cdc1z"


def test_filter_name():
    assert filter_name("Bonjour") == "Bonjour"
    assert filter_name("") == ""
    assert filter_name("Bonjour ♥") == "Bonjour \♥"
    assert filter_name("♥ Bonjour ♥") == "\♥ Bonjour \♥"
    assert filter_name("♥♪☆♂☆♀♀ ♥") == "\♥\♪\☆\♂\☆\♀\♀ \♥"
    assert filter_name("♣") == "♣"
    assert filter_name(None) == None


def test_truncate_end_show():
    assert truncate_end_show("Toto - TV") == "Toto"
    assert truncate_end_show("Toto - Movie") == "Toto"
    assert truncate_end_show("Toto - Special") == "Toto"
    assert truncate_end_show("Toto - OVA") == "Toto"
    assert truncate_end_show("Toto - ONA") == "Toto"
    assert truncate_end_show("Toto - Manga") == "Toto"
    assert truncate_end_show("Toto - Manhua") == "Toto"
    assert truncate_end_show("Toto - Manhwa") == "Toto"
    assert truncate_end_show("Toto - Novel") == "Toto"
    assert truncate_end_show("Toto - One-Shot") == "Toto"
    assert truncate_end_show("Toto - Doujinshi") == "Toto"
    assert truncate_end_show("Toto - Music") == "Toto"
    assert truncate_end_show("Toto - OEL") == "Toto"
    assert truncate_end_show("Toto - Unknown") == "Toto"
    
    assert truncate_end_show("Toto- TV") == "Toto"
    assert truncate_end_show("Toto- Music") == "Toto"
    assert truncate_end_show("Titi-Music") == "Titi-Music"
    assert truncate_end_show("- Music") == ""
    assert truncate_end_show(None) == None


def test_media_status():
    # Testing Current
    try:
        current = MediaStatus.CURRENT
        assert MediaStatus.from_str('read') == current
        assert MediaStatus.from_str('READ') == current
        assert MediaStatus.from_str('ReaD') == current
        assert MediaStatus.from_str('Reading') == current
        assert MediaStatus.from_str('READING') == current
        assert MediaStatus.from_str('reading') == current
        assert MediaStatus.from_str('watched') == current
        assert MediaStatus.from_str('WATCHING') == current
        assert MediaStatus.from_str('WATCHED') == current
        assert MediaStatus.from_str('watChing') == current
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Watchh')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Watches')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Red')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Watc hed')

    # Testing Planning
    try:
        planning = MediaStatus.PLANNING
        assert MediaStatus.from_str('PLANS') == planning
        assert MediaStatus.from_str('plans') == planning
        assert MediaStatus.from_str('PlAns') == planning
        assert MediaStatus.from_str('Plan') == planning
        assert MediaStatus.from_str('plan') == planning
        assert MediaStatus.from_str('PLAN') == planning
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('planned')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Pla')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('pla n')

    # Testing Completed
    try:
        completed = MediaStatus.COMPLETED
        assert MediaStatus.from_str('Completed') == completed
        assert MediaStatus.from_str('COMPLETED') == completed
        assert MediaStatus.from_str('completed') == completed
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Complete')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Compl eted')

    # Testing Dropped
    try:
        dropped = MediaStatus.DROPPED
        assert MediaStatus.from_str('DroPPed') == dropped
        assert MediaStatus.from_str('DROPPED') == dropped
        assert MediaStatus.from_str('dropped') == dropped
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Drop')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('Drops')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str(' Dropped')

    # Testing Paused
    try:
        paused = MediaStatus.PAUSED
        assert MediaStatus.from_str('PAUSED') == paused
        assert MediaStatus.from_str('paused') == paused
        assert MediaStatus.from_str('PaUSed') == paused
        assert MediaStatus.from_str('ON-HOLD') == paused
        assert MediaStatus.from_str('on-hold') == paused
        assert MediaStatus.from_str('ON-hold') == paused
        assert MediaStatus.from_str('on-HOLD') == paused
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('pauses')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('on hold')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('onhold')

    # Testing Repeating
    try:
        repeating = MediaStatus.REPEATING
        assert MediaStatus.from_str('reread') == repeating
        assert MediaStatus.from_str('REREAD') == repeating
        assert MediaStatus.from_str('reReaD') == repeating
        assert MediaStatus.from_str('reReading') == repeating
        assert MediaStatus.from_str('REREADING') == repeating
        assert MediaStatus.from_str('rereading') == repeating
        assert MediaStatus.from_str('rewatched') == repeating
        assert MediaStatus.from_str('REWATCHING') == repeating
        assert MediaStatus.from_str('reWATCHED') == repeating
        assert MediaStatus.from_str('RewatChing') == repeating
    except Exception as e:
        pytest.fail("Unexpected Exception : {}".format(e))

    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('rreread')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('rewatches')
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('re read')

    # Testing incorrect uses cases
    with pytest.raises(NotImplementedError):
        MediaStatus.from_str('')
    with pytest.raises(TypeError):
        MediaStatus.from_str(None)
