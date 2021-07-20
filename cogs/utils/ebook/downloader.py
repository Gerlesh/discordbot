import cloudscraper
from bs4 import BeautifulSoup
from ebooklib import epub

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'}

URL_MAP = {
    "https://archiveofourown.org/": 'ao3',
    "https://www.fanfiction.net/": 'ffn',
    "https://www.wattpad.com/": 'wp'
}


def get_fic(url):
    scraper = cloudscraper.create_scraper()

    ####################################################################################################################
    # Get right module

    module = None
    site = None

    for domain in URL_MAP:
        if url.startswith(domain):
            module = __import__(URL_MAP[domain]).main(scraper)
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
        print("Retrieving " + c)
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

        print(chapter_title)

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

