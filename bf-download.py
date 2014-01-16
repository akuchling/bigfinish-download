#!/usr/bin/env python

import argparse
import re
import sys
import requests
import bs4

class Downloader:
    def __init__(self, args):
        self.args = args
        self.session = requests.Session()
        self.titles = {}

    def login(self):
        # Log in to the server
        if True:
            if self.args.verbose:
                sys.stderr.write('Logging into server...\n')

            # Access top page in order to get the cookies.
            r = self.session.get('http://bigfinish.com')

            r = self.session.post('http://bigfinish.com/customers/login',
                              data={'_method' :'POST',
                                    'data[post_action]': 'login',
                                    'data[Customer][email_address]': self.args.user,
                                    'data[Customer][password]': self.args.password,
                                    'data[remember_me]': '1'},
                          )

    def read_library(self):
        # Read the complete library page
        if self.args.verbose:
            print('Retrieving complete library...')
        if True:
            r = self.session.get('http://bigfinish.com/customers/my_account/perpage:0')
            html = r.text
            open('bf-download-new.html', 'w').write(html)
        else:
            html = open('bf-download-new.html', 'rb').read()

        # Parse the HTML.
        if self.args.verbose:
            sys.stderr.write('Parsing library...\n')

        html_parser = bs4.BeautifulSoup(html)

        def extract_info(img):
            # Link to download the file
            href = img.parent['href']
            if not href.startswith('http'):
                href = 'http://bigfinish.com' + href

            # Title for this file
            product_entry = img.parent.parent.parent
            title = product_entry.select('a.largePopOut > img')[0]['alt']
            return (title, href)

        mp3_images = html_parser.find_all('img', attrs={
            'src': re.compile('button-account-downloadmp3.png$')})
        audiobook_images = html_parser.find_all('img', attrs={
            'src': re.compile('button-account-downloadaudiobook.png$')})

        for img in mp3_images:
            title, href = extract_info(img)
            d = self.titles.setdefault(title, {})
            d['mp3'] = href

        for img in audiobook_images:
            title, href = extract_info(img)
            d = self.titles.setdefault(title, {})
            d['audiobook'] = href

        if self.args.verbose:
            sys.stderr.write('%i titles in library\n' % len(self.titles))

        # Check for actual file name of titles
        return html_parser

    def download_audio(self):
        pass

def main():
    parser = argparse.ArgumentParser(
        description='Download Big Finish audios from an account')
    parser.add_argument('user', metavar='USERNAME',
                        help='bigfinish.com user account name')
    parser.add_argument('password', metavar='PASSWORD',
                        help='bigfinish.com user account password')
    parser.add_argument('dir', metavar='DIRECTORY',
                        help='directory to store audio files')
    parser.add_argument('--prefer-audiobook', action='store_const',
                        const='audiobook', dest='prefer_format',
                        help='download audiobook format when available')
    parser.add_argument('--prefer-mp3', action='store_const',
                        const='mp3', dest='prefer_format',
                        default='mp3',
                        help='download mp3s when available')
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose',
                        help='produce more logging output')
    args = parser.parse_args()

    dl = Downloader(args)
    dl.login()
    dl.read_library()
    dl.download_audio()

if __name__ == '__main__':
    hp = main()
