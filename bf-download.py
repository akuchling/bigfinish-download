#!/usr/bin/env python3 -i

import argparse
import re
import sys
import requests
import bs4

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

    # Log in to the server
    if False:
        if args.verbose:
            print('Logging into server...', file=sys.stderr)

        # Access top page in order to get the cookies.
        r = requests.get('http://www.bigfinish.com')
        cookie_jar = r.cookies

        r = requests.post('http://www.bigfinish.com/customers/login',
                          cookies=cookie_jar,
                          data={'_method' :'POST',
                                'data[Customer][email_address]': args.user,
                                'data[Customer][password]': args.password,
                                'data[remember_me]': '1'},
                      )

    # Read the complete library page
    if args.verbose:
        print('Retrieving complete library...')
    if False:
        r = requests.get('http://bigfinish.com/customers/my_account/perpage:0',
                          cookies=cookie_jar)
        html = r.content
    else:
        html = open('bf-download.html', 'rb').read()

    # Parse the HTML.
    if args.verbose:
        print('Parsing library...', file=sys.stderr)

    html_parser = bs4.BeautifulSoup(html)

    def extract_info(img):
        # Link to download the file
        href = img.parent['href']

        # Title for this file
        product_entry = img.parent.parent.parent
        title = product_entry.find('a', attrs={'class':'largePopOut'}).text

        return (title, href)

    mp3_images = hp.find_all('img', attrs={
        'src': re.compile('button-account-downloadmp3.png$')})
    audiobook_images = hp.find_all('img', attrs={
        'src': re.compile('button-account-downloadaudiobook.png$')})

    mp3_hrefs = [extract_info(img) for img in mp3_images]
    audiobook_hrefs = [extract_info(img) for img in audiobook_images]

    all_titles = set(title for (title, href) in mp3_hrefs + audiobook_hrefs)

    if verbose:
        print(len(all_titles), 'in library', file=sys.stderr)

    # Check for actual file name of titles


    return html_parser

if __name__ == '__main__':
    hp = main()
