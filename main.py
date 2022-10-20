import requests
from bs4 import BeautifulSoup
import re


URL = 'https://habr.com'
KEYWORDS = ['дизайн', 'фото', 'web', 'python']

cookies_ = {
    '_ym_d': '1660160813',
    '_ym_uid': '1660160813305233842',
    'hl': 'ru',
    'fl': 'ru',
    '_ga': 'GA1.2.1537204775.1660160813',
    '_gid': 'GA1.2.977757873.1665820994',
    'visited_articles': '248559:330034:438162:196382:349860:265007:562322:692714:439288:328372',
    '_ym_isad': '1',
    'habr_web_home_feed': '/all/',
}

headers_ = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ru,en;q=0.9,de;q=0.8,la;q=0.7,tr;q=0.6',
    'Connection': 'keep-alive',
    'DNT': '1',
    'If-None-Match': 'W/"4-K+iMpCQsduglOsYkdIUQZQMtaDM"',
    'Referer': 'https://habr.com/ru/all/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/104.0.5112.124 YaBrowser/22.9.3.886 Yowser/2.5 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Yandex";v="22"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'x-app-version': '2.93.0',
}


def get_articles_from_soup_obj(soup, root_url=None):
    articles = soup.find_all('article')

    article_list = []
    for article in articles:
        article_id = article.attrs['id']
        title_base = article.find(class_='tm-article-snippet__title-link')
        title = title_base.find('span').text
        if root_url is not None:
            href = root_url + title_base.attrs['href']
        else:
            href = title_base.attrs['href']
        hubs = ','.join([hub.find('span').text
                         for hub in article.find_all(class_='tm-article-snippet__hubs-item-link')])

        preview_text = article.find(
            class_='article-formatted-body article-formatted-body article-formatted-body_version-1')
        if preview_text is None:
            preview_text = article.find(
                class_='article-formatted-body article-formatted-body article-formatted-body_version-2')

        date = re.match(r"\d{4}-\d{1,2}-\d{1,2}", article.find('time').attrs['datetime']).group(0)

        article_obj = dict(id=article_id, title=title, href=href, hubs=hubs,
                           preview_text=preview_text.text.strip(), date=date)
        article_list.append(article_obj)
    return article_list


def get_full_text_from_article_soup(soup):
    full_article_text = soup.find(
        class_='article-formatted-body article-formatted-body article-formatted-body_version-1')
    if full_article_text is None:
        full_article_text = soup.find(
            class_='article-formatted-body article-formatted-body article-formatted-body_version-2')
    res = full_article_text.text.strip()
    return res


def filter_articles_by_keywords(articles, keywords, is_in_text=False):
    filtered_articles = []
    for article in articles:
        full_content_string = article.get('title') + article.get('hubs') + article.get('preview_text')
        search_pattern = r'|'.join(keywords)
        search_res = re.search(search_pattern, full_content_string)
        if search_res is not None:
            filtered_articles.append(article)
        elif is_in_text:
            full_article_text = article.get('full_text')
            search_res = re.search(search_pattern, full_article_text)
            if search_res is not None:
                filtered_articles.append(article)
    return filtered_articles


def main(url, keywords, full_text_required=False, cookies=None, headers=None):
    response = requests.get(url, cookies=cookies, headers=headers)
    text = response.text

    soup = BeautifulSoup(text, features='html.parser')
    articles = get_articles_from_soup_obj(soup, root_url=url)

    if full_text_required:
        for article in articles:
            response = requests.get(article.get('href'), cookies=cookies, headers=headers)
            text = response.text
            soup = BeautifulSoup(text, features='html.parser')
            full_article_text = get_full_text_from_article_soup(soup)
            article['full_text'] = full_article_text

    filtered_articles = filter_articles_by_keywords(articles, keywords, is_in_text=full_text_required)

    for article in filtered_articles:
        print(f"{article.get('date')} - {article.get('title')} - {article.get('href')}")


if __name__ == '__main__':
    main(URL, KEYWORDS, cookies=cookies_, headers=headers_, full_text_required=True)
