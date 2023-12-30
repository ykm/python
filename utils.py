#!/usr/bin/python3

import os
import re
import fnmatch
import bs4
import enum
import requests
import six

from collections import namedtuple


def ls(path, pattern=None, ignore=None):
    for directory, subdirs, files in os.walk(path):
        for i in files:
            if ignore and i in ignore:
                continue

            if pattern and not re.match(pattern, i, re.I):
                continue

            yield os.path.join(directory, i)


def search(path, pattern=None):
    regex = fnmatch.translate(pattern)
    for i in ls(path, pattern=regex):
        print(i)



class HNMode(enum.Enum):
    top = "news"
    newest = "newest"
    comments = "comments"
    ask = "ask"
    show = "show"
    jobs = "jobs"


Story = namedtuple("Story", ["id", "rank", "title", "url", "user", "upvotes", "timestamp"])

        
class HackerNews(object):

    BASE_URL = "https://news.ycombinator.com"

    def __init__(self, count=30, mode="top"):
        self.count = count
        self.mode = (
            getattr(HNMode, mode, HNMode.top)
            if isinstance(mode, six.string_types)
            else mode
        )
        self.current_page = 1

    def getUrl(self, mode=None, nextPage=False):
        url = HackerNews.BASE_URL
        mode = mode or self.mode
        if mode != HNMode.top:
            url += "/" + mode.value

        if nextPage:
            self.current_page += 1
            url += "/?p={0}".format(self.current_page)

        return url

    def extract(self, html, partial=False):
        b = bs4.BeautifulSoup(html, features="lxml")
        for element in b.find_all(attrs={"class": "athing"}):
            story = {}
            story["id"] = element.attrs.get("id")
            rankElem = element.find(attrs={"class": "rank"})
            story["rank"] = getattr(rankElem, "text", "")
            titleLine = element.find(attrs={"class": "titleline"})
            title = titleLine.find_next(name="a", href=True)
            story["url"] = getattr(title, "attrs", {}).get("href")
            if story["url"] and partial:
                story["url"] = HackerNews.BASE_URL + "/" + story["url"]

            story["title"] = getattr(title, "text", "")
            story["user"] = None
            story["upvotes"] = None
            story["timestamp"] = None
            yield Story(**story)

    def get(self, mode=None, nextPage=False):
        """ Get the stories from the request HN page. """
        mode = mode or self.mode
        url = self.getUrl(mode=mode, nextPage=nextPage)
        res = requests.get(url)
        print("url: '{0}', status_code='{1}'".format(url, res.status_code))
        if res.status_code == 200:
            html = res.text
            stories = [i for i in self.extract(html, partial=mode == HNMode.ask)]
            return stories

        return []
    

if __name__ == "__main__":
    for i in HackerNews(mode="newest").get():
        print(i)
