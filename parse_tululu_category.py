import argparse
import json
import requests
import os
from bs4 import BeautifulSoup
from pathlib import Path
from pathvalidate import sanitize_filename
from urllib.parse import urljoin

def create_parser():
    parser = argparse.ArgumentParser(description='Парсер книг с сайта tululu.org')
    parser.add_argument('--start_page', help='Начальная страница', type=int)
    parser.add_argument('--end_page', help='Конечная страница', type=int, default=702)
    return parser

def download_txt(url, filename, folder='books'):
    response = requests.get(url, allow_redirects = False)
    response.raise_for_status()
    filepath = os.path.join(folder, sanitize_filename(filename + '.txt'))
    with open(filepath, 'w', encoding='utf8') as file:
        file.write(response.text)
    return filepath

def download_image(url, filename, folder='images'):
    response = requests.get(url, allow_redirects = False)
    response.raise_for_status()
    filepath = os.path.join(folder, filename)
    with open(filepath, 'wb') as file:
        file.write(response.content)
    return filepath

def find_book_title(soup):
    book_title_text = soup.select_one('h1').text
    book_information = book_title_text.split('::')
    book_title = book_information[0].strip()
    return book_title

def find_book_author(soup):
    book_title_text = soup.select_one('h1').text
    book_information = book_title_text.split('::')
    book_author = book_information[1].strip()
    return book_author

def find_book_comments(soup):
    return [comment.text for comment in soup.select('.texts span')]

def find_book_genres(soup):
    return [genre.text for genre in soup.select('span.d_book a')]    

def get_books_description(books_from_page):
    for book in books_from_page:
        book_page_href = book.select_one('a')['href']
        book_page_url = urljoin('http://tululu.org/index.html', book_page_href.strip('/') + '/')

        response = requests.get(book_page_url, allow_redirects = False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        book_title = find_book_title(soup)
        book_author = find_book_author(soup)
        comments = find_book_comments(soup)
        genres = find_book_genres(soup)

        book_id = book_page_href.strip('/b')
        book_download_url = book_download_url_template.format(book_id)
        book_path = download_txt(book_download_url, book_title)

        if book_path is None:
            continue

        book_image_src = book.select_one('img')['src']
        book_image_title = book_image_src.split('/')[2]
        book_image_url = urljoin('http://tululu.org/index.html', book_image_src.strip('/'))
        img_src = download_image(book_image_url, book_image_title)

        book_description = {
            'title': book_title,
            'author': book_author,
            'img_src': img_src,
            'book_path': book_path,
            'comments': comments,
            'genres': genres
        }
        books_description.append(book_description)

        print(book_page_url)

    return books_description

if __name__ == '__main__':
    page_url_template = 'http://tululu.org/l55/more'
    book_download_url_template = 'http://tululu.org/txt.php?id={}'
    parser = create_parser()
    args = parser.parse_args()
    
    if args.start_page:
        Path('books').mkdir(parents=True, exist_ok=True)
        Path('images').mkdir(parents=True, exist_ok=True)

        books_description = []
        for page in range(args.start_page, args.end_page):
            page_url = urljoin(page_url_template, str(page))
            response = requests.get(page_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            books_from_page = soup.select('.bookimage')
            books_description = get_books_description(books_from_page)

        with open('books_description.json', 'w', encoding='utf8') as my_file:
            json.dump(books_description, my_file, ensure_ascii = False, indent=4)

    if not args.start_page:
    	print('Введите начальную страницу')