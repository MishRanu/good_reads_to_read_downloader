import requests
from xml.dom.minidom import parseString
from htmldom import htmldom
import libgenapi
import time
import re
from bs4 import BeautifulSoup
from os.path import splitext
from lib.misc.book import Book

class Libgen(object):

    def __init__(self, isbn_list, mirrors = ["http://gen.lib.rus.ec/", "http://libgen.io/", "http://libgen.net/", "http://bookfi.org/"]):
        self.mirrors = mirrors
        self.lg = libgenapi.Libgenapi(mirrors)
        self.isbn_list = isbn_list


    def find_single(self, book):
        '''
            Tries to find a single book in the database based on it's ISBN or ISBN13.
        '''
        download_urls = []
        if not hasattr(book, 'title'):
            return download_urls
        # Trying to download via ISBN or via ISBN13
        if hasattr(book, 'identifier') and len(book.identifier)!=0:
            for identifier in book.identifier:
                if identifier.get('type') == 'isbn':
                    download_urls = self.inner_find(identifier.get('value'))
                elif identifier.get('type') == 'isbn3':
                    download_urls = self.inner_find(identifier.get('value'))

        # if 'isbn' in book.identifier:
        #     download_url = self.inner_find(book.identifier.get('isbn'))
        # if 'isbn13' in book.identifier:
        #     download_url = self.inner_find(book.identifier.get('isbn13'))

        if download_urls is not None and len(download_urls) !=0:
                print("[FOUND] Book {} found.".format(book.title))
        else:
                print("[ERROR] Book {} not found.".format(book.title))

        return download_urls

    def find(self):
        total = len(self.isbn_list)
        download_urls_list = [] # Success

        for book in self.isbn_list:
            time.sleep(5)
            download_urls = self.find_single(book)
            if download_urls is not None and len(download_urls) != 0:
                download_urls_list.append(download_urls)

        print("=== Summary ===")
        print("Success: {}".format(str(len(download_urls_list))))
        print("Total: {}".format(str(total)))
        return download_urls_list

    def download_single(self, book, find=True):
        download_urls = self.find_single(book)
        download_urls = download_urls if find and download_urls is not None else []
        if download_urls is not None and len(download_urls) != 0:
            for download_url in download_urls:
                if download_url:
                    if hasattr(book, 'title'):
                        filename = "downloads/" + re.sub(r'(\W+)', "", book.title) + download_url.get('extension')
                    else:
                        filename = "downloads/" + re.sub(r'(\W+)', "", str(time.time())) + download_url.get('extension')
                    if self.inner_download(url=download_url.get('url'), filename=(filename)) == True:
                        return

    def download(self):
        for book in self.isbn_list:
            self.download_single(book, find=True)
        # download_urls_list = self.find()
        # for download_urls in download_urls_list:
        #     time.sleep(5)
        #     self.download_single(download_urls, find=True)

    # Private methods
    def inner_find(self, isbn):
        results = self.lg.search(isbn, "identifier")
        downloadable_mirror_urls=[]

        extension_check_results = [result for result in results if result.get('extension') in ['epub', 'pdf', 'mobi', 'chm', 'djvu', 'doc']]
        language_check_results = [result for result in results if result.get('language')=='English']
        primary_check_results = []
        for result in extension_check_results:
            primary_check_results.append(result)
        for result in language_check_results:
            primary_check_results.append(result)
        for result in results:
            primary_check_results.append(result)

        for result in primary_check_results:
            if result.get('mirrors') is not None:
                for mirror in result.get('mirrors'):
                    downloadable_mirror_urls.append(mirror)

        download_links = []
        for downloadable_mirror_url in downloadable_mirror_urls:
            mirror_request = requests.get(downloadable_mirror_url, verify=False)
            soup = BeautifulSoup(mirror_request.content, 'lxml')
            regex_download = re.compile("/download|Download|download now|Download Now|DOWNLOAD NOW|DOWNLOAD|Get|get|GET|Get now|GET NOW/i")
            soup_links = soup.find_all('a', string=regex_download)
            for download_link in soup_links:
                # download_link = soup_link.find(self.has_download_text)
                if download_link is not None:
                    parsed = requests.utils.urlparse(download_link.get('href'))
                    root, ext = splitext(parsed.path)
                    if ext in ['.epub','.pdf', '.mobi','.chm','.djvu', '.doc']:
                        download_links.append({'url': download_link.get('href'), 'extension': ext})

        if len(download_links) != 0:
            return download_links
        else:
            return None

    def inner_download(self, url, filename):
        with open(filename, "wb") as handle:
            response = requests.get(url, stream=True, verify=False)
            if not response.ok:
                return False

            print("Downloading book to {}".format(filename))

            for block in response.iter_content(chunk_size=128):
                handle.write(block)
        return True
