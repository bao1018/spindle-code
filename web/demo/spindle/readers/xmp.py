"""Scrape word information out of XML transcript files generated by
 Adobe Premiere in .XMP format.
"""

import re
from xml.etree.cElementTree import iterparse
from words import Word, words_to_clips

# Qualified names of tags we care about
RDF_LI = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li'
XMPDM_MARKERS = '{http://ns.adobe.com/xmp/1.0/DynamicMedia/}markers'
XMPDM_FRAMERATE = '{http://ns.adobe.com/xmp/1.0/DynamicMedia/}frameRate'
XMPDM_STARTTIME = '{http://ns.adobe.com/xmp/1.0/DynamicMedia/}startTime'
XMPDM_DURATION = '{http://ns.adobe.com/xmp/1.0/DynamicMedia/}duration'
XMPDM_NAME = '{http://ns.adobe.com/xmp/1.0/DynamicMedia/}name'

def words(infile):
    inMarkers = False
    frame_rate = None

    def frames_to_seconds(frames):
        return float(frames) / frame_rate

    for event, elem in iterparse(infile, ('start','end')):
        if event == 'start' and elem.tag == XMPDM_MARKERS:
            inMarkers = True
            if not frame_rate:
                raise Exception("No frame rate specifier found before beginning of markers.")
        elif event == 'end' and elem.tag == XMPDM_MARKERS:
            inMarkers = False
        elif event == 'end' and elem.tag == XMPDM_FRAMERATE:
            frame_rate = parse_frame_rate(elem.text)
        elif inMarkers and event == 'end' and elem.tag == RDF_LI:
            yield Word(token = elem.find(XMPDM_NAME).text,
                       intime = frames_to_seconds(elem.find(XMPDM_STARTTIME).text),
                       duration = frames_to_seconds(elem.find(XMPDM_DURATION).text))

# See
# http://www.adobe.com/content/dam/Adobe/en/devnet/xmp/pdfs/XMPSpecificationPart2.pdf
# , section 1.2.6.4: FrameRate
def parse_frame_rate(text):
    m = re.match('f(\d+)$', text)
    if m:
        return int(m.group(1))
    
    m = re.match('f(\d+)s(\d+)$', text)
    if m:
        return float(m.group(1)) / float(m.group(2))

    raise Exception("Bad FrameRate specifier:", text)

def read(infile, **kwargs):
    return words_to_clips(words(infile), **kwargs)