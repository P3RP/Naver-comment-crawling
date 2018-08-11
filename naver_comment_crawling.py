#-*- encoding:utf-8 -*-

import os
import time
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium import webdriver
from openpyxl import Workbook
from bs4 import BeautifulSoup
import requests
import json
import re
import logging.handlers


def my_debug():
    input()
    driver.quit()
    exit()


# MAKE DIRECTORY FOR URLr
def make_dir_url(url, file_name):
    try:
        dir_name = url.replace('https://cafe.naver.com/', '').replace('/', '_').strip()
        if not os.path.exists('./result/' + file_name + '/' + dir_name):
            os.mkdir('./result/' + file_name + '/' + dir_name)
        logger.info("[COMPLETE] 해당 URL({}) Directory 확인/생성 성공".format(url.strip()))
        return dir_name
    except:
        logger.error("[ERROR] 해당 URL({}) Directory 확인/생성 실패".format(url.strip()))
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
    logger.info("[COMPLETE] [{}] Excel 생성 완료".format(name))


# GET ACCOUNT INFO
def get_account_info(file_name):
    try:
        with open('./setting/account/' + file_name) as file:
            logger.info("[COMPLETE] Account File 확인")
            info = file.readlines()

        user_info_list = info[0:2]
        url_info_list = info[2:]

        return [user_info_list, url_info_list]
    except FileNotFoundError:
        logger.error("[ERROR] Account File 확인 실패")
        exit()


# GET COUNT OF JSON PAGES
def get_count_json_url(total, cnt_per_page):
    count = total / cnt_per_page
    if total % cnt_per_page != 0:
        count += 1
    return int(count)


# MAKE JSON URL
def make_json_url(url):
    try:
        bs4 = BeautifulSoup(driver.page_source, 'lxml')
        article_temp = bs4.find('iframe', id='cafe_main').get('src')
        article_temp = article_temp.split('?')
        article_attr = article_temp[1]
        article_attr = article_attr.replace('articleid', 'search.articleid')
        article_attr = article_attr.replace('clubid', 'search.clubid')
        json_chk_url = 'https://cafe.naver.com/CommentView.nhn?' + article_attr

        temp_data = requests.get(json_chk_url).text

        try:
            comment_data = json.loads(temp_data)
            url_chk = 0
        except:
            driver.get(json_chk_url)
            bs4 = BeautifulSoup(driver.page_source, 'lxml')
            comment_data = json.loads(bs4.get_text())
            url_chk = 1

        page_count = get_count_json_url(comment_data['result']['totalCount'], comment_data['result']['countPerPage'])

        json_url_list = []
        for num in range(1, page_count + 1):
            json_url_list.append('https://cafe.naver.com/CommentView.nhn?search.page={}&'.format(num) + article_attr)
        return [json_url_list, url_chk]

    except UnexpectedAlertPresentException:
        alert = driver.switch_to_alert()
        logger.info("[PASS] ({}) ".format(url.strip()), end='')
        logger.info(alert.text)
        return "continue"


# GET COMMENT LIST AND LAST COMMENT
def get_comment_list_json(main_url, json_url_list, run_case, url_case):
    comment_list = []
    new_last_comment_id = -1

    for json_url in json_url_list:
        comment_data = {}
        if url_case == 0:
            temp_data = requests.get(json_url).text
            comment_data = json.loads(temp_data)
        elif url_case == 1:
            driver.get(json_url)
            bs4 = BeautifulSoup(driver.page_source, 'lxml')
            comment_data = json.loads(bs4.get_text())

        for comment in comment_data['result']['list']:
            temp = []
            if run_case == 0:
                if check_history(main_url.strip(), comment["commentid"]):
                    temp.append(comment['writerid'] + '@naver.com')
                    temp.append(comment['content'])
                    temp.append(main_url.strip())
                    temp.append(comment['writedt'])
                    temp.append(get_now_time())
                    comment_list.append(temp)
            elif run_case == 1:
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
    # LOGGER
    logger = logging.getLogger('notice')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[SYSTEM] %(asctime)s :: %(message)s')
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # VARIABLE
    current_path = os.getcwd()

    run_case = -1
    url_case = -1

    comment_list_all = []
    comment_list_url = []

    # =======
    # MAIN
    # STEP 0.1 : Make result directory and log directory
    try:
        if not os.path.exists('./result'):
            os.mkdir('./result')
        logger.info("[COMPLETE] Result Directory 확인/생성 성공")
    except:
        logger.error("[ERROR] Result Directory 확인/생성 실패")
        exit()

    try:
        if not os.path.exists('./setting/log'):
            os.mkdir('./setting/log')
        logger.info("[COMPLETE] Log Directory 확인/생성 성공")
    except:
        logger.error("[ERROR] Log Directory 확인/생성 실패")
        exit()

    # STEP 0.5 Driver initiate
    # while True:
    #     select = int(input("[INPUT] 진행 과정을 보시겠습니까?? (예: 0 | 아니오: 1) : "))
    #
    #     if select == 0:
    #         driver = webdriver.Chrome('./setting/chromedriver.exe')
    #         break
    #     elif select == 1:
    #         options = webdriver.ChromeOptions()
    #         options.add_argument('headless')
    #         options.add_argument('window-size=1920x1080')
    #         options.add_argument("disable-gpu")
    #         driver = webdriver.Chrome('./setting/chromedriver.exe', chrome_options=options)
    #         break
    #     else:
    #         print("[ERROR] 다시 입력하세요")
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")
    driver = webdriver.Chrome('./setting/chromedriver.exe', chrome_options=options)
    driver.maximize_window()
    driver.implicitly_wait(3)

    # STEP 0.2 : Get account file name
    # account_file_name = input("[INPUT] account 파일 이름 입력( 확장자 .txt 입력X ) : ")
    for account_file_name in os.listdir(current_path + '/setting/account/'):
        log_data = {"log": []}
        last_list = {}
        new_log = {}

        os.chdir(current_path)
        info_list = get_account_info(account_file_name)

        # STEP 0.3 : Make result directory for account
        # try:
        #     if not os.path.exists('./result/' + account_file_name):
        #         os.mkdir('./result/' + account_file_name)
        #     print("[COMPLETE] 해당 Account Result Directory 확인/생성 성공")
        # except:
        #     print("[ERROR] 해당 Account Result Directory 확인/생성 실패")
        #     exit()

        # STEP 0.4 : Get latest log
        try:
            with open('./setting/log/' + account_file_name.split('.')[0] + '_log.json') as log_file:
                logger.info("[COMPLETE] Log File 확인")
                log_data = json.load(log_file)
                last_list = log_data['log']['last_comment']
                run_case = 0

        except FileNotFoundError:
            logger.info("[PASS] 최초 실행 (Log File 체크 생략)")
            run_case = 1

        # STEP 0.6 : Sign in
        user_info = info_list[0]

        driver.get('https://nid.naver.com/nidlogin.login')
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="id"]').send_keys(user_info[0].strip())
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="pw"]').send_keys(user_info[1].strip())
        driver.implicitly_wait(3)
        driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()
        driver.implicitly_wait(3)

        # STEP 0.7 : Check whether 'sign in' is completed
        while driver.current_url != 'https://www.naver.com/':
            logger.error("[ERROR] 로그인 실패")
            time.sleep(0.5)
            logger.debug("[FIX] 다시 시도 중...")
            driver.get('https://nid.naver.com/nidlogin.login')
            driver.implicitly_wait(3)
            driver.find_element_by_xpath('//*[@id="id"]').send_keys(user_info[0].strip())
            driver.implicitly_wait(3)
            driver.find_element_by_xpath('//*[@id="pw"]').send_keys(user_info[1].strip())
            driver.implicitly_wait(3)
            driver.find_element_by_xpath('//*[@id="frmNIDLogin"]/fieldset/input').click()
            driver.implicitly_wait(3)
        logger.info("[COMPLETE] 로그인 성공")

        # STEP 1.1 : Set time in log
        new_log['time'] = get_now_time()
        new_log['last_comment'] = {}

        # STEP 1.2 : Make URL list | Move to url
        url_list = info_list[1]
        for main_url in url_list:
            main_url = main_url.strip()
            driver.get(main_url)
            driver.implicitly_wait(3)

            # STEP 1.3 : Check url whether is all view
            # STEP 1.4.1 : Make json url
            message = make_json_url(main_url)
            if message == 'continue':
                continue
            json_url_list = message[0]
            url_case = message[1]

            # STEP 1.4.2 : Get comment list in json url
            temp_list = get_comment_list_json(main_url, json_url_list, run_case, url_case)
            comment_list_url = temp_list[0]
            excel_name = re.sub('[^A-Za-z0-9]+', '', get_now_time())

            # STEP 1.6 : Make url directory and move to directory
            # os.chdir(current_path)
            # dir_name = make_dir_url(main_url, account_file_name)
            # os.chdir(current_path + '/result/' + account_file_name + '/' + dir_name)

            # STEP 1.7 : Make excel for url
            # make_excel(comment_list_url, excel_name)

            # STEP 1.8 : Append comment in all list
            for comment in comment_list_url:
                comment_list_all.append(comment)

            # STEP 1.9 : Set last comment in log
            new_log['last_comment'][main_url.strip()] = temp_list[1]

        # STEP 1.10 : Set run data in log
        log_data['log'] = new_log

        # STEP 1.11 : Make excel for all url
        # os.chdir(current_path + '/result/' + account_file_name)
        # make_excel(comment_list_all, "result_" + re.sub('[^A-Za-z0-9]+', '', get_now_time()))

        # STEP 1.13 : Make log file
        os.chdir(current_path + '/setting/log/')
        try:
            with open(account_file_name.split('.')[0] + '_log.json', 'w', encoding='utf-8') as new_log:
                json.dump(log_data, new_log, ensure_ascii=False, indent='\t')
            logger.info("[COMPLETE] Log File 생성 완료")
        except:
            logger.error("[ERROR] Log File 생성 실패")
            exit()

    # STEP 1.12 : Make excel
    os.chdir(current_path + '/result')
    make_excel(comment_list_all, "result_" + re.sub('[^A-Za-z0-9]+', '', get_now_time()))

    # STEP 1.12 : Quit Driver
    driver.quit()
