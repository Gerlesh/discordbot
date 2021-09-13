import re
import sys

import bs4
import cloudscraper
from bs4 import BeautifulSoup
from ebooklib import epub

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'}

URL_MAP = {
    "https://archiveofourown.org/": 'ao3',
    "https://www.fanfiction.net/": 'ffn',
    "https://www.wattpad.com/": 'wp',
    "https://toonily.net/": 'toon'
}


class wp:
    def __init__(self, scraper):
        self.image_count = 0
        self.chapters = []
        self.scraper = scraper

    def url_transform(self, url):
        return url

    def get_id(self, url, soup):
        return re.search(r'story/(\d+)-', url).group(1)

    def get_title(self, url, soup):
        return soup.find('div', {'class': 'story-info__title'}).string

    def get_author(self, url, soup):
        return soup.find('div', {'class': "author-info__username"}).string

    def get_cover(self, url, soup):
        return self.scraper.get(soup.find('div', {'class': 'story-cover'}).img['src']).content

    def get_summary(self, soup):
        return "<p>" + soup.find('pre', {'class': 'description-text'}).text.replace("\n", "</p><p>") + "</p>"

    def first_chapter_url(self, url, soup):
        self.chapters = []
        for c in soup.find('div', {'class': 'story-parts'}).find_all('li'):
            self.chapters.append("https://www.wattpad.com" + c.a['href'])
        return self.chapters.pop(0)

    def get_chapter_title(self, url, soup):
        return soup.find('h1', {'class': 'h2'}).string.strip()

    def last_chapter(self, url, soup):
        return not self.chapters

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


class ffn:
    def __init__(self, scraper):
        self.chapter_count = 0
        self.chapters = []
        self.scraper = scraper

    def url_transform(self, url):
        return url

    def get_id(self, url, soup):
        return re.search(r'/s/(\d*?)/', url).group(1)

    def get_title(self, url, soup):
        return soup.find('div', {'id': "profile_top"}).find('b', {'class': "xcontrast_txt"}).string

    def get_author(self, url, soup):
        return soup.find('div', {'id': "profile_top"}).find('a', {'class': "xcontrast_txt"}).string

    def get_cover(self, url, soup):
        return self.scraper.get(
            "https://www.fanfiction.net" + soup.find('div', {'id': 'profile_top'}).find('img', {'class': 'cimage'})[
                'src']).content

    def get_summary(self, soup):
        return "<p>" + soup.find('div', {'class': 'xcontrast_txt', 'style': 'margin-top:2px'}).string + "</p>"

    def first_chapter_url(self, url, soup):
        if soup.find('select', {'id': 'chap_select'}):
            self.chapters = ["https://www.fanfiction.net/s/" + self.get_id(url, soup) + '/' + i['value'] for i in
                             soup.find('select', {'id': 'chap_select'}).find_all('option')]
        else:
            self.chapters = ["https://www.fanfiction.net/s/" + self.get_id(url, soup) + '/1']
        self.chapter_count = len(self.chapters)
        return self.chapters.pop(0)

    def get_chapter_title(self, url, soup):
        title = soup.find('option', {"selected": True}).contents[0]
        if title:
            return title
        else:
            return soup.find('div', {'id': "profile_top"}).find('b', {'class': "xcontrast_txt"}).string

    def last_chapter(self, url, soup):
        return not self.chapters

    def next_chapter(self, url, soup):
        return self.chapters.pop(0)

    def get_chapter_content(self, book, url, soup):
        return str(soup.find('div', {'class': 'storytext xcontrast_txt nocopy'})) \
            .replace('href="/', 'href="https://www.fanfiction.org/') \
            .replace("href='/", "href='https://www.fanfiction.net/")


class ao3:
    def __init__(self, scraper):
        self.image_count = 0
        self.scraper = scraper

    def url_transform(self, url):
        return (url if url[-1] != "/" else url[:-1]) + "?view_adult=true"

    def get_id(self, url, soup):
        return re.search(r'/works/(\d*?)/', url).group(1)

    def get_title(self, url, soup):
        return soup.find('h2', {'class': 'title heading'}).string.strip()

    def get_author(self, url, soup):
        return soup.find('a', {'rel': "author"}).string

    def get_cover(self, url, soup):
        return

    def get_summary(self, soup):
        return ''.join([str(p) for p in soup.find('div', {'class': 'summary module'}).blockquote.contents])

    def first_chapter_url(self, url, soup):
        return url

    def get_chapter_title(self, url, soup):
        return ''.join([i for i in soup.find('div', {'class': 'chapter preface group'}).h3.strings]).replace('\n',
                                                                                                             '').strip()

    def last_chapter(self, url, soup):
        return not soup.find('li', {'class': 'chapter next'})

    def next_chapter(self, url, soup):
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


class toon:
    def __init__(self, scraper):
        self.image_count = 0
        self.chapters = []
        self.scraper = scraper

    def url_transform(self, url):
        return url

    def get_id(self, url, soup):
        return re.search(r'/manga/(.*?)/$', url).group(1)

    def get_title(self, url, soup):
        return soup.find('div', {'class': 'post-title'}).h1.string

    def get_author(self, url, soup):
        return soup.find('div', {'class': 'author-content'}).string

    def get_cover(self, url, soup):
        return self.scraper.get(soup.find('div', {'class': 'summary_image'}).a.img['src']).content

    def get_summary(self, soup):
        return ''.join(soup.find('div', {'class': 'summary__content show-more'}).contents)

    def first_chapter_url(self, url, soup):
        self.chapters = [link['href'] for link in soup.find('ul', {'class': 'main version-chap'}).find_all('a')][::-1]
        return self.chapters.pop(0)

    def get_chapter_title(self, url, soup):
        return soup.find('h1', {'id': 'chapter-heading'}).string

    def last_chapter(self, url, soup):
        return not self.chapters

    def next_chapter(self, url, soup):
        return self.chapters.pop(0)

    def get_chapter_content(self, book, url, soup):
        content = '<div style="width:99%;text-align:center;display:block;font-size:0;line-height:0;">'
        images = [im['src'] for im in soup.find('div', {'class': 'reading-content'}).find_all('img')]

        for i, im in enumerate(images):
            pic = epub.EpubImage()
            pic.file_name = 'images\\' + str(self.image_count) + '.jpg'
            pic.media_type = 'image.jpeg'

            while pic.content == b'':
                try:
                    pic.content = self.scraper.get(im).content
                except self.scraper.ConnectionError:
                    pass

            content += '<img style="display:block;width:99%;max-width:770px;height:auto;margin:0 auto;" src="' + pic.file_name + '"/>'
            book.add_item(pic)
            self.image_count += 1

        content += '</div>'
        return content


def get_fic(url):
    scraper = cloudscraper.create_scraper()

    ####################################################################################################################
    # Get right module

    module = None
    site = None

    for domain in URL_MAP:
        if url.startswith(domain):
            module = getattr(sys.modules[__name__], URL_MAP[domain])(scraper)
            site = domain

    if module is None:
        raise ValueError("This website is not supported or there is an error in your url.")

    ####################################################################################################################
    # Get first chapter and parse html
    url = module.url_transform(url)
    r = scraper.get(url, headers=HEADERS)

    soup = BeautifulSoup(r.text, "html.parser")

    ####################################################################################################################
    # Initialize ebook and get basic info

    book = epub.EpubBook()

    story_id = module.get_id(url, soup)
    title = module.get_title(url, soup)
    author = module.get_author(url, soup)

    book.set_identifier(site + '_' + story_id)
    book.set_title(title)
    book.set_language('en')

    cover = module.get_cover(url, soup)
    if cover:
        book.set_cover("cover.jpg", cover)

    book.add_author(author)

    ####################################################################################################################
    # Get and add ebook summary

    summary = epub.EpubHtml(title="Summary", file_name='summary.xhtml')
    summary.content = "<h1><a href='" + url + "'>" + title + "</a></h1>"
    summary.content += "<h2>by " + author + "</h2>"
    summary.content += module.get_summary(soup)

    book.add_item(summary)

    chapters = [summary]

    chapter_links = [module.first_chapter_url(url, soup)]

    ####################################################################################################################
    # Get ebook chapters

    i = 1
    while chapter_links:
        ################################################################################################################
        # Get chapter data

        c = chapter_links.pop(0)
        # print("Retrieving " + c)
        r = scraper.get(module.url_transform(c), headers=HEADERS)
        s = BeautifulSoup(r.text, "html.parser")
        ################################################################################################################
        # Get chapter title

        chapter_title = module.get_chapter_title(c, s)

        ################################################################################################################
        # Add next chapter to list

        if not module.last_chapter(c, s):
            chapter_links.append(module.next_chapter(c, s))

        ################################################################################################################
        # Get chapter content

        content = "<h1><a href='" + c + "'>" + chapter_title + "</a></h1>" + module.get_chapter_content(book, c, s)

        # print(chapter_title)

        ################################################################################################################
        # Add chapter to ebook

        ch = epub.EpubHtml(title=chapter_title,
                           file_name=str(i) + '.xhtml')

        i += 1

        ch.content = content
        chapters.append(ch)
        book.add_item(ch)

    ####################################################################################################################
    # Add table of contents and navigation metadata

    book.toc = chapters[1:]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    spine = ['cover', chapters[0], 'nav'] + chapters[1:]
    book.spine = spine

    return book
