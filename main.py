#!/usr/bin/python
# -*- coding: UTF-8 -*-
from bs4 import BeautifulSoup
from alive_progress import alive_bar
import requests
import os
import re
import time
import json
import sys


def Anime_Season(url):
    titles, urls = [], []
    # https://anime1.me/category/.../...
    r = requests.post(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    h2 = soup.find_all('h2', class_="entry-title")
    for idx, i in enumerate(h2):
        video_link = i.find("a", attrs={"rel": "bookmark"})
        urls.append(video_link.get('href'))
        title = video_link.text
        titles.append(title)

    # NextPage
    if(soup.find('div', class_='nav-previous')):
        ele_div = soup.find('div', class_='nav-previous')
        NextUrl = ele_div.find('a').get('href')
        nexturls, nexttitles = Anime_Season(NextUrl)
        urls.extend(nexturls)
        titles.extend(nexttitles)

    return urls, titles


def Anime_Episode(url):
    # 1 https://anime1.me/...
    r = requests.post(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    data = soup.find('video', class_='video-js')['data-apireq']
    title = soup.find('h2', class_="entry-title").text

    # #2 https://v.anime1.me/watch?v=...
    # r = requests.post(url,headers = headers)
    # soup = BeautifulSoup(r.text, 'lxml')
    # script_text = soup.find_all("script")[1].string
    # xsend = 'd={}'.format(re.search(r"'d=(.*?)'", script_text, re.M|re.I).group(1))
    xsend = 'd={}'.format(data)

    # 3 APIv2
    r = requests.post('https://v.anime1.me/api', headers=headers, data=xsend)
    text = json.loads(r.text)['s']
    for row in text:
        src = row['src']
        if os.path.splitext(src)[1] == '.mp4':
            url = 'https:{}'.format(src)

    set_cookie = r.headers['set-cookie']
    cookie_e = re.search(r"e=(.*?);", set_cookie, re.M | re.I).group(1)
    cookie_p = re.search(r"p=(.*?);", set_cookie, re.M | re.I).group(1)
    cookie_h = re.search(r"HttpOnly, h=(.*?);",
                         set_cookie, re.M | re.I).group(1)
    cookies = 'e={};p={};h={};'.format(cookie_e, cookie_p, cookie_h)
    MP4_DL(url, title, cookies)


def MP4_DL(Download_URL, Video_Name, Cookies):
    # ???????????????????????????
    chunk_size = 10240

    headers_cookies = {
        "accept": "*/*",
        "accept-encoding": 'identity;q=1, *;q=0',
        "accept-language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        "cookie": Cookies,
        "dnt": '1',
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }

    r = requests.get(Download_URL, headers=headers_cookies, stream=True)
    # ????????????
    content_length = int(r.headers['content-length'])

    if(r.status_code == 200):
        print('+ \033[1;34m{}\033[0m [{:.2f} MB][{}/{}]'.format(Video_Name,
              content_length / 1024 / 1024, NUM+1, NUMS))
        # Progress Bar
        with alive_bar(round(content_length / chunk_size), spinner='ball_scrolling', bar='blocks') as bar:
            with open(os.path.join(download_path,  '{}.mp4'.format(Video_Name)), 'wb') as f:
                for data in r.iter_content(chunk_size=chunk_size):
                    f.write(data)
                    f.flush()
                    bar()
            f.close()
    else:
        print("- \033[1;31mFailure\033[0m???{}".format(r.status_code))


if __name__ == '__main__':
    # ?????? Header
    headers = {
        "Accept": "*/*",
        "Accept-Language": 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        "DNT": "1",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "cookie": "__cfduid=d8db8ce8747b090ff3601ac6d9d22fb951579718376; _ga=GA1.2.1940993661.1579718377; _gid=GA1.2.1806075473.1579718377; _ga=GA1.3.1940993661.1579718377; _gid=GA1.3.1806075473.1579718377",
        "Content-Type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3573.0 Safari/537.36",
    }

    anime_urls = input("? Anime1 URL???").split(',')

    url_list = []
    title_list = []
    for anime_url in anime_urls:
        # ??????????????????
        if re.search(r"anime1.me/category/(.*?)", anime_url, re.M | re.I):
            urls, titles = Anime_Season(anime_url)
            url_list.extend(urls)
            title_list.extend(titles)
        elif re.search(r"anime1.me/[0-9]", anime_url, re.M | re.I):
            r = requests.post(anime_url, headers=headers)
            soup = BeautifulSoup(r.text, 'lxml')
            title_list.append(soup.find('h2', class_="entry-title").text)
            url_list.append(anime_url)
        else:
            print(
                "- \033[1;31mUnable to support this link. QAQ ({})\033[0m".format(anime_url))
            sys.exit(0)

    ## ??????list ##
    url_list.reverse()
    title_list.reverse()

    start_time = time.time()

    ## ????????????????????? ##
    end = re.search(r" \[[0-9]+\]", title_list[0]).span()[0]
    folder_name = title_list[0][:end]  # Get save-folder name
    download_path = "{}/Downloads/{}".format(os.getcwd(), folder_name)
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    ## ?????????????????? ##
    if len(url_list) > 1:
        print('-'*20)
        for i, title in enumerate(title_list):
            print(f"{i+1}. {title}")
        print('-'*20)
        print("????????????????????????????????????")
        chosen = input("???????????????????????????????????????[0~9]????????????????????????[all]??????????????????: ").split(',')

        new_url_list = []
        for i in chosen:
            if i == 'all':
                new_url_list = url_list
            elif "~" not in i:
                new_url_list.append(url_list[int(i)-1])
            else:
                i = i.split('~')
                new_url_list.extend([url_list[j-1]
                                    for j in range(int(i[0]), int(i[1])+1)])
    else:
        new_url_list = url_list

    ## ?????? ##
    NUMS = len(new_url_list)
    for NUM, url in enumerate(new_url_list):
        Anime_Episode(url)

    end_time = time.time()

    print(f"+ ????????? {end_time - start_time} ??????{len(url_list)} ???????????????")