#!/usr/bin/env python3

import argparse
import re
import sys
import os
import json
import requests
import bs4

class Downloader:
    def __init__(self, args):
        self.args = args
        self.session = requests.Session()
        self.titles = {}

    def read_persistent_data(self):
        json_file = os.path.join(self.args.dir, '.library.json')
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                d = json.load(f)
                # Merge contents of the dictionary into the .titles dict
                self.titles.clear()
                self.titles.update(d)

    def write_persistent_data(self):
        json_file = os.path.join(self.args.dir, '.library.json')
        with open(json_file, 'w') as f:
            json.dump(self.titles, f, indent='  ')

    def login(self):
        # Log in to the server
        if not self.args.dry_run:
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

    def read_purchased_library(self):
        # Read the complete library page
        html_file = os.path.join(self.args.dir, '.library.html')
        if not self.args.dry_run:
            if self.args.verbose:
                print('Retrieving complete library...')

            # This URL contains the user's library on a single page.
            r = self.session.get('http://bigfinish.com/customers/my_account/perpage:0')
            html = r.text
            # Save a copy of the HTML for --dry-run to use.
            open(html_file, 'w').write(html)
        else:
            html = open(html_file, 'r').read()

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

        # Look for the images for the download buttons.
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

        # Ensure all the titles have '*_filename' set to None if it's not
        # present.
        for d in self.titles.values():
            d.setdefault('audiobook_filename', None)
            d.setdefault('mp3_filename', None)

        return html_parser

    def determine_filenames(self):
        """Loop over contents of self.titles and figure out the filenames we
        want to download.
        """
        for k, d in sorted(self.titles.items()):
            url = None
            for format in (self.args.prefer_format, 'mp3', 'audiobook'):
                if format in d:
                    url = d[format]
                    filename_key = format + '_filename'
                    break

            assert url is not None, 'No URL found for {0}'.format(k)

            # Do we already know the filename?
            if d[filename_key]:
                continue

            # Not present, so do an HTTP HEAD to get the filename.
            if self.args.verbose:
                print('Determining filename for {!r}'.format(k))
            if self.args.dry_run:
                continue
            req = self.session.head(url)
            content_disp = req.headers['Content-disposition']
            m = re.search('filename=" ( [^"]* )"', content_disp, re.VERBOSE)
            assert m is not None, "Header {0} doesn't contain a filename".format(content_disp)
            filename = m.group(1)
            d[filename_key] = filename
            if self.args.verbose:
                print('  ... will download filename {!r}'.format(filename))

    def download_audio(self):
        "Download audio zip files"
        # This method shouldn't modify the .titles dictionary, because it
        # will have already been written out to disk at this point.
        for k, d in sorted(self.titles.items()):
            url = None
            for format in (self.args.prefer_format, 'mp3', 'audiobook'):
                if format in d:
                    url = d[format]
                    filename_key = format + '_filename'
                    filename = d[filename_key]
                    break

            assert url is not None, 'No URL found for {0}'.format(k)

            path = os.path.join(self.args.dir, filename)
            if os.path.exists(path):
                continue

            if self.args.verbose:
                print('Retrieving {} file for {!r}: {}'.format(format, k,
                                                               filename))
            if self.args.dry_run:
                continue

            # Download the archive
            # XXX it would be politer to save a partially-downloaded
            # file and then resume it.
            try:
                input = self.session.get(url, stream=True)
                # XXX could check that the length matches afterwards
                length = int(input.headers['Content-Length'])
                with open(path, 'wb') as output:
                    for chunk in input.iter_content(4096):
                        output.write(chunk)
            except Exception:
                print('Error: removing {}'.format(path))
                os.remove(path)
                raise
            except KeyboardInterrupt:
                print('Interrupted: removing {}'.format(path))
                os.remove(path)
                raise


def main():
    parser = argparse.ArgumentParser(
        description='Download Big Finish audios from an account')
    parser.add_argument('user', metavar='USERNAME',
                        help='bigfinish.com user account name')
    parser.add_argument('password', metavar='PASSWORD',
                        help='bigfinish.com user account password')
    parser.add_argument('dir', metavar='DIRECTORY', default='.',
                        help='directory to store audio files')
    parser.add_argument('--prefer-audiobook', action='store_const',
                        const='audiobook', dest='prefer_format',
                        default='mp3',
                        help='download audiobook format when available')
    parser.add_argument('--prefer-mp3', action='store_const',
                        const='mp3', dest='prefer_format',
                        default='mp3',
                        help='download mp3s when available')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        dest='dry_run', default=False,
                        help='produce more logging output')
    parser.add_argument('-v', '--verbose', action='store_true',
                        dest='verbose', default=False,
                        help='produce more logging output')
    args = parser.parse_args()

    dl = Downloader(args)
    dl.login()
    dl.read_persistent_data()
    dl.read_purchased_library()
    dl.determine_filenames()
    dl.write_persistent_data()
    dl.download_audio()
    return dl


if __name__ == '__main__':
    hp = main()
