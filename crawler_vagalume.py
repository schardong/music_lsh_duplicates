#!/usr/bin/python3
# -*- coding: utf-8 -*-


import pickle
import urllib
import time

from bs4 import BeautifulSoup


LYRICS = []
OUTPUT_PICKLE_PATH = 'out/lyrics_vagalume.pickle'
READ_ALL_ARTISTS = False
CURRENT_ARTIST = 'ajay-atul'
SAVED_CURRENT_ARTIST_LYRICS = False


def save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names):
    for lyrics_name, lyrics in zip(artist_lyrics_names, artist_lyrics):
        LYRICS.append((website_name, artist_name, lyrics_name, lyrics))


def crawl_vagalume():
    def get_artists_URLs(home_html):
        def is_artist(tag):
            try:
                # .meio_no_block div ol li a
                return (tag.name == "a"
                        and tag.parent.name == "li"
                        and tag.parent.parent.name == "ol"
                        and tag.parent.parent.parent.name == "div"
                        and tag.parent.parent.parent.parent.name == "div"
                        and "meio_no_block" in tag.parent.parent.parent.parent["class"])
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
                # .vscroll .tracks li a
                return (tag.name == "a"
                        and tag.parent.name == "li"
                        and tag.parent.parent.name == "ul"
                        and "tracks" in tag.parent.parent["class"]
                        and tag.parent.parent.parent.name == "div"
                        and "vscroll" in tag.parent.parent.parent["class"])
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
                # .left.originalOnly div
                return (tag.name == "div"
                        and tag.parent.name == "div"
#                         and "originalOnly" in tag.parent["class"])
                        and "lyr_original" == tag.parent["id"])
            except:
                return False

        ret = []
        soup = BeautifulSoup(lyrics_html, 'html.parser')
        lyrics_tags = soup.find_all(is_lyrics)
        for div_tag in lyrics_tags:
            string_inside = str(div_tag).lstrip('<div itemprop="description">').rstrip('</div>')
            clean_string_inside = '\n'.join(string_inside.split('<br/>'))
            ret.append(clean_string_inside)
        return '\n'.join(ret)
    
    website_name = 'vagalume.com.br'
    base_url = 'https://www.vagalume.com.br'
    start_url = 'https://www.vagalume.com.br/browse/a.html'

    global CURRENT_ARTIST
    global SAVED_CURRENT_ARTIST_LYRICS
    global READ_ALL_ARTISTS

    SAVED_CURRENT_ARTIST_LYRICS = False
    artist_already_seen = True

    home_html = urllib.request.urlopen(start_url).read()
    artists_URLs = get_artists_URLs(home_html)
    for artist_URL in artists_URLs:
        artist_name = artist_URL.lstrip('/').rstrip('/')
        
        if artist_name == CURRENT_ARTIST or CURRENT_ARTIST == '':
            artist_already_seen = False
        
        if artist_already_seen:
            continue
        
        CURRENT_ARTIST = artist_name
        SAVED_CURRENT_ARTIST_LYRICS = False

        artist_lyrics_names = []
        artist_lyrics = []
        artist_full_URL = base_url + artist_URL
        artist_html = urllib.request.urlopen(artist_full_URL).read()
        songs_URLs = get_songs_URLs(artist_html)
        print(artist_name)
        for song_URL in songs_URLs:
            song_name = song_URL.split('/')[-1].rstrip('.html')
            song_html = urllib.request.urlopen(base_url + song_URL).read()
            artist_lyrics.append(get_lyrics(song_html))
            artist_lyrics_names.append(song_name)
            print('\t'+song_name)
        save_artist_lyrics(website_name, artist_name, artist_lyrics, artist_lyrics_names)
        SAVED_CURRENT_ARTIST_LYRICS = True
    
    READ_ALL_ARTISTS = True


if __name__ == '__main__':
    try:
        while not READ_ALL_ARTISTS:
            try:
                crawl_vagalume()
            except Exception as e:
                print("Error reading artist %s.\n%s" % (CURRENT_ARTIST, str(e)))
                
                if SAVED_CURRENT_ARTIST_LYRICS:
                    print("Removing last element in list.")
                    LYRICS.pop()
                
                print("Waiting 3 seconds to continue...")
                time.sleep(3)
    finally:
        pickle.dump(LYRICS, open(OUTPUT_PICKLE_PATH, 'wb'))
