import re

from ebooklib import epub
import bs4


class main:
    def __init__(self, scraper):
        self.image_count = 0
        self.scraper = scraper

    @staticmethod
    def url_transform(url):
        return (url if url[-1] != "/" else url[:-1]) + "?view_adult=true"

    @staticmethod
    def get_id(url, soup):
        return re.search(r'/works/(\d*?)/', url).group(1)

    @staticmethod
    def get_title(url, soup):
        return soup.find('h2', {'class': 'title heading'}).string.strip()

    @staticmethod
    def get_author(url, soup):
        return soup.find('a', {'rel': "author"}).string

    def get_cover(self, url, soup):
        return

    @staticmethod
    def get_summary(soup):
        return ''.join([str(p) for p in soup.find('div', {'class': 'summary module'}).blockquote.contents])

    @staticmethod
    def first_chapter_url(url, soup):
        return url

    @staticmethod
    def get_chapter_title(url, soup):
        return ''.join([i for i in soup.find('div', {'class': 'chapter preface group'}).h3.strings]).replace('\n',
                                                                                                             '').strip()

    @staticmethod
    def last_chapter(url, soup):
        return not bool(soup.find('li', {'class': 'chapter next'}))

    @staticmethod
    def next_chapter(url, soup):
        return 'https://archiveofourown.org' + soup.find('li', {'class': 'chapter next'}).a['href']

    def get_chapter_content(self, book, url, soup):
        content = ""

        # Get notes
        notes = soup.find('div', {'class': 'notes module'})  # Check if there are notes
        if notes is not None and notes.blockquote is not None:
            content += str(notes.blockquote) + "<hr>"  # Get notes

        paragraphs = []
        for p in soup.find('div', {'class': 'chapter'}).find('div', {'class': 'userstuff module'}).contents:
            if isinstance(p, bs4.element.Tag) and not ('class' in p.attrs and p['class'][0] == "landmark"):
                image = p.find('img')
                if image:
                    image = self.scraper.get(image['src'])

                    im = epub.EpubImage()
                    im.file_name = "images/" + str(self.image_count) + '.' + \
                                   image.headers['content-type'].split('/')[1]
                    im.media_type = image.headers['content-type']
                    im.content = image.content
                    book.add_item(im)

                    self.image_count += 1

                    paragraphs.append(str(p).replace(image.url, im.file_name))
                else:
                    paragraphs.append(str(p))

        content += ''.join(paragraphs).replace('href="/', 'href="https://www.archiveofourown.org/') \
            .replace("href='/", "href='https://www.archiveofourown.org/")
        return content
