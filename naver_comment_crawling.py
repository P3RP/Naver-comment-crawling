#-*- encoding:utf-8 -*-

import os
import time
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium import webdriver
from openpyxl import Workbook
from bs4 import BeautifulSoup
import requests
import json


def my_debug():
    input()
    driver.quit()
    exit()


# MAKE DIRECTORY FOR URL
def make_dir_url(url):
    try:
        dir_name = url.replace('https://cafe.naver.com/', '').replace('/', '_').strip()
        if not os.path.exists('./result/' + dir_name):
            os.mkdir('./result/' + dir_name)
        print("[COMPLETE] 해당 URL({}) Directory 확인 성공".format(url.strip()))
        return dir_name
    except:
        print("[ERROR] 해당 URL({}) Directory 확인 실패".format(url.strip()))
        exit()


# MAKE EXCEL
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

    # DATA SAVE
    for comment_data in data_list:
        ws1.append(comment_data)
    # END
    wb.save(FILENAME)
    print("[COMPLETE] [{}] Excel 생성 완료".format(name))


# GET ACCOUNT INFO
def get_account_info(file_name):
    try:
        file = open('./setting/account/' + file_name)
        print("[COMPLETE] Account File 확인")
        info_list = file.readlines()
        file.close()

        user_info_list = info_list[1:3]
        url_info_list = info_list[5:]

        return [user_info_list, url_info_list]
    except FileNotFoundError:
        print("[ERROR] User File 확인 실패")
        exit()


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


# URL LIST
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


# MAKE JSON URL
def make_json_url(url):
    try:
        bs4 = BeautifulSoup(driver.page_source, 'lxml')
        article_temp = bs4.find('iframe', id='cafe_main').get('src')
        article_temp = article_temp.split('?')
        article_attr = article_temp[1]
        article_attr = article_attr.replace('articleid', 'search.articleid')
        article_attr = article_attr.replace('clubid', 'search.clubid')
        json_url = 'https://cafe.naver.com/CommentView.nhn?' + article_attr
        return json_url
    except UnexpectedAlertPresentException:
        alert = driver.switch_to_alert()
        print("[PASS] ({}) ".format(url.strip()), end='')
        print(alert.text)
        return "continue"


# GET COMMENT LIST AND LAST COMMENT
def get_comment_list(main_url, json_url, case):
    comment_list = []
    new_last_comment_id = -1

    temp_data = requests.get(json_url).text
    comment_data = json.loads(temp_data)

    for comment in comment_data['result']['list']:
        temp = []
        if case == 0:
            if check_history(main_url.strip(), comment["commentid"]):
                temp.append(comment['writerid'] + '@naver.com')
                temp.append(comment['content'])
                temp.append(main_url.strip())
                temp.append(comment['writedt'])
                temp.append(get_now_time())
                comment_list.append(temp)
        elif case == 1:
            temp.append(comment['writerid'] + '@naver.com')
            temp.append(comment['content'])
            temp.append(main_url.strip())
            temp.append(comment['writedt'])
            temp.append(get_now_time())
            comment_list.append(temp)

        if comment["commentid"] > new_last_comment_id:
            new_last_comment_id = comment["commentid"]

    return [comment_list, new_last_comment_id]


# NOW TIME
def get_now_time():
    now = time.localtime()
    s = "{0}.{1:0>2}.{2:0>2}. {3}:{4}".format(now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min)
    return s


# CHECK HISTORY
def check_history(url, comment_id):
    if url in last_list:
        if last_list[url] < comment_id:
            return True
        else:
            return False
    else:
        return True


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

    run_case = -1

    comment_list_all = []
    comment_list_url = []

    log_data = {"log": []}
    last_list = {}
    new_log = {}

    # DRIVER INITIATE
    # driver = webdriver.Chrome('./setting/chromedriver.exe')
    # driver.maximize_window()
    # driver.implicitly_wait(3)

    # GET LATEST LOG
    # try:
    #     with open('./setting/history.json') as log_file:
    #         print("[COMPLETE] Log File 확인")
    #         log_data = json.load(log_file)
    #         last_list = log_data['log']['last_comment']
    #         run_case = 0
    #
    # except FileNotFoundError:
    #     print("[PASS] 최초 실행 (Log File 체크 생략)")
    #     run_case = 1

    # =======
    # MAIN
    # STEP 0.1 : Get account file name
    account_file_name = input("account 파일 이름 입력 : ")

    info_list = get_account_info(account_file_name)






    # STEP 0.1 : Sign in
    user_info = info_list[0]

    driver.get('https://nid.naver.com/nidlogin.login')
    driver.implicitly_wait(3)
    driver.find_element_by_xpath('//*[@id="id"]').send_keys(user_info[0].strip())
    driver.implicitly_wait(3)
    driver.find_element_by_xpath('//*[@id="pw"]').send_keys(user_info[1].strip())
    driver.implicitly_wait(3)
    driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()
    driver.implicitly_wait(3)

    # STEP 0.2 : Check whether 'sign in' is completed
    while driver.current_url != 'https://www.naver.com/':
        print("[ERROR] 로그인 실패")
        time.sleep(0.5)
        print("[FIX] 다시 시도 중...")
        driver.get('https://nid.naver.com/nidlogin.login')
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="id"]').send_keys(user_info[0])
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="pw"]').send_keys(user_info[1])
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()
        driver.implicitly_wait(3)
    print("[COMPLETE] 로그인 성공")

    # STEP 1.0 : Set time in log
    new_log['time'] = get_now_time()
    new_log['last_comment'] = {}

    # STEP 1.1 : Make URL list
    url_list = get_url_list("url.txt")

    # STEP 1.2 : Get comment in each url
    for main_url in url_list:

        # STEP 1.3 : Move to url
        driver.get(main_url)
        driver.implicitly_wait(3)

        # STEP 1.4 : Make json url
        message = make_json_url(main_url)
        if message == 'continue':
            continue
        json_url = message

        # STEP 1.5 : Get comment list
        temp_list = get_comment_list(main_url, json_url, run_case)
        comment_list_url = temp_list[0]
        excel_name = get_now_time().replace('.', '_').replace(' ', '').replace(':', '_')

        # STEP 1.6 : Make url directory and move to directory
        os.chdir(current_path)
        dir_name = make_dir_url(main_url)
        os.chdir(current_path + '/result/' + dir_name)

        # STEP 1.7 : Make excel for url
        make_excel(comment_list_url, excel_name)

        # STEP 1.8 : Append comment in all list
        for comment in comment_list_url:
            comment_list_all.append(comment)

        # STEP 1.9 : Set last comment in log
        new_log['last_comment'][main_url.strip()] = temp_list[1]

    # STEP 1.10 : Set run data in log
    log_data['log'] = new_log

    # STEP 1.11 : Make excel for all url
    os.chdir(current_path + '/result/')
    make_excel(comment_list_all, "result_" + get_now_time().replace('.', '_').replace(' ', '').replace(':', '_'))

    # STEP 2.1 : Quit Driver
    driver.quit()

    # STEP 2.2 : Make log file
    os.chdir(current_path + '/setting')
    try:
        with open('history.json', 'w', encoding='utf-8') as new_log:
            json.dump(log_data, new_log, ensure_ascii=False, indent='\t')
        print("[COMPLETE] Log File 생성 완료")
    except:
        print("[COMPLETE] Log File 생성 실패")
        exit()

    """
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome('chromedriver.exe', chrome_options=options)
    """
