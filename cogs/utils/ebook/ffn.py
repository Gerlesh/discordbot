import re
import cloudscraper
from bs4 import BeautifulSoup
from ebooklib import epub

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'}


def get_fanfiction_fic(url):
    scraper = cloudscraper.create_scraper()
    r = scraper.get(url,
                    headers=HEADERS)

    soup = BeautifulSoup(r.content, "html.parser")

    book = epub.EpubBook()

    story_id = re.search(r'/s/(\d*?)/', url).group(1)
    title = soup.find('div', {'id': "profile_top"}).find('b', {'class': "xcontrast_txt"}).string
    author = soup.find('div', {'id': "profile_top"}).find('a', {'class': "xcontrast_txt"}).string

    book.set_identifier('ffn' + story_id)
    book.set_title(title)
    book.set_language('en')

    book.add_author(author)

    cover = scraper.get(
        "https://www.fanfiction.net" + soup.find('div', {'id': 'profile_top'}).find('img', {'class': 'cimage'})[
            'src']).content

    book.set_cover("cover.jpg", cover)

    summary = epub.EpubHtml(title="Summary", file_name='summary.xhtml')
    summary.content = "<h1>" + title + "</h1>"
    summary.content += "<h2>by " + author + "</h2>"
    summary.content += "<p>" + soup.find('div', {'class': 'xcontrast_txt', 'style': 'margin-top:2px'}).string + "</p>"

    book.add_item(summary)

    chapters = [summary]

    if soup.find('select', {'id': 'chap_select'}):
        chapter_links = ["https://www.fanfiction.net/s/" + story_id + '/' + i['value'] for i in
                         soup.find('select', {'id': 'chap_select'}).find_all('option')]
    else:
        chapter_links = ["https://www.fanfiction.net/s/" + story_id + '/1']

    for c in chapter_links:
        print("Retrieving " + c)
        r = scraper.get(c, headers=HEADERS)
        s = BeautifulSoup(r.content, "html.parser")

        content = str(s.find('div', {'class': 'storytext xcontrast_txt nocopy'})) \
            .replace('href="/', 'href="https://www.fanfiction.org/') \
            .replace("href='/", "href='https://www.fanfiction.net/")

        if len(chapter_links) > 1:
            chapter_title = s.find('option', {"selected": True}).contents[0]
        else:
            chapter_title = title

        ch = epub.EpubHtml(title=chapter_title,
                           file_name=re.search(r'/(\d+)$', c).group(1) + '.xhtml')
        ch.content = "<h1><a href='" + c + "'>" + chapter_title + "</a></h1>" + content

        chapters.append(ch)
        book.add_item(ch)

    book.toc = chapters[1:]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    spine = ['cover', chapters[0], 'nav'] + chapters[1:]
    book.spine = spine

    return book


class main:
    def __init__(self, scraper):
        self.chapter_count = 0
        self.chapters = []
        self.scraper = scraper

    @staticmethod
    def url_transform(url):
        return url

    @staticmethod
    def get_id(url, soup):
        return re.search(r'/s/(\d*?)/', url).group(1)

    @staticmethod
    def get_title(url, soup):
        return soup.find('div', {'id': "profile_top"}).find('b', {'class': "xcontrast_txt"}).string

    @staticmethod
    def get_author(url, soup):
        return soup.find('div', {'id': "profile_top"}).find('a', {'class': "xcontrast_txt"}).string

    def get_cover(self, url, soup):
        return self.scraper.get(
            "https://www.fanfiction.net" + soup.find('div', {'id': 'profile_top'}).find('img', {'class': 'cimage'})[
                'src']).content

    @staticmethod
    def get_summary(soup):
        return "<p>" + soup.find('div', {'class': 'xcontrast_txt', 'style': 'margin-top:2px'}).string + "</p>"

    def first_chapter_url(self, url, soup):
        if soup.find('select', {'id': 'chap_select'}):
            self.chapters = ["https://www.fanfiction.net/s/" + story_id + '/' + i['value'] for i in
                             soup.find('select', {'id': 'chap_select'}).find_all('option')]
        else:
            self.chapters = ["https://www.fanfiction.net/s/" + story_id + '/1']
        self.chapter_count = len(self.chapters)
        return self.chapters.pop(0)

    @staticmethod
    def get_chapter_title(url, soup):
        title = soup.find('option', {"selected": True}).contents[0]
        if title:
            return title
        else:
            return soup.find('div', {'id': "profile_top"}).find('b', {'class': "xcontrast_txt"}).string

    def last_chapter(self, url, soup):
        return not bool(self.chapters)

    def next_chapter(self, url, soup):
        return self.chapters.pop(0)

    @staticmethod
    def get_chapter_content(book, url, soup):
        return str(soup.find('div', {'class': 'storytext xcontrast_txt nocopy'})) \
            .replace('href="/', 'href="https://www.fanfiction.org/') \
            .replace("href='/", "href='https://www.fanfiction.net/")