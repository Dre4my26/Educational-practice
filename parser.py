# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import re


def get_all_pages(default_page='https://habr.com/ru/hub/machine_learning/top/alltime/page'):
    """
    Simple function to get the list of all the links to the pages. \n
    P.S. Since all the pages are on the same topic, and the only thing changing is the number in the end, the function
    simply increases the *URL*/pageXX/ by 1 with every iteration.
    :return: list of pages to parse
    """
    pages = []

    for page_num in range(1, 51):
        next_page = default_page + str(page_num)
        pages.append(next_page)
    print("Функция get_all_pages() отработала")
    print(pages)

    return pages


def extract_comments_links(url):
    """
    Extracts links to comments page with the given URL
    :param url: takes URL [e.g. 'https://habr.com/ru/hub/machine_learning/top/alltime/page1/'] where from to extract
    links to webpages with comments [https://habr.com/ru/post/570694/comments/,
    https://habr.com/ru/post/480348/comments/, ...]
    :return: list of links to comments pages
    """
    page = requests.get(url)
    print(f'Status code is: {page.status_code}')

    soup = BeautifulSoup(page.text, "html.parser")
    allComments = soup.findAll('a', class_='tm-article-comments-counter-link__link')
    halfLinksToComments = []
    for comment in allComments:
        halfLinksToComments.append(comment.attrs['href'])

    habrURL = 'https://habr.com'
    linksToComments = []

    for link in halfLinksToComments:
        commentLink = habrURL + link
        linksToComments.append(commentLink)
    print("Функция extract_comments_links() отработала")
    print(linksToComments)

    return linksToComments


def comments_extractor(urlToCommentsWebpage, article_id):
    """
    Extracts *article title* and *comments* from the given webpage [e.g. https://habr.com/ru/post/570694/comments/]
    :param urlToCommentsWebpage: URL where from to extract comments
    :param article_id: internal id of an article (saves the article_id to csv)
    :return: comments_texts[] as a list of comments
    """
    commentsPage = requests.get(urlToCommentsWebpage)
    soup = BeautifulSoup(commentsPage.text, "html.parser")
    title = soup.find('h1', class_='tm-article-snippet__title tm-article-snippet__title_h1')
    theme = soup.find('div', class_='tm-article-snippet__hubs').text.strip()
    theme = theme.replace('*', '')
    num_of_comments = soup.find('span', class_="tm-comments-wrapper__comments-count").text.strip()
    title = title.text
    for div in soup.find_all("div", {'class': 'tm-comment__body-content tm-comment__body-content_empty'}):
        div.decompose()
    allComments = soup.findAll('div', class_='tm-comment__body-content')
    allUsernames = soup.findAll('a', class_='tm-user-info__username')
    comments_texts = []
    all_usernames = []
    dates = []
    article_url = re.search('(.*)comments', urlToCommentsWebpage).group(1)
    # Добавление счетчика подкомментариев для каждой ветки
    threads_block = soup.find('div', class_="tm-comments__tree")
    children = 0
    k = 0
    n = 1
    comments_under_comment_threads = []
    comments_under_comment = []
    for thread in threads_block:
        children = thread.findAll('article', class_='tm-comment-thread__comment')
        k += len(children)
        comments_under_comment_threads.append(k)
        k = 0
        n += 1
    for i in comments_under_comment_threads:
        for j in range(i):
            comments_under_comment.append(i - 1)

    all_dates = soup.findAll('a', class_='tm-comment-thread__comment-link')
    for date in all_dates:
        dates.append(date.text.strip().split(' ')[0])
    for comment in allComments:
        comment = comment.text.replace("\n", "").replace("\r", " ")
        comment = comment.replace("\n", "")
        comments_texts.append(comment)
    for username in allUsernames:
        username = username.text.strip()
        all_usernames.append(username)
    del all_usernames[0]
    print(title)  # str с названием статьи
    print(article_url)  # str с ссылкой на статью
    with open('articles.csv', 'a', encoding='utf-8') as comments_csv:
        for comment_text, username, comments_under_comment_counter, date in zip(comments_texts, all_usernames,
                                                                                comments_under_comment, dates):
            if title == ' ' or article_url == ' ':
                comments_csv.write(comment_text)
            else:
                comments_csv.write('\n' + str(article_id) + '\t;' + title + '\t;' + article_url + '\t;' +
                                   num_of_comments + '\t;' + comment_text + '\t;' + username + '\t;' +
                                   theme + '\t;' + str(comments_under_comment_counter) + '\t;' + date)

    return title, comments_texts


def main():
    article_id = 1
    for url in get_all_pages():
        for extracted_link in extract_comments_links(url):
            # TODO: заменить костыльный метод проверки на какой-нибудь адекватный
            page = requests.get(extracted_link)
            soup = BeautifulSoup(page.text, 'html.parser')
            num_comments = soup.find('span', class_='tm-article-comments-counter-link__value').text.strip()
            if int(num_comments) != 0:
                comments_extractor(extracted_link, article_id)
                print(f"Количество комментариев: {num_comments}")
                article_id += 1
            else:
                print('В данной статье нет комментариев!')


if __name__ == "__main__":
    main()
