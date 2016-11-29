#!/usr/bin/python3
# -*- coding: utf-8 -*-


import pickle
import urllib

from bs4 import BeautifulSoup


LYRICS = []
OUTPUT_PICKLE_PATH = 'lyrics_pickle_output_letras_de_musicas'


def save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names):
    for lyrics_name, lyrics in zip(artist_lyrics_names, artist_lyrics):
        LYRICS.append((website_name, artist_name, lyrics_name, lyrics))


def crawl_letras():
    def get_artists_URLs(home_html):
        def is_artist(tag):
            try:
                return (tag.name == "a"
                        and tag.parent.name == "li"
                        and tag.parent.parent.name == "ol"
                        and tag.parent.parent.parent.name == "div"
                        and "lst1" in tag.parent.parent.parent["class"])
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
                        and tag.parent.parent.name == "ol"
                        and tag.parent.parent.parent.name == "div"
                        and "lst1" in tag.parent.parent.parent["class"])
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
                return tag.name == "p" and "pumSum" in tag["class"]
            except:
                return False

        soup = BeautifulSoup(lyrics_html, 'html.parser')
        lyrics_tags = soup.find_all(is_lyrics)
        try:
            string_inside = str(lyrics_tags[0])
        except IndexError:
            return ''
        string_inside = string_inside[string_inside.find(">") + 1: string_inside.rfind('</')]
        clean_string_inside = '\n'.join(string_inside.split('<br/>'))
        return clean_string_inside

    website_name = 'letrasdemusicas.com.br'
    base_url = 'http://www.letrasdemusicas.com.br'
    start_url = 'http://www.letrasdemusicas.com.br/listagemartistas/a/'

    for page_num in range(1, 107):
        page = start_url + str(page_num) + '.html'
        home_html = urllib.request.urlopen(page).read()
        artists_URLs = get_artists_URLs(home_html)
        for artist_URL in artists_URLs:
            artist_name = artist_URL.strip('/')
            artist_lyrics_names = []
            artist_lyrics = []
            artist_full_URL = base_url + artist_URL + "maisletras/"
            artist_html = urllib.request.urlopen(artist_full_URL).read()
            songs_URLs = get_songs_URLs(artist_html)
            print(artist_name)
            for song_URL in songs_URLs:
                song_name = song_URL.split('/')[-2]
                song_html = urllib.request.urlopen(base_url + song_URL).read()
                artist_lyrics.append(get_lyrics(song_html))
                artist_lyrics_names.append(song_name)
                print('\t'+song_name)
            save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names)


if __name__ == '__main__':
    try:
        crawl_letras()
    finally:
        pickle.dump(LYRICS, open(OUTPUT_PICKLE_PATH, 'wb'))
