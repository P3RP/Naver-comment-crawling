#-*- encoding:utf-8 -*-

import os
import time
from selenium import webdriver
from openpyxl import Workbook
from bs4 import BeautifulSoup
import requests
import json


def my_debug():
    input()
    driver.quit()
    exit()


# Make Directory for url
def make_dir_url(url):
    try:
        dir_name = url.replace('https://cafe.naver.com/', '').replace('/', '_').strip()
        if not os.path.exists('./result/' + dir_name):
            os.mkdir('./result/' + dir_name)
        print("[COMPLETE] 해당 URL Directory 확인 성공")
        return dir_name
    except:
        print("[ERROR] 해당 URL Directory 확인 실패")
        exit()


# Make Excel
def make_excel(data_list, name):
    """
        :호출예시 make_excel([ [1,2,3,4], [5,6,7,8] ]) or make_excel(2dArray)
        :param data_list:  [ data1, data2, data3, data4 ] 꼴의 1차원 list를 가지는 2차원 list
        :return: 없
    """
    # === CONFIG
    FILENAME = name + ".xlsx"

    # === SAVE EXCEL
    wb = Workbook()
    ws1 = wb.worksheets[0]
    header1 = ['댓글 아이디(완전한 이메일 형태)', '내용', '크롤링 URL', '작성시각', '현재시각']
    ws1.column_dimensions['A'].width = 30
    ws1.column_dimensions['B'].width = 70
    ws1.column_dimensions['C'].width = 50
    ws1.column_dimensions['D'].width = 20
    ws1.column_dimensions['E'].width = 20
    ws1.append(header1)

    # data save
    for comment_data in data_list:
        ws1.append(comment_data)
    # end
    wb.save(FILENAME)
    print("[COMPLETE] [{}] Excel 생성 완료".format(name))


# USER INFO
def get_user_info(file_name):
    try:
        file = open('./setting/' + file_name)
        print("[COMPLETE] User File 확인")
        user_info_list = file.readlines()
        file.close()
        return user_info_list
    except FileNotFoundError:
        print("[ERROR] User File 확인 실패")
        exit()


# URL List
def get_url_list(file_name):
    try:
        file = open('./setting/' + file_name)
        print("[COMPLETE] URL File 확인")
        url_info_list = file.readlines()
        file.close()
        return url_info_list
    except FileNotFoundError:
        print("[ERROR] URL File 확인 실패")
        exit()


# Make json url
def make_json_url():
    bs4 = BeautifulSoup(driver.page_source, 'lxml')
    article_temp = bs4.find('iframe', id='cafe_main').get('src')
    article_temp = article_temp.split('?')
    article_attr = article_temp[1]
    article_attr = article_attr.replace('articleid', 'search.articleid')
    article_attr = article_attr.replace('clubid', 'search.clubid')
    json_url = 'https://cafe.naver.com/CommentView.nhn?' + article_attr
    return json_url


# Get comment list
def get_comment_list(main_url, json_url):
    comment_list = []

    temp_data = requests.get(json_url).text
    comment_data = json.loads(temp_data)

    for comment in comment_data['result']['list']:
        temp = []
        temp.append(comment['writerid'] + '@naver.com')
        temp.append(comment['content'])
        temp.append(main_url.strip())
        temp.append(comment['writedt'])
        temp.append(get_now_time())

        comment_list.append(temp)
    return comment_list


# Now time
def get_now_time():
    now = time.localtime()
    s = "{0}.{1:0>2}.{2:0>2}. {3}:{4}".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
    return s


if __name__ == "__main__":
    # =======
    # SETTING
    # MAKE RESULT DIRECTORY
    try:
        if not os.path.exists('./result'):
            os.mkdir('./result')
        print("[COMPLETE] Result Directory 확인 성공")
    except:
        print("[ERROR] Result Directory 확인 실패")
        exit()

    # VARIABLE
    current_path = os.getcwd()

    comment_list_all = []
    comment_list_url = []

    # DRIVER INITIATE
    driver = webdriver.Chrome('chromedriver.exe')
    driver.implicitly_wait(3)

    # =======
    # MAIN
    # STEP 0.1 : login

    # STEP 1.1 : Make URL list
    url_list = get_url_list("url.txt")

    # STEP 1.2 : Get comment in each url
    for main_url in url_list:
        # STEP 1.3 : Make url directory and move to directory
        os.chdir(current_path)
        dir_name = make_dir_url(main_url)
        os.chdir(current_path + '/result/' + dir_name)

        # STEP 1.4 : Move to url
        driver.get(main_url)
        driver.implicitly_wait(3)

        # STEP 1.5 : Make json url
        json_url = make_json_url()

        # STEP 1.6 : Get comment list
        comment_list_url = get_comment_list(main_url, json_url)
        excel_name = get_now_time().replace('.', '_').replace(' ', '').replace(':', '_')

        # STEP 1.7 : Make excel for url
        make_excel(comment_list_url, excel_name)

        # STEP 1.8 : Append comment in all list
        for comment in comment_list_url:
            comment_list_all.append(comment)

    # STEP 1.9 : Make excel for all url
    os.chdir(current_path + '/result/')
    make_excel(comment_list_all, "result")

    # STEP 2.1 : Quit Driver
    driver.quit()

    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome('chromedriver.exe', chrome_options=options)
    """


    """
    os.chdir(current_path + '/' + dir_name_dom)
    
    temp = get_now_time()
    print(temp.replace('.', '_').replace(' ', '').replace(':', '_'))
    
    
    user = get_user_info("user.txt")
    url_list = get_url_list("url.txt")
    
    로그인 버튼 : //*[@id="account"]/div/a/i
    """
