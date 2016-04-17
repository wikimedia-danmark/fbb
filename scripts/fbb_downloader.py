"""
FBB downloader.

Usage:
  fbb_downloader.py <useragent> [options]

Options:
  --from=<from>  email

"""

import codecs

from lxml import etree

from os import listdir
from os.path import isfile, join, split

import requests

from time import sleep


dirname, filename = split(__file__)
DATA_DIRECTORY = join('..', 'data')


class Api(object):
    """Interface to FBB website and stored files."""

    def __init__(self, useragent, from_=None):
        """Setup parameters.

        Arguments
        ---------
        useragent : str
            User-selected string for User-Agent in request header
        from_ : str
            User-selected string for from field in request header

        """
        self.user_agent = useragent
        self.from_ = from_
        self.main_page_filename = join(DATA_DIRECTORY, 'mainpage.html')
        self.main_url = 'https://www.kulturarv.dk/fbb/fredningsliste.htm'
        self.pause = 5

    @property
    def headers(self):
        """Return HTTP request header."""
        headers = {'User-Agent': self.user_agent,
                   'From': self.from_}
        return headers

    def download_main_page(self):
        """Download and save mainpage from website."""
        response = requests.get(self.main_url, headers=self.headers)
        with codecs.open(self.main_page_filename, 'w', encoding='utf-8') as f:
            f.write(response.text)

    def extract_municipalities(self):
        """Extract the municipality identifiers."""
        with codecs.open(self.main_page_filename, encoding='utf-8') as f:
            tree = etree.HTML(f.read())
        div = tree.xpath("//*[contains(@class, 'publicFredningslisteText')]")
        ids = [option.get('value') for option in div[0].xpath('//option')
               if option.get('value') != '-1']
        return ids

    def download_municipality(self, id):
        """Download municipality webpages.

        Arguments
        ---------
        id : str
            Municipality identifier.

        """
        if str(id) != str(int(str(id))):
            raise Exception('Something is wrong with the id: {}'.format(id))
        response = requests.post(self.main_url, headers=self.headers,
                                 params={'kommune': id})

        filename = join(DATA_DIRECTORY, str(id) + '.html')
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)

    def download_municipalities(self, ids):
        """Download municipality information from website.

        Files will be writte in the data directory.

        """
        for id in ids:
            self.download_municipality(id)
            sleep(self.pause)

    def extract_case_numbers_from_file(self, filename):
        """Extract case numbers from a single file.

        Arguments
        ---------
        filename : str
            Full filename

        Returns
        -------
        case_cumbers : list of str
            Case numbers as list of strings.

        """
        with codecs.open(filename, encoding='utf-8') as f:
            tree = etree.HTML(f.read())
        a_tags = tree.xpath(
            "//div[contains(@class, 'list_results clearfix')]/a")
        case_numbers = [a_tag.get('href')[15:] for a_tag in a_tags]
        return case_numbers

    def extract_case_numbers(self):
        """Extraect all case numbers from downloaded files.

        Returns
        -------
        case_numbers : list of str
            Case numbers as list of strings.

        """
        filenames = listdir(DATA_DIRECTORY)
        case_numbers = []
        for filename in filenames:
            if filename.startswith('26919'):
                full_filename = join(DATA_DIRECTORY, filename)
                case_numbers.extend(
                    self.extract_case_numbers_from_file(full_filename))
        return case_numbers


def main(arguments):
    """Handle command-line input.

    Arguments
    ---------
    arguments : dict
        Dictionary in docopt format.

    """
    api = Api(useragent=arguments['<useragent>'], from_=arguments['--from'])

    if not isfile(api.main_page_filename):
        api.download_main_page()

    # TODO: check if already downloaded
    # ids = api.extract_municipalities()
    # api.download_municipalities(ids)

    case_numbers = api.extract_case_numbers()
    print("\n".join(case_numbers))


if __name__ == '__main__':
    from docopt import docopt

    main(docopt(__doc__))
