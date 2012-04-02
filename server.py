#!/usr/bin/python
# -*- coding: utf8 -*-

import socket
import webbrowser
import gdata.youtube.service as yt_service
import json
import urllib2
import re
from log import Logger, Level, put_stdout
from collections import deque
from socket import AF_INET, SOCK_STREAM

OPENURL = "url "
SEARCH = "play "
END = "fin "
DEL = "del "
log = Logger(put_stdout, Level.DEBUG)

def search_youtube(search_terms, orderby="relevance", racy="include"):
    """Returns a feed containing the entrys from the gdata youtube query"""
    service = yt_service.YouTubeService()
    query = yt_service.YouTubeVideoQuery()
    query.vq = search_terms
    query.orderby = orderby
    query.racy = racy
    feed = service.YouTubeQuery(query)
    return feed

def open_url(url):
    """Opens a URL in the default browser"""
    log.info("Opening URL: {0}\n".format(url))
    webbrowser.open(url, new=0)

def get_youtube_id_from_url(url):
    """Extracts the video id from a youtube URL"""
    video_id = None
    if "youtu.be" in url:
        match = re.match(".*youtu\.be\/(.{11}).*", url)
    else:
        match = re.match(".*[&|\?]v=(.{11}).*", url)

    if match:
        video_id = match.groups()[0]
    return video_id

def get_youtube_info_by_id(video_id):
    ytclient = yt_service.YouTubeService()
    video_entry = ytclient.GetYouTubeVideoEntry(video_id=video_id)
    if video_entry:
        duration = int(video_entry.media.duration.seconds)
        durationstr = str(duration/60) + ":" + str(duration%60)
        title = video_entry.media.title.text

    return {"id": video_id, "runtime": durationstr, "title": title}

def open_webplayer_with_id(video_id):
    if not video_id:
        log.error("Error: open_webplayer_with_id, video_id was None")
    webplayer_url = "http://localhost:8880/player/?videoID={0}".format(video_id)
    webbrowser.open(webplayer_url, new=0)

def try_play_next(playlist):
    if len(playlist) > 0:
        open_webplayer_with_id(playlist[0]["id"])
    else:
        send_playlist_to_server(playlist)

#def skip(playlist):
#    """Skips the current video"""
#    if len(playlist) > 1:
#        playlist.popleft()
#        send_playlist_to_server(playlist)
#        try_play_next(playlist)

def send_playlist_to_server(playlist):
    log.debug("Sending playlist to webserver")
    jdata = json.dumps(list(playlist))
    urllib2.urlopen("http://127.0.0.1:8880/callback", jdata)

def delete_from_playlist(playlist, video_id):
    log.debug("Trying to delete {0}".format(video_id))
    newplaylist = deque([e for e in playlist if e["id"] != video_id])
#    for e in playlist:
#        #log.debug("{0} == {1} ?".format(video_id, e["id"]))
#        if video_id == e["id"]:
#            log.info("Deleting {0} from playlist".format(str(e)))
#            playlist.remove(e)
#            send_playlist_to_server(playlist)
#            return 0
    if len(newplaylist) < len(playlist):
        log.info("Deleted {0} from playlist".format(video_id))
        send_playlist_to_server(playlist)
    else:
        log.debug("Could not find {0} in playlist!".format(video_id))

    return newplaylist

def is_id_in_playlist(playlist, video_id):
    for e in playlist:
        if video_id == e["id"]:
            return True
    return False

def receive(sock, playlist):
    c, addr = sock.accept()
    log.info("{0} connected".format(addr))
    data = c.recv(1024)
    if not data:
        log.warning("Failed to receive data, try again.")
        c.close()
        raise
    log.recv(data)
    url = ""

    if data.startswith(OPENURL):
        url = data[len(OPENURL):]
    elif data.startswith(SEARCH):
        subject = data[len(SEARCH):]
        log.info("Searching on youtube for {0}...".format(subject))
        feed = search_youtube(subject)
        if not feed or len(feed.entry) == 0:
            log.warning("Could not find \"{0}\" on youtube!".format(subject))
            c.close()
            raise
        log.info("Found \"{0}\" on youtube!".format(subject))
        firstentry = feed.entry[0]
        url = firstentry.media.player.url
    elif data.startswith(END):
        video_id = data[len(END):]
        if len(playlist) > 0 and playlist[0]["id"] == video_id:
            playlist.popleft()
            send_playlist_to_server(playlist)
            try_play_next(playlist)
        #d = delete_from_playlist(playlist, video_id)
        #if d == 0:
        #    try_play_next(playlist)
    elif data.startswith(DEL):
        video_id = data[len(DEL):]
        if playlist[0]["id"] != video_id:
            playlist = delete_from_playlist(playlist, video_id)

    try:
        if url:
            if "youtu" in url:
                video_id = get_youtube_id_from_url(url)
                if not video_id:
                    log.error("video_id was None: {0}".format(url))
                    raise
                else:
                    entry = get_youtube_info_by_id(video_id)

                    if not is_id_in_playlist(playlist, video_id):
                        playlist.append(entry)
                        log.info("Added {0} to playlist".format(entry))
                        send_playlist_to_server(playlist)
                        if len(playlist) == 1:
                            try_play_next(playlist)
            else:
                open_url(url)
    finally:
        c.close()


def start():
    sock = socket.socket(AF_INET, SOCK_STREAM)
    host = socket.gethostname()
    port = 3421
    sock.bind(("", port))

    # wait for client
    sock.listen(1)

    return sock

def main():

    # playlist
    playlist = deque([])
    # the server socket
    sock = start()

    while True:
        try:
            receive(sock, playlist)
        except KeyboardInterrupt:
            print("[skip|playlist]")
            cmd = raw_input()
            # this will try to play the next video even if the current one is not finished
            if cmd == "skip":
                try_play_next(playlist)
            elif cmd == "playlist":
                print(playlist)
        except:
            continue

if __name__ == "__main__":
    main()
