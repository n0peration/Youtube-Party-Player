#!/usr/bin/python
# -*- coding: utf8 -*-

import socket
import webbrowser
import gdata
import gdata.youtube
import gdata.youtube.service
import json
import urllib2
import re
from collections import deque
from socket import AF_INET, SOCK_STREAM

OPENURL = "url "
SEARCH = "play "
END = "fin "
DEL = "del "

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
                    self.log.warning("Could not find \"{0}\" on youtube!".format(subject))
                    c.close()
                    continue
                self.log.warning("Found \"{0}\" on youtube!".format(subject))
                firstentry = feed.entry[0]
                url = firstentry.media.player.url
            elif data.startswith(END):
                video_id = data[len(END):]
                d = self.delete_from_playlist(video_id)
                if d == 0:
                    self.try_play_next()
            elif data.startswith(DEL):
                video_id = data[len(DEL):]
                if self.playlist[0]["id"] != video_id:
                    self.delete_from_playlist(video_id)

            try:
                if url:
                    if "youtu" in url:
                        video_id = self.get_youtube_id_from_url(url)
                        if not video_id:
                            self.log.error("video_id was None: {0}".format(url))
                            raise
                        else:
                            entry = self.get_youtube_info_by_id(video_id)

                            if not self.id_in_playlist(video_id):
                                self.playlist.append(entry)
                                self.log.info("added {0} to playlist".format(entry))
                                self.send_playlist_to_server()
                                if len(self.playlist) == 1:
                                    self.try_play_next()
                    else:
                        self.open_url(url)
            finally:
                c.close()

    def id_in_playlist(self, video_id):
        for e in self.playlist:
            if video_id == e["id"]:
                return True
        return False

    def delete_from_playlist(self, video_id):
        self.log.debug("Trying to delete {0}".format(video_id))
        for e in self.playlist:
            self.log.debug("{0} == {1} ?".format(video_id, e["id"]))
            if video_id == e["id"]:
                self.log.info("Deleting {0} from playlist".format(str(e)))
                self.playlist.remove(e)
                self.send_playlist_to_server()
                return 0
                #break
        return -1

    def send_playlist_to_server(self):
        self.log.info("sending playlist to webserver")
        jdata = json.dumps(list(self.playlist))
        urllib2.urlopen("http://127.0.0.1:8880/callback", jdata)

    def try_play_next(self):
        if len(self.playlist) > 0:
            self.open_webplayer_with_id(self.playlist[0]["id"])
        else:
            self.send_playlist_to_server()

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

    def get_youtube_info_by_id(self, v_id):
        ytclient = gdata.youtube.service.YouTubeService()
        video = ytclient.GetYouTubeVideoEntry(video_id=v_id)
        if video:
            duration = int(video.media.duration.seconds)
            durationstr = str(duration/60) + ":" + str(duration%60)
            title = video.media.title.text

        return {"id": v_id, "runtime": durationstr, "title": title}

    def open_webplayer_with_id(self, video_id):
        if not video_id:
            self.log.error("Error: open_webplayer_with_id, video_id was None")
        webplayer_url = "http://localhost:8880/player/?videoID={0}".format(video_id)
        webbrowser.open(webplayer_url, new=0)

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
                print(server.playlist)

if __name__ == "__main__":
    main()
