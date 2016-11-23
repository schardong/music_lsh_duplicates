#!/usr/bin/python3
# -*- coding: utf-8 -*-


import pickle
import urllib

from bs4 import BeautifulSoup


LYRICS = []
OUTPUT_PICKLE_PATH = 'lyrics_pickle_output_1'


def save_artist_lyrics(artist_name, artist_lyrics, artist_lyrics_names):
    for lyrics_name, lyrics in zip(artist_lyrics_names, artist_lyrics):
        LYRICS.append(('letras.mus.br', artist_name, lyrics_name, lyrics))


def crawl_letras():
    def get_artists_URLs(home_html):
        def is_artist(tag):
            try:
                return (tag.name == "a"
                        and tag.parent.name == "li"
                        and tag.parent.parent.name == "ul"
                        and "cnt-list" in tag.parent.parent["class"]
                        and tag.parent.parent.parent.name == "div"
                        and "artistas-a" in tag.parent.parent.parent["class"])
            except:
                return False

        ret = []
        soup = BeautifulSoup(home_html, 'html.parser')
        artists_a_tag_list = soup.find_all(is_artist)
        for artist_a_tag in artists_a_tag_list:
            ret.append(artist_a_tag["href"])
        return ret

    def get_songs_URLs(artist_html):
        def is_song(tag):
            try:
                return (tag.name == "a"
                        and tag.parent.name == "li"
                        and tag.parent.parent.name == "ul"
                        and "cnt-list" in tag.parent.parent["class"]
                        and tag.parent.parent.parent.name == "div"
                        and "cnt-list--alp" in tag.parent.parent.parent["class"])
            except:
                return False

        ret = []
        soup = BeautifulSoup(artist_html, 'html.parser')
        songs_a_tag_list = soup.find_all(is_song)
        for song_a_tag in songs_a_tag_list:
            ret.append(song_a_tag["href"])
        return ret

    def get_lyrics(lyrics_html):
        def is_lyrics(tag):
            try:
                return (tag.name == "p"
                        and tag.parent.name == "article"
                        and tag.parent.parent.name == "div"
                        and "cnt-letra" in tag.parent.parent["class"])
            except:
                return False

        ret = []
        soup = BeautifulSoup(lyrics_html, 'html.parser')
        lyrics_tags = soup.find_all(is_lyrics)
        for p_tag in lyrics_tags:
            string_inside = str(p_tag).lstrip('<p>').rstrip('</p>')
            clean_string_inside = '\n'.join(string_inside.split('<br/>'))
            ret.append(clean_string_inside)
        return '\n'.join(ret)

    base_url = 'https://www.letras.mus.br'
    start_url = 'https://www.letras.mus.br/letra/A/artistas.html'

    home_html = urllib.request.urlopen(start_url).read()
    artists_URLs = get_artists_URLs(home_html)
    for artist_URL in artists_URLs:
        artist_name = artist_URL.rstrip('/')
        artist_lyrics_names = []
        artist_lyrics = []
        artist_full_URL = base_url + artist_URL
        artist_html = urllib.request.urlopen(artist_full_URL).read()
        songs_URLs = get_songs_URLs(artist_html)
        print(artist_name[1:])
        for song_URL in songs_URLs:
            song_name = song_URL.split('/')[-2]
            song_html = urllib.request.urlopen(base_url + song_URL).read()
            artist_lyrics.append(get_lyrics(song_html))
            artist_lyrics_names.append(song_name)
            print('\t'+song_name)
        # Let's remove the leadind '/' in the artist name.
        save_artist_lyrics(artist_name[1:], artist_lyrics, artist_lyrics_names)


def crawl_vagalume():
    start_url = 'https://www.vagalume.com.br/browse/a.html'


def crawl_musica():
    start_url = 'http://www.musica.com/letras.asp?g=A'


def crawl_cifraclub():
    start_url = 'https://www.cifraclub.com.br/cifras/letra_a.html'


def crawl_letrasdemusicas():
    start_url = 'http://www.letrasdemusicas.com.br/listagemartistas/a.html'


if __name__ == '__main__':
    try:
        crawl_letras()
    finally:
        pickle.dump(LYRICS, open(OUTPUT_PICKLE_PATH, 'wb'))
    # crawl_vagalume()
    # crawl_musica()
    # crawl_cifraclub()
    # crawl_letrasdemusicas()
