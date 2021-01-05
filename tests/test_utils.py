import pytest

from myanimebot.utils import MediaType, Service, filter_name, replace_all, truncate_end_show
from myanimebot.globals import SERVICE_MAL, SERVICE_ANILIST

def test_MediaType_from_str():
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


def test_Service_from_str():
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

    # Testing incorrect Services
    with pytest.raises(NotImplementedError, match='Cannot convert "Kitsu" to a Service'):
        Service.from_str('Kitsu')
    with pytest.raises(NotImplementedError, match='Cannot convert "toto" to a Service'):
        Service.from_str('toto')
    with pytest.raises(NotImplementedError, match='Cannot convert "ani list" to a Service'):
        Service.from_str('ani list')
    with pytest.raises(NotImplementedError, match='Cannot convert "mla" to a Service'):
        Service.from_str('mla')


def test_replace_all():
    with pytest.raises(AttributeError):
        replace_all("texte", []) == "texte"

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

