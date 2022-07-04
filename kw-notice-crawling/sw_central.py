import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from fcm import pushNotification

def crawl_sw_central(conn, cursor):
    BASE_URL = 'https://npsw.kw.ac.kr/site/sub.php?Tid=27&Ctnum=28&Ctid=HM28&page=1&sg=&st=&search_yes=&Cate='
    ROOT_URL = 'https://npsw.kw.ac.kr/site'
    
    SW_CENTRAL_NEW_TOPIC = 'sw-central-new'
    
    page = requests.get(BASE_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    notice_list = soup.select('div.tbl_notice tbody tr')

    query = "SELECT url FROM SW_CENTRAL"
    cursor.execute(query)
    crawled_url_list = set(row[0] for row in cursor.fetchall())
    pushed_url_list = []

    for notice in notice_list:
        title = notice.select_one('td.left > a').get_text().strip()
        posted_date = notice.select_one('td:nth-child(5)').get_text().replace('/','-').strip()
        url = ROOT_URL + notice.select_one('td.left > a').attrs['href'][1:].strip()
        type = 'SW_CENTRAL'
        crawled_time = (datetime.now() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M:%S')
        
        if url in crawled_url_list or url in pushed_url_list: continue
        query = "INSERT INTO SW_CENTRAL(title, posted_date, url, type, crawled_time) VALUES ('{}','{}','{}','{}','{}')".format(title, posted_date, url, type, crawled_time)
        cursor.execute(query)

        pushNotification('SW중심대학사업단에 새 공지사항이 올라왔어요!', title, url, SW_CENTRAL_NEW_TOPIC)
        pushed_url_list.append(url)
    
    conn.commit()