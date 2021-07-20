import re
import time

from bs4 import BeautifulSoup
from ebooklib import epub

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'}


class main:
    def __init__(self, scraper):
        self.image_count = 0
        self.chapters = []
        self.scraper = scraper

    @staticmethod
    def url_transform(url):
        return url

    @staticmethod
    def get_id(url, soup):
        return re.search(r'story/(\d+)-', url).group(1)

    @staticmethod
    def get_title(url, soup):
        return soup.find('div', {'class': 'story-info__title'}).string

    @staticmethod
    def get_author(url, soup):
        return soup.find('div', {'class': "author-info__username"}).string

    def get_cover(self, url, soup):
        return self.scraper.get(soup.find('div', {'class': 'story-cover'}).img['src']).content

    @staticmethod
    def get_summary(soup):
        return "<p>" + soup.find('pre', {'class': 'description-text'}).text.replace("\n", "</p><p>") + "</p>"

    def first_chapter_url(self, url, soup):
        self.chapters = []
        for c in soup.find('div', {'class': 'story-parts'}).find_all('li'):
            self.chapters.append("https://www.wattpad.com" + c.a['href'])
        return self.chapters.pop(0)

    @staticmethod
    def get_chapter_title(url, soup):
        return soup.find('h1', {'class': 'h2'}).string.strip()

    def last_chapter(self, url, soup):
        return not bool(self.chapters)

    def next_chapter(self, url, soup):
        return self.chapters.pop(0)

    def get_chapter_content(self, book, url, soup):
        content = ""

        while soup.find(text='Load More Pages...'):
            paragraphs = soup.find_all(attrs={'data-p-id': True})

            for p in paragraphs:
                if 'data-media-type' in p.attrs:
                    image = self.scraper.get(p.img['src'])

                    im = epub.EpubImage()
                    im.file_name = "images/" + str(self.image_count) + '.' + \
                                   image.headers['content-type'].split('/')[1]
                    im.media_type = image.headers['content-type']
                    im.content = image.content
                    book.add_item(im)

                    self.image_count += 1

                    content += str(p).replace(p.img['src'], im.file_name)
                else:
                    content += str(p)

            soup = BeautifulSoup(self.scraper.get(soup.find("a", {"aria-label": "Load More Pages"})['href'],
                                                  headers=HEADERS).text, 'html.parser')

        paragraphs = soup.find_all(attrs={'data-p-id': True})

        for p in paragraphs:
            if 'data-media-type' in p.attrs:
                image = self.scraper.get(p.img['src'])

                im = epub.EpubImage()
                im.file_name = "images/" + str(self.image_count) + '.' + \
                               image.headers['content-type'].split('/')[1]
                im.media_type = image.headers['content-type']
                im.content = image.content
                book.add_item(im)

                self.image_count += 1

                content += str(p).replace(p.img['src'], im.file_name)
            else:
                content += str(p)

        content.replace('href="/', 'href="https://www.wattpad.com/') \
            .replace("href='/", "href='https://www.wattpad.com/")
        return content
