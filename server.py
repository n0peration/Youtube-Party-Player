#!/usr/bin/python
# -*- coding: utf8 -*-

import socket
import webbrowser
import gdata
import gdata.youtube
import gdata.youtube.service
import re
from collections import deque
from socket import AF_INET, SOCK_STREAM

OPENURL = "url "
SEARCH = "play "
END = "fin "

class Logger(object):
    """Simple Logger"""
    
    def info(self, data):
        print("log: {0}".format(data))

    def warning(self, data):
        print("warning: {0}".format(data))

    def error(self, data):
        print("error: {0}".format(data))

    def debug(self, data):
        print("debug: {0}".format(data))

    def recv(self, data):
        print("<< {0}".format(data))

class PartyServer(object):

    def __init__(self):
        self.playlist = deque([])
        self.log = Logger()
        self.currently_playing = False
        self.sock = None

    def start(self):
        self.sock = socket.socket(AF_INET, SOCK_STREAM)
        host = socket.gethostname()
        port = 3421
        self.sock.bind(("", port))

        # wait for client
        self.sock.listen(1)


    def start_receiving(self):
        while True:
            c, addr = self.sock.accept()
            self.log.info("{0} connected".format(addr))
            data = c.recv(1024)
            if not data:
                self.log.warning("Failed to receive data, try again.")
                c.close()
                continue
            self.log.recv(data)
            url = ""

            if data.startswith(OPENURL):
                url = data[len(OPENURL):]
            elif data.startswith(SEARCH):
                subject = data[len(SEARCH):]
                self.log.info("Searching on youtube for {0}...".format(subject))
                feed = self.search_youtube(subject)
                if not feed or len(feed.entry) == 0:
                    c.close()
                    continue
                firstentry = feed.entry[0]
                url = firstentry.media.player.url
            elif data.startswith(END):
                self.try_play_next()

            try:
                if url:
                    if "youtu" in url:
                        video_id = self.get_youtube_id_from_url(url)
                        if not video_id:
                            self.log.error("video_id was None: {0}".format(url))
                            raise
                        if self.currently_playing == True:
                            self.playlist.append(video_id)
                            self.log.info("added url to playlist")
                        else:
                            self.open_webplayer_with_id(video_id)
                    else:
                        self.open_url(url)
            finally:
                c.close()

    def try_play_next(self):
        self.currently_playing = False
        if len(self.playlist) > 0:
            self.open_webplayer_with_id(self.playlist.popleft())

    def search_youtube(self, search_terms, orderby="relevance", racy="include"):
        """Returns a feed containing the entrys"""
        service = gdata.youtube.service.YouTubeService()
        query = gdata.youtube.service.YouTubeVideoQuery()
        query.vq = search_terms
        query.orderby = orderby
        query.racy = racy
        feed = service.YouTubeQuery(query)
        return feed

    def open_url(self, url):
        self.log.info("Opening URL: {0}\n".format(url))
        webbrowser.open(url, new=0)

    def get_youtube_id_from_url(self, url):
        video_id = None
        if "youtu.be" in url:
            match = re.match(".*youtu\.be\/(.{11}).*", url)
        else:
            match = re.match(".*[&|\?]v=(.{11}).*", url)

        if match:
            video_id = match.groups()[0]
        return video_id

    def open_webplayer_with_id(self, video_id):
        if not video_id:
            self.log.error("Error: open_webplayer_with_id, video_id was None")
        webplayer_url = "http://localhost:8880/player/?videoID={0}".format(video_id)
        webbrowser.open(webplayer_url, new=0)
        self.currently_playing = True

def main():
    server = PartyServer()
    server.start()
    while True:
        try:
            server.start_receiving()
        except KeyboardInterrupt:
            print("Command me! [unlock|playlist]")
            cmd = raw_input()
            if cmd == "unlock":
                server.try_play_next()
            elif cmd == "playlist":
                print((server.playlist))

if __name__ == "__main__":
    main()
