YELP_COM_URL = 'http://www.yelp.com'
__author__ = 'S.R'
__date__ = 'Nov 24th, 2014'

from BeautifulSoup import BeautifulSoup
import urllib2
import argparse
import re
import time
import random
import sys

def extractText(tag, default=None, verbose=False, attrs={}):
    try:
        if False in [True if(re.compile(attrs[time_key]).match(tag[time_key])) else False for time_key in attrs.keys()]:
            return default
        else:
            return tag.getText()
    except Exception, e:
        if verbose: print 'Extracting ' + attrs + 'failed.', str(e)
    return default

def extractTagAttribute(tag, default=None, verbose=False, property='content', attrs={}):
    try:
        if False in [True if(re.compile(attrs[time_key]).match(tag[time_key])) else False for time_key in attrs.keys()]:
            return default
        else:
            return tag[property]
    except Exception, e:
        if verbose: print 'Extracting ' + attrs + 'failed.', str(e)
    return default

def crawl_page(url, verbose=False):
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    for tag in soup.findAll('div', {'class':'biz-main-info embossed-text-white'}):
        for subtag in tag.findAll('meta', {'itemprop':'ratingValue'}):
            return float(extractTagAttribute(subtag, -1, verbose))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts details of yelp restaurant')
    parser.add_argument('-f', '--file', type=str, help='Enter file')
    args = parser.parse_args()
    er = open("error.txt", mode='w')
    with open(args.file, mode='r') as f:
        for line in f:
            try:
                if line.startswith("B="):
                    B=R=NR=[] #TMP HOLDER
                    exec(line)
                elif line.startswith("R="):
                    exec(line) #New R
                elif line.startswith("NR="):
                    exec(line) #New NR, End of one set
                    B[2] = crawl_page(B[4])
                    print 'B=', B
                    print 'R=', R
                    print 'NR=', NR
                else:
                    print line
            except Exception, e:
                print >>sys.stderr, e
                print >>er, 'B=', B
                print >>er, 'R=', R
                print >>er, 'NR=', NR
                time.sleep(random.randint(1, 4) * .931467298)