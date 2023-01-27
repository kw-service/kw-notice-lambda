import pymysql
import requests

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fcm import pushNotification
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
}

def crawl_kw_home(conn, cursor):
    BASE_URL = 'https://www.kw.ac.kr/ko/life/notice.jsp?srCategoryId=&mode=list&searchKey=1&searchVal='
    ROOT_URL = 'https://www.kw.ac.kr'
    
    KW_HOME_NEW_TOPIC = 'kw-home-new'
    KW_HOME_EDIT_TOPIC = 'kw-home-edit'
    
    NEW_MESSAGE = '광운대학교에 새 공지사항이 올라왔어요!'
    EDIT_MESSAGE = '광운대학교에 수정된 공지사항이 있어요!'

    r = requests.get(BASE_URL, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')

    board_list = soup.find("div", {"class":"board-list-box"})
    notice_list = board_list.findAll("li")

    query = "SELECT url FROM KW_HOME"
    cursor.execute(query)
    crawled_url_list = set(row[0] for row in cursor.fetchall())
    
    fcm_queue = dict()
    
    print('# Crawled')
    
    for notice in notice_list:
        title = notice.find("div", {"class":"board-text"}).find("a").text.replace('신규게시글','').replace('Attachment','').replace("'",'"').strip()
        tag = notice.find("div", {"class":"board-text"}).find("a").find("strong", {"class":"category"}).text.replace('[','').replace(']','').strip()
        info = notice.find("div", {"class":"board-text"}).find("p", {"class":"info"}).text.split(' | ')
        url = ROOT_URL + notice.find("div", {"class":"board-text"}).find("a").attrs['href'].strip()
        posted_date = info[1].split()[1]
        modified_date = info[2].split()[1]
        department = info[3]
        type = 'KW_HOME'
        crawled_time = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')

        query = ''
        if url in crawled_url_list:
            cursor.execute("SELECT modified_date FROM KW_HOME WHERE url = '{}'".format(url))
            old_modified_date = cursor.fetchone()[0]
            if str(modified_date) != str(old_modified_date):
                query = "UPDATE KW_HOME SET modified_date = '{}', crawled_time = '{}' WHERE url = '{}'".format(modified_date, crawled_time, url)
                print('update -> ' + title)
                fcm_queue[url] = [EDIT_MESSAGE, title, url, KW_HOME_EDIT_TOPIC]
        else:
            query = "INSERT INTO KW_HOME(title, tag, posted_date, modified_date, department, url, type, crawled_time) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}')".format(title, tag, posted_date, modified_date, department, url, type, crawled_time)
            print('insert -> ' + title)
            fcm_queue[url] = [NEW_MESSAGE, title, url, KW_HOME_NEW_TOPIC]
        
        if query != '': cursor.execute(query)
    
    conn.commit()
    
    print('# Push notification')
    
    for k in fcm_queue.keys():
        value = fcm_queue.get(k)
        pushNotification(value[0], value[1], value[2], value[3])
        print('pushed -> ' + value[1])
        time.sleep(1)
    
    queries = ["set SQL_SAFE_UPDATES = 0", "DELETE FROM KW_HOME WHERE crawled_time < date_sub(now(), interval 3 month)", "set SQL_SAFE_UPDATES = 1"]
    for query in queries:
        cursor.execute(query)
    
    conn.commit()