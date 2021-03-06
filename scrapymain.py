import urllib.request
import http.cookiejar
import urllib.parse
from bs4 import BeautifulSoup
import pymysql
import re
import logging


# Setting log
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')
console = logging.StreamHandler()
file_handler = logging.FileHandler('meta-data.log', encoding='utf-8')
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
console.setFormatter(formatter)

logging.getLogger().addHandler(console)
logging.getLogger().addHandler(file_handler)
SCHOOL_CODE_PATTERN = "\[(\d{4})]"  # school code is 4 digit number

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

header = {
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'}

url = 'http://www.heao.gov.cn/datacenter/pages/PZTJ.aspx'

first_query_data = {
    '__EVENTTARGET': '',
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': '/wEPDwULLTEyMTg2OTYxMjQPZBYCZg9kFgYCAQ8WAh4HVmlzaWJsZWhkAgUPFgIfAGhkAgkPDxYKHgxmQ3VycmVudFBhZ2UCAR4RZlRvdGFsUmVjb3JkQ291bnQCkgQeCmZQYWdlQ291bnQCJB4JZlBhZ2VTaXplAg8fAGdkZGTj74r3jZ8WgeGJNTZIullpdv+dkQ==',
    '__VIEWSTATEGENERATOR': '275FA2E0',
    '__EVENTVALIDATION': '/wEWCALXmseEBALwuI29AQKut8n9DwLLuOX4AwK2r/yJBQK6r/CJBgLqhPDLCwLQ0r3uCATSWN7GFwO4c9s2aqf+GrNcf+3s',
    'type': 'YXTJ',
    'button': 'q',
    'ddlNF_YXTJ': '2014',
    'ddlKL_YXTJ': '理科'.encode('gb2312'),
    'ddlPC_YXTJ': '本科第二批'.encode('gb2312'),
    'x': '21',
    'y': '8',
    'iYXMC': 'PagesUpDown$edtPage='
}

first_query_data = urllib.parse.urlencode(first_query_data).encode('utf-8')

request = urllib.request.Request(url, first_query_data, header)
data = urllib.request.urlopen(request)
html_data = data.read().decode('gb2312')

soup = BeautifulSoup(html_data, 'html.parser')

view_state = soup.find(id='__VIEWSTATE')['value']
event_validation = soup.find(id='__EVENTVALIDATION')['value']

logging.info(view_state + '->' + event_validation)

html_table = soup.find('table', id='yxlqqktj_table')
table_rows = html_table.findAll('tr')

# Open a database connection
conn = pymysql.connect(host='localhost', user='root', passwd='789632145', db='dev', port=3306, charset='utf8')
cursor = conn.cursor()


def get_next_page_data(next_page_view_state, next_page_event_validation):
    query_data2 = {
        '__EVENTTARGET': 'PagesUpDown$btnNext',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': next_page_view_state,
        '__VIEWSTATEGENERATOR': '275FA2E0',
        '__EVENTVALIDATION': next_page_event_validation,
        'type': 'YXTJ',
        'button': '',
        'ddlNF_YXTJ': '2014',
        'ddlKL_YXTJ': '理科'.encode('gb2312'),
        'ddlPC_YXTJ': '本科第二批'.encode('gb2312'),
        'iYXMC': '',
        'PagesUpDown$edtPage=': '',
    }
    query_data2 = urllib.parse.urlencode(query_data2).encode('utf-8')
    request2 = urllib.request.Request(url, query_data2, header)
    data2 = urllib.request.urlopen(request2)
    html_data2 = data2.read().decode('gb2312')
    next_page_soup = BeautifulSoup(html_data2, 'html.parser')
    next_page_html_table = next_page_soup.find('table', id='yxlqqktj_table')
    next_page_table_rows = next_page_html_table.findAll('tr')
    extract_data(next_page_table_rows)
    next_page_view_state = next_page_soup.find(id='__VIEWSTATE')['value']
    next_page_event_validation = next_page_soup.find(id='__EVENTVALIDATION')['value']
    return next_page_view_state, next_page_event_validation


def extract_data(table_data):
    global tr, cols, school, matcher_code, school_code, school_name, kl, plan_num, act_num, top_score, min_score, avg_score, UPDATE_STATE
    for tr in table_data:
        cols = tr.findAll('td')
        if cols:
            school = cols[0].text
            matcher_code = re.search(SCHOOL_CODE_PATTERN, school)
            if matcher_code:
                school_code = int(matcher_code.group(1))
                school_name = school[6:]
            kl = 1 if cols[1].text == '理科' else 2
            plan_num = int(cols[2].text)
            act_num = int(cols[3].text)
            top_score = int(cols[4].text)
            min_score = int(cols[5].text)
            avg_score = float(cols[6].text)
            UPDATE_STATE = 'UPDATE SCHOOL_SCORES SET 最低分 = %s, 录取最高分 = %s, 平均分 = %s, 录取人数 = %s WHERE 院校代号 = %s AND 院校名称 = %s AND 省份 = "河南" AND 科别 = %s AND 年份 = %s'
            logging.info('%d,%d,%.1f,%d,%d,%s,%d,%d', min_score, top_score, avg_score, act_num, school_code, school_name, kl, 2014)
            cursor.execute(UPDATE_STATE, (min_score, top_score, avg_score, act_num, school_code, school_name, kl, 2014))
            conn.commit()


view_state, event_validation = get_next_page_data(view_state, event_validation)
# extract_data(table_rows)


while view_state and event_validation:
    logging.info(view_state + '->' + event_validation)
    view_state, event_validation = get_next_page_data(view_state, event_validation)






