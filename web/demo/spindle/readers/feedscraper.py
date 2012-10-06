import feedparser
import pprint
from time import mktime
from datetime import datetime
from urlparse import urlparse
from os.path import basename, splitext
# from spindle.models import Item

# Scrape the OXITEMS RSS-of-RSS feed for audio and video files we
# should pull in
def rss_to_records(url):
    d = feedparser.parse(url)

    for entry in d.entries:
        dct = {}
        try:
            dct['duration'] = int(entry['duration'])
            dct['name'] = entry['title']
            dct['published'] = datetime.fromtimestamp(mktime(entry['published_parsed']))

            for link in entry.links:
                if 'shorttype' in link:
                    if link['shorttype'] == 'audio':
                        dct['url'] = link['href']
                        dct['type'] = 'audio'
                    elif link['shorttype'] == 'video':
                        dct['url'] = link['href']
                        dct['type'] = 'video'
                        
            # Keywords are <category> tags with no "scheme"; tags with
            # a "scheme" are iTunes-specific metadata
            if entry.tags:
                dct['keywords'] = u','.join(tag.term for tag in entry.tags 
                                            if tag.scheme is None)
            else:
                dct['keywords'] = ''

            if 'url' in dct:
                yield dct

        except(KeyError):
            pass

# Group together audio and video files that look like the same item
# into one record
# 
def records_to_items(items):
    # Two items are likely to represent the same content in different
    # forms if they have the same basename (foo.mp3 vs. foo.mpg), same
    # duration, and same title

    # A hash mapping keys of the form "TITLE/BASENAME/DURATION" into a
    # hash of URLs. Each hash of URLs maps a real .mp3 or .mpg URL to
    # the item record referring to it
    hash = {}

    for item in items:
        url = urlparse(item['url'])
        bname = splitext(basename(url.path))[0]
        key = u"{}/{}/{:d}".format(item['name'],
                                   bname,
                                   item['duration'])

        if key not in hash:
            hash[key] = {}

        hash[key][item['url']] = item

    # Loop over the hash and create Item objects which combine the
    # audio and video together
    for key, urlhash in hash.items():
        item = None
        for url, record in urlhash.items():
            if item is None:
                item = dict((field, record[field]) for field in ['name', 'duration', 'published', 'keywords'])
                
            if record['type'] == 'audio':
                item['audio_url'] = record['url']
            else:
                item['video_url'] = record['url'];

        if item: yield item


#
#
def extract(url):
    for item in records_to_items(rss_to_records(url)):
        yield item
    