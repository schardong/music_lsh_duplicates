#!/usr/bin/python3
# -*- coding: utf-8 -*-


import pickle
import urllib

from bs4 import BeautifulSoup


LYRICS = []
OUTPUT_PICKLE_PATH = 'lyrics_pickle_output_musica'


def save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names):
    for lyrics_name, lyrics in zip(artist_lyrics_names, artist_lyrics):
        LYRICS.append((website_name, artist_name, lyrics_name, lyrics))


def crawl_musica():
    def get_artists_URLs(home_html):
        def is_artist(tag):
            try:
                return (tag.name == "a"
                        and tag["href"][:18] == "letras.asp?letras=")
            except:
                return False

        def get_artist_name(tag):
            return tag.contents[1].strip()

        ret = []
        soup = BeautifulSoup(home_html, 'html.parser')
        artists_a_tag_list = soup.find_all(is_artist)
        for artist_a_tag in artists_a_tag_list:
            ret.append((artist_a_tag["href"], get_artist_name(artist_a_tag)))
        return ret

    def get_songs_URLs(artist_html):
        def is_song(tag):
            try:
                return (tag.name == "a"
                        and tag["href"][:17] == "letras.asp?letra="
                        and tag.contents[1][:11] == " Letras de ")
            except:
                return False

        def get_song_name(tag):
            s = tag.contents[1]
            return s[s.find(' - ') + 3:]

        ret = []
        soup = BeautifulSoup(artist_html, 'html.parser')
        songs_a_tag_list = soup.find_all(is_song)
        for song_a_tag in songs_a_tag_list:
            ret.append((song_a_tag["href"], get_song_name(song_a_tag)))
        return ret

    def get_lyrics(lyrics_html):
        def is_lyrics(tag):
            try:
                return (tag.name == "p"
                        and tag.parent.name == "td"
                        and tag.parent.parent.name == "tr")
            except:
                return False

        soup = BeautifulSoup(lyrics_html, 'html.parser')
        lyrics_tags = soup.find_all(is_lyrics)
        string_inside = str(lyrics_tags[0])
        string_inside = string_inside[string_inside.find('">') + 2: string_inside.rfind('</font')]
        clean_string_inside = '\n'.join(string_inside.replace('\r', '').replace('</br>', '').replace('<br/>', '').split(
            '<br>'))
        return clean_string_inside

    website_name = 'musica.com'
    base_url = 'http://www.musica.com/'
    start_url = 'http://www.musica.com/letras.asp?g=A&ver=ALL'

    home_html = urllib.request.urlopen(start_url).read()
    artists_URLs = get_artists_URLs(home_html)
    for artist_URL, artist_name in artists_URLs:
        artist_lyrics_names = []
        artist_lyrics = []
        artist_full_URL = base_url + artist_URL
        artist_html = urllib.request.urlopen(artist_full_URL).read()
        songs_URLs = get_songs_URLs(artist_html)
        print(artist_name)
        for song_URL, song_name in songs_URLs:
            song_html = urllib.request.urlopen(base_url + song_URL).read()
            try:            
                artist_lyrics.append(get_lyrics(song_html))
                artist_lyrics_names.append(song_name)
                print('\t' + song_name)
            except:
                pass
        save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names)


if __name__ == '__main__':
    try:
        crawl_musica()
    finally:
        pickle.dump(LYRICS, open(OUTPUT_PICKLE_PATH, 'wb'))
