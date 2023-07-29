from flask import Flask, Response, render_template, url_for, redirect, request, flash, session, app
import sqlite3
import re
import hashlib
import os
import secrets


import time
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
import requests
import ssl

from pykrx import stock
import pandas as pd

# https://pypi.org/project/stockstats/
from stockstats import wrap
import yfinance as yf

from flask_bcrypt import Bcrypt



app=Flask(__name__)

# App Configuration
app.secret_key = os.environ.get('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=30)

bcrypt = Bcrypt(app)

# Database configuration
DATABASE = 'database.db'


def create_table():
 with sqlite3.connect(DATABASE) as conn:
  cursor = conn.cursor()
  cursor.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT UNIQUE NOT NULL,
                           email TEXT UNIQUE NOT NULL,
                           password_hash TEXT NOT NULL)''')


def insert_user(username, email, password):
 # password_hash = hashlib.sha256(password.encode()).hexdigest()
 password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
 with sqlite3.connect(DATABASE) as conn:
  cursor = conn.cursor()
  try:
   cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, password_hash))
   conn.commit()
   return True
  except sqlite3.IntegrityError:
   return False


def get_user(username):
 with sqlite3.connect(DATABASE) as conn:
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM users WHERE username=?", (username,))
  return cursor.fetchone()


def get_user_by_email(useremail):
 with sqlite3.connect(DATABASE) as conn:
  cursor = conn.cursor()
  cursor.execute("SELECT password_hash FROM users WHERE email=?", (useremail,))
  return cursor.fetchone()

# 비밀번호 변경
def update_password(username, email, new_password):
 new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
 with sqlite3.connect(DATABASE) as conn:
  cursor = conn.cursor()
  try:
   cursor.execute("UPDATE users SET password_hash = ? WHERE username=?", (new_password_hash, username))
   conn.commit()
   return True
  except sqlite3.IntegrityError:
   return False

create_table()


def validate_password(password):
 return len(password) >= 8


def validate_username(username):
 return len(username) >= 3


def validate_email(email):
 # Simple email validation using regular expression
 pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
 return re.match(pattern, email)

"""
#'https://www.worldometers.info/coronavirus
url='https://en.m.wikipedia.org/wiki/List_of_largest_Internet_companies'
req=requests.get(url)
bsObj=BeautifulSoup(req.text,"html.parser")

data=bsObj.find('table',{'class':'wikitable sortable mw-collapsible'})

table_data=[]
trs=bsObj.select('table tr')

for tr in trs[1:6]: #first element is empty - 
	row=[]
	for t in tr.select('td')[:3]:
		row.extend([t.text.strip()])
	table_data.append(row)
data=table_data
"""

# 여기부터 내가 작성
"""
url = "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401"

response = requests.get(url, verify=False)
soup = BeautifulSoup(response.text, 'html.parser')

dd_tags = soup.find_all('dd', class_='articleSubject')
titles = []; hrefs = []

for dd in dd_tags:
    title = dd.find('a').text; titles.append(title)
    href = dd.find('a')['href']; hrefs.append(href.partition("&type")[0])
"""

# 여기까지 내가 작성


"""모든 한국 주식 리스트 만들기 (변수명 = KR_tickers)"""
# 오늘 날짜를 8자리 string으로
today_str = str(date.today().strftime('%Y%m%d'))

KOSPI_tickers = stock.get_market_ticker_list(today_str, market="KOSPI")
KOSDAQ_tickers = stock.get_market_ticker_list(today_str, market="KOSDAQ")

# KR_tickers = KOSPI_tickers + KOSDAQ_tickers

"""모든 미국 주식 리스트 만들기 (변수명 = US_tickers)"""
# 미국 주식 티커들 모음: https://github.com/rreichel3/US-Stock-Symbols

US_tickers = ['A', 'AA', 'AAC', 'AACG', 'AACI', 'AACIW', 'AACT', 'AADI', 'AAIC', 'AAIN', 'AAL', 'AAM', 'AAME', 'AAN',
              'AAOI', 'AAON', 'AAP', 'AAPL', 'AAT', 'AB', 'ABBV', 'ABC', 'ABCB', 'ABCL', 'ABCM', 'ABEO', 'ABEV', 'ABG',
              'ABIO', 'ABL', 'ABLLW', 'ABM', 'ABNB', 'ABOS', 'ABR', 'ABSI', 'ABST', 'ABT', 'ABUS', 'ABVC', 'AC', 'ACA',
              'ACAB', 'ACABU', 'ACABW', 'ACAC', 'ACACW', 'ACAD', 'ACAH', 'ACAHW', 'ACAX', 'ACAXR', 'ACAXU', 'ACAXW',
              'ACB', 'ACBA', 'ACBAU', 'ACBAW', 'ACCD', 'ACCO', 'ACDC', 'ACDCW', 'ACEL', 'ACER', 'ACET', 'ACGL',
              'ACGLN', 'ACGLO', 'ACGN', 'ACHC', 'ACHL', 'ACHR', 'ACHV', 'ACI', 'ACIU', 'ACIW', 'ACLS', 'ACLX', 'ACM',
              'ACMR', 'ACN', 'ACNB', 'ACNT', 'ACON', 'ACONW', 'ACOR', 'ACP', 'ACR', 'ACRE', 'ACRO', 'ACRS', 'ACRV',
              'ACRX', 'ACST', 'ACT', 'ACTG', 'ACV', 'ACVA', 'ACXP', 'ADAG', 'ADAP', 'ADBE', 'ADC', 'ADCT', 'ADD',
              'ADEA', 'ADER', 'ADERU', 'ADERW', 'ADES', 'ADI', 'ADIL', 'ADILW', 'ADM', 'ADMA', 'ADMP', 'ADN', 'ADNT',
              'ADNWW', 'ADOC', 'ADOCR', 'ADOCW', 'ADP', 'ADPT', 'ADSE', 'ADSEW', 'ADSK', 'ADT', 'ADTH', 'ADTHW',
              'ADTN', 'ADTX', 'ADUS', 'ADV', 'ADVM', 'ADVWW', 'ADX', 'ADXN', 'AEAE', 'AEE', 'AEFC', 'AEG', 'AEHL',
              'AEHR', 'AEI', 'AEIS', 'AEL', 'AEM', 'AEMD', 'AENT', 'AENTW', 'AENZ', 'AEO', 'AEP', 'AEPPZ', 'AER',
              'AES', 'AESC', 'AESI', 'AEVA', 'AEY', 'AEYE', 'AEZS', 'AFAR', 'AFARU', 'AFB', 'AFBI', 'AFCG', 'AFG',
              'AFGB', 'AFGC', 'AFGD', 'AFGE', 'AFIB', 'AFL', 'AFMD', 'AFRI', 'AFRIW', 'AFRM', 'AFT', 'AFTR', 'AFYA',
              'AG', 'AGAC', 'AGAE', 'AGBA', 'AGCO', 'AGD', 'AGEN', 'AGFY', 'AGI', 'AGIL', 'AGILW', 'AGIO', 'AGL',
              'AGLE', 'AGM', 'AGMH', 'AGNC', 'AGNCL', 'AGNCM', 'AGNCN', 'AGNCO', 'AGNCP', 'AGO', 'AGR', 'AGRI',
              'AGRIW', 'AGRO', 'AGRX', 'AGS', 'AGTI', 'AGX', 'AGYS', 'AHCO', 'AHG', 'AHH', 'AHI', 'AHL', 'AHT', 'AI',
              'AIB', 'AIC', 'AIF', 'AIG', 'AIH', 'AIHS', 'AIMAW', 'AIMBU', 'AIMD', 'AIMDW', 'AIN', 'AIO', 'AIP', 'AIR',
              'AIRC', 'AIRG', 'AIRS', 'AIRT', 'AIRTP', 'AIT', 'AIU', 'AIV', 'AIXI', 'AIZ', 'AIZN', 'AJG', 'AJRD',
              'AJX', 'AJXA', 'AKA', 'AKAM', 'AKAN', 'AKBA', 'AKLI', 'AKO', 'AKR', 'AKRO', 'AKTS', 'AKTX', 'AKU',
              'AKYA', 'AL', 'ALAR', 'ALB', 'ALBT', 'ALC', 'ALCC', 'ALCO', 'ALCY', 'ALCYU', 'ALCYW', 'ALDX', 'ALE',
              'ALEC', 'ALEX', 'ALG', 'ALGM', 'ALGN', 'ALGS', 'ALGT', 'ALHC', 'ALIM', 'ALIT', 'ALK', 'ALKS', 'ALKT',
              'ALL', 'ALLE', 'ALLG', 'ALLK', 'ALLO', 'ALLR', 'ALLT', 'ALLY', 'ALNY', 'ALOR', 'ALORW', 'ALOT', 'ALPN',
              'ALPP', 'ALRM', 'ALRN', 'ALRS', 'ALSA', 'ALSAR', 'ALSAU', 'ALSAW', 'ALSN', 'ALT', 'ALTG', 'ALTI', 'ALTO',
              'ALTR', 'ALTU', 'ALTUW', 'ALV', 'ALVO', 'ALVOW', 'ALVR', 'ALX', 'ALXO', 'ALYA', 'ALZN', 'AM', 'AMAL',
              'AMAM', 'AMAO', 'AMAOU', 'AMAOW', 'AMAT', 'AMBA', 'AMBC', 'AMBP', 'AMC', 'AMCR', 'AMCX', 'AMD', 'AME',
              'AMED', 'AMEH', 'AMG', 'AMGN', 'AMH', 'AMK', 'AMKR', 'AMLI', 'AMLX', 'AMN', 'AMNB', 'AMOT', 'AMP',
              'AMPG', 'AMPGW', 'AMPH', 'AMPL', 'AMPS', 'AMPX', 'AMPY', 'AMR', 'AMRC', 'AMRK', 'AMRN', 'AMRS', 'AMRX',
              'AMSC', 'AMSF', 'AMST', 'AMSWA', 'AMT', 'AMTB', 'AMTD', 'AMTI', 'AMTX', 'AMWD', 'AMWL', 'AMX', 'AMZN',
              'AN', 'ANAB', 'ANDE', 'ANEB', 'ANET', 'ANF', 'ANGH', 'ANGHW', 'ANGI', 'ANGO', 'ANIK', 'ANIP', 'ANIX',
              'ANNX', 'ANSS', 'ANTE', 'ANTX', 'ANVS', 'ANY', 'ANZU', 'ANZUW', 'AOD', 'AOGO', 'AOGOU', 'AOGOW', 'AOMR',
              'AON', 'AORT', 'AOS', 'AOSL', 'AOUT', 'AP', 'APA', 'APAC', 'APACW', 'APAM', 'APCA', 'APCX', 'APCXW',
              'APD', 'APDN', 'APE', 'APEI', 'APG', 'APGB', 'APGE', 'APGN', 'APGNW', 'APH', 'API', 'APLD', 'APLE',
              'APLM', 'APLMW', 'APLS', 'APLT', 'APM', 'APMI', 'APMIU', 'APMIW', 'APO', 'APOG', 'APP', 'APPF', 'APPH',
              'APPHW', 'APPN', 'APPS', 'APRE', 'APRN', 'APTM', 'APTMW', 'APTO', 'APTV', 'APVO', 'APWC', 'APXI',
              'APXIU', 'APXIW', 'APYX', 'AQB', 'AQMS', 'AQN', 'AQNA', 'AQNB', 'AQNU', 'AQST', 'AQU', 'AQUNR', 'AR',
              'ARAV', 'ARAY', 'ARBB', 'ARBE', 'ARBEW', 'ARBG', 'ARBGU', 'ARBGW', 'ARBK', 'ARBKL', 'ARC', 'ARCB',
              'ARCC', 'ARCE', 'ARCH', 'ARCO', 'ARCT', 'ARDC', 'ARDX', 'ARE', 'AREB', 'AREBW', 'AREC', 'ARES', 'ARGD',
              'ARGO', 'ARGX', 'ARHS', 'ARI', 'ARIS', 'ARIZ', 'ARIZW', 'ARKO', 'ARKOW', 'ARKR', 'ARL', 'ARLO', 'ARLP',
              'ARMK', 'ARNC', 'AROC', 'AROW', 'ARQQ', 'ARQQW', 'ARQT', 'ARR', 'ARRW', 'ARRWU', 'ARRWW', 'ARRY', 'ARTE',
              'ARTEU', 'ARTEW', 'ARTL', 'ARTLW', 'ARTNA', 'ARTW', 'ARVL', 'ARVN', 'ARW', 'ARWR', 'ARYD', 'ASA', 'ASAI',
              'ASAN', 'ASB', 'ASBA', 'ASC', 'ASCA', 'ASCAR', 'ASCAW', 'ASCB', 'ASCBR', 'ASG', 'ASGI', 'ASGN', 'ASH',
              'ASIX', 'ASLE', 'ASLN', 'ASMB', 'ASML', 'ASND', 'ASNS', 'ASO', 'ASPA', 'ASPAW', 'ASPI', 'ASPN', 'ASPS',
              'ASR', 'ASRT', 'ASRV', 'ASST', 'ASTC', 'ASTE', 'ASTI', 'ASTL', 'ASTLW', 'ASTR', 'ASTS', 'ASTSW', 'ASUR',
              'ASX', 'ASYS', 'ATAI', 'ATAK', 'ATAKR', 'ATAKW', 'ATAT', 'ATCO', 'ATCOL', 'ATEC', 'ATEN', 'ATER', 'ATEX',
              'ATGE', 'ATH', 'ATHA', 'ATHE', 'ATHM', 'ATHX', 'ATI', 'ATIF', 'ATIP', 'ATKR', 'ATLC', 'ATLCL', 'ATLCP',
              'ATLO', 'ATLX', 'ATMC', 'ATMCU', 'ATMCW', 'ATMU', 'ATMV', 'ATMVU', 'ATNF', 'ATNFW', 'ATNI', 'ATO',
              'ATOM', 'ATOS', 'ATR', 'ATRA', 'ATRC', 'ATRI', 'ATRO', 'ATS', 'ATSG', 'ATUS', 'ATVI', 'ATXG', 'ATXI',
              'ATXS', 'AU', 'AUB', 'AUBN', 'AUDC', 'AUGX', 'AUID', 'AUPH', 'AUR', 'AURA', 'AURC', 'AURCU', 'AURCW',
              'AUROW', 'AUTL', 'AUUD', 'AUUDW', 'AUVI', 'AUVIP', 'AVA', 'AVAH', 'AVAL', 'AVAV', 'AVB', 'AVD', 'AVDL',
              'AVDX', 'AVGO', 'AVGR', 'AVHI', 'AVHIW', 'AVID', 'AVIR', 'AVK', 'AVNS', 'AVNT', 'AVNW', 'AVO', 'AVPT',
              'AVPTW', 'AVRO', 'AVT', 'AVTA', 'AVTE', 'AVTR', 'AVTX', 'AVXL', 'AVY', 'AWF', 'AWH', 'AWI', 'AWIN',
              'AWINW', 'AWK', 'AWP', 'AWR', 'AWRE', 'AX', 'AXDX', 'AXGN', 'AXL', 'AXLA', 'AXNX', 'AXON', 'AXP', 'AXR',
              'AXS', 'AXSM', 'AXTA', 'AXTI', 'AY', 'AYI', 'AYRO', 'AYTU', 'AYX', 'AZ', 'AZEK', 'AZN', 'AZO', 'AZPN',
              'AZTA', 'AZUL', 'AZYO', 'AZZ', 'B', 'BA', 'BABA', 'BAC', 'BACK', 'BAER', 'BAERW', 'BAFN', 'BAH', 'BAK',
              'BALL', 'BALY', 'BAM', 'BANC', 'BAND', 'BANF', 'BANFP', 'BANL', 'BANR', 'BANX', 'BAOS', 'BAP', 'BARK',
              'BASE', 'BATRA', 'BATRK', 'BAX', 'BB', 'BBAI', 'BBAR', 'BBCP', 'BBD', 'BBDC', 'BBDO', 'BBGI', 'BBIG',
              'BBIO', 'BBLG', 'BBLGW', 'BBN', 'BBSI', 'BBU', 'BBUC', 'BBVA', 'BBW', 'BBWI', 'BBY', 'BC', 'BCAB',
              'BCAL', 'BCAN', 'BCAT', 'BCBP', 'BCC', 'BCDA', 'BCDAW', 'BCE', 'BCEL', 'BCH', 'BCLI', 'BCML', 'BCO',
              'BCOV', 'BCOW', 'BCPC', 'BCRX', 'BCS', 'BCSA', 'BCSAU', 'BCSAW', 'BCSF', 'BCTX', 'BCTXW', 'BCX', 'BCYC',
              'BDC', 'BDJ', 'BDN', 'BDRX', 'BDSX', 'BDTX', 'BDX', 'BE', 'BEAM', 'BEAT', 'BEATW', 'BECN', 'BEDU',
              'BEEM', 'BEEMW', 'BEKE', 'BELFA', 'BELFB', 'BEN', 'BENF', 'BENFW', 'BEP', 'BEPC', 'BEPH', 'BEPI', 'BERY',
              'BEST', 'BF', 'BFAC', 'BFAM', 'BFC', 'BFH', 'BFI', 'BFIIW', 'BFIN', 'BFK', 'BFLY', 'BFRG', 'BFRGW',
              'BFRI', 'BFRIW', 'BFS', 'BFST', 'BFZ', 'BG', 'BGB', 'BGC', 'BGFV', 'BGH', 'BGLC', 'BGNE', 'BGR', 'BGS',
              'BGSF', 'BGT', 'BGX', 'BGXX', 'BGY', 'BH', 'BHAC', 'BHACW', 'BHAT', 'BHC', 'BHE', 'BHF', 'BHFAL',
              'BHFAM', 'BHFAN', 'BHFAO', 'BHFAP', 'BHG', 'BHIL', 'BHK', 'BHLB', 'BHP', 'BHR', 'BHRB', 'BHV', 'BHVN',
              'BIAF', 'BIAFW', 'BIDU', 'BIG', 'BIGC', 'BIGZ', 'BIIB', 'BILI', 'BILL', 'BIMI', 'BIO', 'BIOC', 'BIOL',
              'BIOR', 'BIOS', 'BIOSU', 'BIOSW', 'BIOX', 'BIP', 'BIPC', 'BIPH', 'BIPI', 'BIRD', 'BIT', 'BITF', 'BIVI',
              'BJ', 'BJDX', 'BJRI', 'BK', 'BKCC', 'BKD', 'BKDT', 'BKE', 'BKH', 'BKI', 'BKKT', 'BKN', 'BKNG', 'BKR',
              'BKSC', 'BKSY', 'BKT', 'BKU', 'BKYI', 'BL', 'BLAC', 'BLACR', 'BLACU', 'BLACW', 'BLBD', 'BLBX', 'BLCO',
              'BLD', 'BLDE', 'BLDEW', 'BLDP', 'BLDR', 'BLE', 'BLEU', 'BLEUR', 'BLEUW', 'BLFS', 'BLFY', 'BLIN', 'BLK',
              'BLKB', 'BLMN', 'BLND', 'BLNG', 'BLNGU', 'BLNGW', 'BLNK', 'BLPH', 'BLRX', 'BLTE', 'BLUE', 'BLW', 'BLX',
              'BLZE', 'BMA', 'BMAC', 'BMBL', 'BME', 'BMEA', 'BMEZ', 'BMI', 'BML', 'BMN', 'BMO', 'BMR', 'BMRA', 'BMRC',
              'BMRN', 'BMY', 'BN', 'BNED', 'BNGO', 'BNGOW', 'BNH', 'BNIX', 'BNIXR', 'BNIXW', 'BNJ', 'BNL', 'BNMV',
              'BNOX', 'BNR', 'BNRE', 'BNRG', 'BNS', 'BNTC', 'BNTX', 'BNY', 'BOAC', 'BOC', 'BOCN', 'BOCNW', 'BODY',
              'BOE', 'BOF', 'BOH', 'BOKF', 'BOLT', 'BON', 'BOOM', 'BOOT', 'BORR', 'BOSC', 'BOTJ', 'BOWL', 'BOWNU',
              'BOX', 'BOXL', 'BP', 'BPMC', 'BPOP', 'BPOPM', 'BPRN', 'BPT', 'BPTH', 'BPTS', 'BPYPM', 'BPYPN', 'BPYPO',
              'BPYPP', 'BQ', 'BR', 'BRAC', 'BRACR', 'BRAG', 'BRBR', 'BRC', 'BRCC', 'BRD', 'BRDG', 'BRDS', 'BREA',
              'BREZ', 'BREZR', 'BREZW', 'BRFH', 'BRFS', 'BRID', 'BRK', 'BRKH', 'BRKHU', 'BRKHW', 'BRKL', 'BRKR',
              'BRLI', 'BRLIR', 'BRLIU', 'BRLIW', 'BRLT', 'BRO', 'BROG', 'BROGW', 'BROS', 'BRP', 'BRQS', 'BRSH',
              'BRSHW', 'BRSP', 'BRT', 'BRTX', 'BRW', 'BRX', 'BRY', 'BRZE', 'BSAC', 'BSBK', 'BSBR', 'BSET', 'BSFC',
              'BSGM', 'BSIG', 'BSL', 'BSM', 'BSQR', 'BSRR', 'BST', 'BSTZ', 'BSVN', 'BSX', 'BSY', 'BTA', 'BTAI', 'BTB',
              'BTBD', 'BTBDW', 'BTBT', 'BTCM', 'BTCS', 'BTCY', 'BTDR', 'BTE', 'BTI', 'BTM', 'BTMD', 'BTMWW', 'BTO',
              'BTOG', 'BTT', 'BTTX', 'BTU', 'BTWN', 'BTWNU', 'BTWNW', 'BTZ', 'BUD', 'BUI', 'BUJAU', 'BUR', 'BURL',
              'BUSE', 'BV', 'BVH', 'BVN', 'BVS', 'BVXV', 'BW', 'BWA', 'BWAQ', 'BWAQW', 'BWAY', 'BWB', 'BWBBP', 'BWC',
              'BWEN', 'BWFG', 'BWG', 'BWMN', 'BWMX', 'BWNB', 'BWSN', 'BWV', 'BWXT', 'BX', 'BXC', 'BXMT', 'BXMX', 'BXP',
              'BXRX', 'BXSL', 'BY', 'BYD', 'BYFC', 'BYM', 'BYN', 'BYND', 'BYNO', 'BYNOU', 'BYNOW', 'BYRN', 'BYSI',
              'BYTS', 'BYTSW', 'BZ', 'BZFD', 'BZFDW', 'BZH', 'BZUN', 'C', 'CAAP', 'CAAS', 'CABA', 'CABO', 'CAC',
              'CACC', 'CACI', 'CACO', 'CADE', 'CADL', 'CAE', 'CAF', 'CAG', 'CAH', 'CAKE', 'CAL', 'CALB', 'CALC',
              'CALM', 'CALT', 'CALX', 'CAMP', 'CAMT', 'CAN', 'CANB', 'CANG', 'CANO', 'CAPL', 'CAPR', 'CAR', 'CARA',
              'CARE', 'CARG', 'CARM', 'CARR', 'CARS', 'CARV', 'CASA', 'CASH', 'CASI', 'CASS', 'CASY', 'CAT', 'CATC',
              'CATO', 'CATY', 'CAVA', 'CB', 'CBAN', 'CBAT', 'CBAY', 'CBD', 'CBFV', 'CBH', 'CBIO', 'CBL', 'CBNK',
              'CBRE', 'CBRG', 'CBRGU', 'CBRGW', 'CBRL', 'CBSH', 'CBT', 'CBU', 'CBUS', 'CBZ', 'CC', 'CCAI', 'CCAIU',
              'CCAIW', 'CCAP', 'CCB', 'CCBG', 'CCCC', 'CCCS', 'CCD', 'CCEP', 'CCI', 'CCJ', 'CCK', 'CCL', 'CCLD',
              'CCLDO', 'CCLDP', 'CCLP', 'CCM', 'CCNE', 'CCNEP', 'CCO', 'CCOI', 'CCRD', 'CCRN', 'CCS', 'CCSI', 'CCTS',
              'CCU', 'CCV', 'CCVI', 'CCZ', 'CD', 'CDAQU', 'CDAQW', 'CDAY', 'CDE', 'CDIO', 'CDIOW', 'CDLX', 'CDMO',
              'CDNA', 'CDNS', 'CDR', 'CDRE', 'CDRO', 'CDROW', 'CDTX', 'CDW', 'CDXC', 'CDXS', 'CDZI', 'CDZIP', 'CE',
              'CEAD', 'CEADW', 'CECO', 'CEE', 'CEG', 'CEIX', 'CELC', 'CELH', 'CELL', 'CELU', 'CELUW', 'CELZ', 'CEM',
              'CEN', 'CENN', 'CENT', 'CENTA', 'CENX', 'CEPU', 'CEQP', 'CERE', 'CERS', 'CERT', 'CETUR', 'CETUW', 'CETX',
              'CETXP', 'CETY', 'CEVA', 'CF', 'CFB', 'CFBK', 'CFFE', 'CFFEU', 'CFFEW', 'CFFI', 'CFFN', 'CFFS', 'CFFSW',
              'CFG', 'CFIV', 'CFIVU', 'CFIVW', 'CFLT', 'CFMS', 'CFR', 'CFRX', 'CFSB', 'CG', 'CGA', 'CGABL', 'CGAU',
              'CGBD', 'CGC', 'CGEM', 'CGEN', 'CGNT', 'CGNX', 'CGO', 'CGRN', 'CGTX', 'CHCI', 'CHCO', 'CHCT', 'CHD',
              'CHDN', 'CHE', 'CHEA', 'CHEAW', 'CHEF', 'CHEK', 'CHGG', 'CHH', 'CHI', 'CHK', 'CHKEL', 'CHKEW', 'CHKEZ',
              'CHKP', 'CHMG', 'CHMI', 'CHN', 'CHNR', 'CHPT', 'CHRD', 'CHRS', 'CHRW', 'CHS', 'CHSCL', 'CHSCM', 'CHSCN',
              'CHSCO', 'CHSCP', 'CHSN', 'CHT', 'CHTR', 'CHUY', 'CHW', 'CHWY', 'CHX', 'CHY', 'CI', 'CIA', 'CIB', 'CIEN',
              'CIF', 'CIFR', 'CIFRW', 'CIG', 'CIGI', 'CII', 'CIM', 'CINF', 'CING', 'CINGW', 'CINT', 'CIO', 'CION',
              'CIR', 'CISO', 'CISS', 'CITE', 'CITEW', 'CIVB', 'CIVI', 'CIZN', 'CJET', 'CJJD', 'CKPT', 'CL', 'CLAR',
              'CLAY', 'CLAYU', 'CLAYW', 'CLB', 'CLBK', 'CLBT', 'CLBTW', 'CLCO', 'CLDT', 'CLDX', 'CLEU', 'CLF', 'CLFD',
              'CLGN', 'CLH', 'CLIN', 'CLINR', 'CLIR', 'CLLS', 'CLMB', 'CLMT', 'CLNE', 'CLNN', 'CLNNW', 'CLOE', 'CLOER',
              'CLOV', 'CLPR', 'CLPS', 'CLPT', 'CLRB', 'CLRC', 'CLRCR', 'CLRCW', 'CLRO', 'CLS', 'CLSD', 'CLSK', 'CLST',
              'CLVR', 'CLVRW', 'CLVT', 'CLW', 'CLWT', 'CLX', 'CM', 'CMA', 'CMAX', 'CMAXW', 'CMBM', 'CMC', 'CMCA',
              'CMCM', 'CMCO', 'CMCSA', 'CMCT', 'CME', 'CMG', 'CMI', 'CMLS', 'CMMB', 'CMND', 'CMP', 'CMPO', 'CMPOW',
              'CMPR', 'CMPS', 'CMPX', 'CMRA', 'CMRAW', 'CMRE', 'CMRX', 'CMS', 'CMSA', 'CMSC', 'CMSD', 'CMTG', 'CMTL',
              'CMU', 'CNA', 'CNC', 'CNDA', 'CNDB', 'CNDT', 'CNET', 'CNEY', 'CNF', 'CNFR', 'CNFRL', 'CNGL', 'CNGLW',
              'CNHI', 'CNI', 'CNK', 'CNM', 'CNMD', 'CNNE', 'CNO', 'CNOB', 'CNOBP', 'CNP', 'CNQ', 'CNS', 'CNSL', 'CNSP',
              'CNTA', 'CNTB', 'CNTG', 'CNTX', 'CNTY', 'CNVS', 'CNX', 'CNXA', 'CNXC', 'CNXN', 'COCO', 'COCP', 'CODA',
              'CODI', 'CODX', 'COEP', 'COEPW', 'COF', 'COFS', 'COGT', 'COHR', 'COHU', 'COIN', 'COKE', 'COLB', 'COLD',
              'COLL', 'COLM', 'COMM', 'COMP', 'COMS', 'COMSP', 'COMSW', 'CONN', 'CONX', 'CONXW', 'COO', 'COOK', 'COOL',
              'COOLW', 'COOP', 'COP', 'CORR', 'CORT', 'COSM', 'COST', 'COTY', 'COUR', 'COYA', 'CP', 'CPA', 'CPAA',
              'CPAAU', 'CPAAW', 'CPAC', 'CPB', 'CPE', 'CPF', 'CPG', 'CPHC', 'CPIX', 'CPK', 'CPLP', 'CPNG', 'CPOP',
              'CPRI', 'CPRT', 'CPRX', 'CPS', 'CPSH', 'CPSI', 'CPSS', 'CPT', 'CPTK', 'CPTN', 'CPTNW', 'CPUH', 'CPZ',
              'CR', 'CRAI', 'CRBG', 'CRBP', 'CRBU', 'CRC', 'CRCT', 'CRD', 'CRDF', 'CRDL', 'CRDO', 'CREG', 'CRESW',
              'CRESY', 'CREX', 'CREXW', 'CRGE', 'CRGO', 'CRGOW', 'CRGY', 'CRH', 'CRI', 'CRIS', 'CRK', 'CRKN', 'CRL',
              'CRM', 'CRMD', 'CRMT', 'CRNC', 'CRNT', 'CRNX', 'CRON', 'CROX', 'CRS', 'CRSP', 'CRSR', 'CRT', 'CRTO',
              'CRUS', 'CRVL', 'CRVS', 'CRWD', 'CRWS', 'CSAN', 'CSBR', 'CSCO', 'CSGP', 'CSGS', 'CSIQ', 'CSL', 'CSLM',
              'CSLR', 'CSLRW', 'CSPI', 'CSQ', 'CSR', 'CSSE', 'CSSEL', 'CSSEN', 'CSSEP', 'CSTA', 'CSTE', 'CSTL', 'CSTM',
              'CSTR', 'CSV', 'CSWC', 'CSWCZ', 'CSWI', 'CSX', 'CTA', 'CTAS', 'CTBB', 'CTBI', 'CTCX', 'CTCXW', 'CTDD',
              'CTG', 'CTHR', 'CTIB', 'CTKB', 'CTLP', 'CTLT', 'CTMX', 'CTO', 'CTOS', 'CTR', 'CTRA', 'CTRE', 'CTRM',
              'CTRN', 'CTS', 'CTSH', 'CTSO', 'CTV', 'CTVA', 'CTXR', 'CUBA', 'CUBB', 'CUBE', 'CUBI', 'CUE', 'CUEN',
              'CUK', 'CULL', 'CULP', 'CURI', 'CURIW', 'CURO', 'CURV', 'CUTR', 'CUZ', 'CVAC', 'CVBF', 'CVCO', 'CVCY',
              'CVE', 'CVEO', 'CVGI', 'CVGW', 'CVI', 'CVII', 'CVKD', 'CVLG', 'CVLT', 'CVLY', 'CVNA', 'CVRX', 'CVS',
              'CVV', 'CVX', 'CW', 'CWAN', 'CWBC', 'CWBR', 'CWCO', 'CWD', 'CWEN', 'CWH', 'CWK', 'CWST', 'CWT', 'CX',
              'CXAC', 'CXAI', 'CXAIW', 'CXDO', 'CXE', 'CXH', 'CXM', 'CXT', 'CXW', 'CYAN', 'CYBR', 'CYCC', 'CYCCP',
              'CYCN', 'CYD', 'CYH', 'CYN', 'CYRX', 'CYT', 'CYTH', 'CYTHW', 'CYTK', 'CYTO', 'CZFS', 'CZNC', 'CZOO',
              'CZR', 'CZWI', 'D', 'DAC', 'DADA', 'DAIO', 'DAKT', 'DAL', 'DALN', 'DALS', 'DAN', 'DAO', 'DAR', 'DARE',
              'DASH', 'DATS', 'DATSW', 'DAVA', 'DAVE', 'DAVEW', 'DAWN', 'DB', 'DBGI', 'DBGIW', 'DBI', 'DBL', 'DBRG',
              'DBTX', 'DBVT', 'DBX', 'DCBO', 'DCF', 'DCFC', 'DCFCW', 'DCGO', 'DCI', 'DCO', 'DCOM', 'DCOMP', 'DCP',
              'DCPH', 'DCTH', 'DD', 'DDD', 'DDI', 'DDL', 'DDOG', 'DDS', 'DDT', 'DE', 'DEA', 'DECA', 'DECK', 'DEI',
              'DELL', 'DEN', 'DENN', 'DEO', 'DERM', 'DESP', 'DFFN', 'DFH', 'DFIN', 'DFLI', 'DFLIW', 'DFP', 'DFS', 'DG',
              'DGHI', 'DGICA', 'DGICB', 'DGII', 'DGLY', 'DGX', 'DH', 'DHAC', 'DHACW', 'DHC', 'DHCA', 'DHCAW', 'DHCNI',
              'DHCNL', 'DHF', 'DHI', 'DHIL', 'DHR', 'DHT', 'DHX', 'DIAX', 'DIBS', 'DICE', 'DIN', 'DINO', 'DIOD', 'DIS',
              'DISA', 'DISAW', 'DISH', 'DIST', 'DISTR', 'DISTW', 'DJCO', 'DK', 'DKDCA', 'DKDCW', 'DKL', 'DKNG', 'DKS',
              'DLB', 'DLHC', 'DLNG', 'DLO', 'DLPN', 'DLR', 'DLTH', 'DLTR', 'DLX', 'DLY', 'DM', 'DMA', 'DMAC', 'DMAQ',
              'DMAQR', 'DMB', 'DMLP', 'DMO', 'DMRC', 'DMS', 'DMTK', 'DNA', 'DNB', 'DNLI', 'DNMR', 'DNOW', 'DNP',
              'DNUT', 'DO', 'DOC', 'DOCN', 'DOCS', 'DOCU', 'DOGZ', 'DOLE', 'DOMA', 'DOMH', 'DOMO', 'DOOO', 'DOOR',
              'DORM', 'DOUG', 'DOV', 'DOW', 'DOX', 'DOYU', 'DPCS', 'DPCSU', 'DPCSW', 'DPG', 'DPRO', 'DPZ', 'DQ',
              'DRCT', 'DRCTW', 'DRD', 'DRH', 'DRI', 'DRIO', 'DRMA', 'DRMAW', 'DRQ', 'DRRX', 'DRS', 'DRTS', 'DRTSW',
              'DRTT', 'DRUG', 'DRVN', 'DSAQ', 'DSGN', 'DSGR', 'DSGX', 'DSKE', 'DSL', 'DSM', 'DSP', 'DSU', 'DSWL',
              'DSX', 'DT', 'DTB', 'DTC', 'DTE', 'DTF', 'DTG', 'DTI', 'DTIL', 'DTM', 'DTOC', 'DTOCW', 'DTSS', 'DTST',
              'DTSTW', 'DTW', 'DUK', 'DUKB', 'DUNE', 'DUNEU', 'DUNEW', 'DUO', 'DUOL', 'DUOT', 'DV', 'DVA', 'DVAX',
              'DVN', 'DWAC', 'DWACU', 'DWACW', 'DWSN', 'DX', 'DXC', 'DXCM', 'DXLG', 'DXPE', 'DXR', 'DXYN', 'DY',
              'DYAI', 'DYN', 'DYNT', 'DZSI', 'E', 'EA', 'EAC', 'EACPU', 'EACPW', 'EAF', 'EAI', 'EAR', 'EARN', 'EAST',
              'EAT', 'EB', 'EBAY', 'EBC', 'EBET', 'EBF', 'EBIX', 'EBMT', 'EBON', 'EBR', 'EBS', 'EBTC', 'EC', 'ECAT',
              'ECBK', 'ECC', 'ECCC', 'ECCV', 'ECCW', 'ECCX', 'ECL', 'ECOR', 'ECPG', 'ECVT', 'ECX', 'ED', 'EDAP',
              'EDBL', 'EDBLW', 'EDD', 'EDF', 'EDI', 'EDIT', 'EDN', 'EDR', 'EDRY', 'EDSA', 'EDTK', 'EDU', 'EDUC', 'EE',
              'EEA', 'EEFT', 'EEIQ', 'EEX', 'EFC', 'EFHT', 'EFHTR', 'EFHTW', 'EFOI', 'EFR', 'EFSC', 'EFSCP', 'EFT',
              'EFTR', 'EFTRW', 'EFX', 'EFXT', 'EG', 'EGAN', 'EGBN', 'EGF', 'EGGF', 'EGHT', 'EGIO', 'EGLE', 'EGLX',
              'EGO', 'EGP', 'EGRX', 'EGY', 'EH', 'EHAB', 'EHC', 'EHI', 'EHTH', 'EIC', 'EICA', 'EIG', 'EIGR', 'EIX',
              'EJH', 'EKSO', 'EL', 'ELAN', 'ELBM', 'ELC', 'ELDN', 'ELEV', 'ELF', 'ELME', 'ELOX', 'ELP', 'ELS', 'ELSE',
              'ELTK', 'ELTX', 'ELV', 'ELVA', 'ELVN', 'ELWS', 'ELYM', 'ELYS', 'EM', 'EMBC', 'EMBK', 'EMBKW', 'EMCG',
              'EMCGR', 'EMCGU', 'EMCGW', 'EMD', 'EME', 'EMF', 'EMKR', 'EML', 'EMLD', 'EMLDU', 'EMLDW', 'EMN', 'EMO',
              'EMP', 'EMR', 'ENB', 'ENCP', 'ENCPU', 'ENCPW', 'ENER', 'ENERR', 'ENERU', 'ENERW', 'ENFN', 'ENG', 'ENIC',
              'ENJ', 'ENLC', 'ENLT', 'ENLV', 'ENO', 'ENOB', 'ENOV', 'ENPH', 'ENR', 'ENS', 'ENSC', 'ENSG', 'ENTA',
              'ENTG', 'ENTX', 'ENV', 'ENVA', 'ENVB', 'ENVX', 'ENZ', 'EOD', 'EOG', 'EOI', 'EOLS', 'EOS', 'EOSE',
              'EOSEW', 'EOT', 'EP', 'EPAC', 'EPAM', 'EPC', 'EPD', 'EPIX', 'EPOW', 'EPR', 'EPRT', 'EPSN', 'EQ', 'EQBK',
              'EQC', 'EQH', 'EQIX', 'EQNR', 'EQR', 'EQRX', 'EQRXW', 'EQS', 'EQT', 'ERAS', 'ERF', 'ERIC', 'ERIE',
              'ERII', 'ERJ', 'ERNA', 'ERO', 'ES', 'ESAB', 'ESAC', 'ESACU', 'ESACW', 'ESCA', 'ESE', 'ESEA', 'ESGR',
              'ESGRO', 'ESGRP', 'ESHA', 'ESHAR', 'ESI', 'ESLT', 'ESMT', 'ESNT', 'ESOA', 'ESPR', 'ESQ', 'ESRT', 'ESS',
              'ESSA', 'ESTA', 'ESTC', 'ESTE', 'ET', 'ETAO', 'ETB', 'ETD', 'ETG', 'ETI', 'ETJ', 'ETN', 'ETNB', 'ETO',
              'ETON', 'ETR', 'ETRN', 'ETSY', 'ETV', 'ETW', 'ETWO', 'ETX', 'ETY', 'EUDA', 'EUDAW', 'EURN', 'EVA',
              'EVAX', 'EVBG', 'EVC', 'EVCM', 'EVER', 'EVEX', 'EVF', 'EVG', 'EVGN', 'EVGO', 'EVGOW', 'EVGR', 'EVGRU',
              'EVGRW', 'EVH', 'EVLO', 'EVLV', 'EVLVW', 'EVN', 'EVO', 'EVOK', 'EVR', 'EVRG', 'EVRI', 'EVT', 'EVTC',
              'EVTL', 'EVTV', 'EW', 'EWBC', 'EWCZ', 'EWTX', 'EXAI', 'EXAS', 'EXC', 'EXEL', 'EXFY', 'EXG', 'EXK',
              'EXLS', 'EXP', 'EXPD', 'EXPE', 'EXPI', 'EXPO', 'EXPR', 'EXR', 'EXTR', 'EYE', 'EYEN', 'EYPT', 'EZFL',
              'EZGO', 'EZPW', 'F', 'FA', 'FAF', 'FAM', 'FAMI', 'FANG', 'FANH', 'FARM', 'FARO', 'FAST', 'FAT', 'FATBB',
              'FATBP', 'FATBW', 'FATE', 'FATH', 'FATP', 'FATPW', 'FAZE', 'FAZEW', 'FBIN', 'FBIO', 'FBIOP', 'FBIZ',
              'FBK', 'FBMS', 'FBNC', 'FBP', 'FBRT', 'FBRX', 'FC', 'FCAP', 'FCBC', 'FCCO', 'FCEL', 'FCF', 'FCFS', 'FCN',
              'FCNCA', 'FCNCO', 'FCNCP', 'FCPT', 'FCRX', 'FCT', 'FCUV', 'FCX', 'FDBC', 'FDEU', 'FDMT', 'FDP', 'FDUS',
              'FDX', 'FE', 'FEAM', 'FEDU', 'FEI', 'FEIM', 'FELE', 'FEMY', 'FENC', 'FENG', 'FERG', 'FET', 'FEXD',
              'FEXDR', 'FEXDU', 'FEXDW', 'FF', 'FFA', 'FFBC', 'FFC', 'FFIC', 'FFIE', 'FFIEW', 'FFIN', 'FFIV', 'FFNW',
              'FFWM', 'FG', 'FGB', 'FGBI', 'FGBIP', 'FGEN', 'FGF', 'FGFPP', 'FGI', 'FGMC', 'FGMCW', 'FHB', 'FHI',
              'FHLT', 'FHLTW', 'FHN', 'FHTX', 'FI', 'FIAC', 'FIBK', 'FICO', 'FICV', 'FICVW', 'FIF', 'FIGS', 'FIHL',
              'FINS', 'FINV', 'FINW', 'FIP', 'FIS', 'FISI', 'FITB', 'FITBI', 'FITBO', 'FITBP', 'FIVE', 'FIVN', 'FIX',
              'FIXX', 'FIZZ', 'FKWL', 'FL', 'FLC', 'FLEX', 'FLFV', 'FLFVR', 'FLFVW', 'FLGC', 'FLGT', 'FLIC', 'FLJ',
              'FLL', 'FLME', 'FLNC', 'FLNG', 'FLNT', 'FLO', 'FLR', 'FLS', 'FLT', 'FLUX', 'FLWS', 'FLXS', 'FLYW',
              'FMAO', 'FMBH', 'FMC', 'FMN', 'FMNB', 'FMS', 'FMX', 'FMY', 'FN', 'FNA', 'FNB', 'FNCB', 'FNCH', 'FND',
              'FNF', 'FNGR', 'FNKO', 'FNLC', 'FNV', 'FNVT', 'FNVTU', 'FNVTW', 'FNWB', 'FNWD', 'FOA', 'FOCS', 'FOF',
              'FOLD', 'FONR', 'FOR', 'FORA', 'FORD', 'FORG', 'FORL', 'FORLU', 'FORLW', 'FORM', 'FORR', 'FORTY', 'FOSL',
              'FOSLL', 'FOUR', 'FOX', 'FOXA', 'FOXF', 'FPAY', 'FPF', 'FPH', 'FPI', 'FPL', 'FR', 'FRA', 'FRAF', 'FRBA',
              'FRBK', 'FRBN', 'FRBNU', 'FREE', 'FREEW', 'FREQ', 'FRES', 'FREY', 'FRG', 'FRGAP', 'FRGE', 'FRGI', 'FRGT',
              'FRHC', 'FRLAW', 'FRLN', 'FRME', 'FRMEP', 'FRO', 'FROG', 'FRPH', 'FRPT', 'FRSH', 'FRST', 'FRSX', 'FRT',
              'FRTX', 'FRXB', 'FRZA', 'FSBC', 'FSBW', 'FSCO', 'FSD', 'FSEA', 'FSFG', 'FSK', 'FSLR', 'FSLY', 'FSM',
              'FSNB', 'FSR', 'FSRX', 'FSRXU', 'FSRXW', 'FSS', 'FSTR', 'FSV', 'FT', 'FTAI', 'FTAIM', 'FTAIN', 'FTAIO',
              'FTAIP', 'FTCH', 'FTCI', 'FTDR', 'FTEK', 'FTFT', 'FTHM', 'FTHY', 'FTI', 'FTII', 'FTIIU', 'FTIIW', 'FTK',
              'FTNT', 'FTRE', 'FTS', 'FTV', 'FUBO', 'FUL', 'FULC', 'FULT', 'FULTP', 'FUN', 'FUNC', 'FUND', 'FUSB',
              'FUSN', 'FUTU', 'FUV', 'FVCB', 'FVRR', 'FWAC', 'FWBI', 'FWONA', 'FWONK', 'FWRD', 'FWRG', 'FXCOR',
              'FXCOW', 'FXLV', 'FXNC', 'FYBR', 'FZT', 'G', 'GAB', 'GABC', 'GAIA', 'GAIN', 'GAINL', 'GAINN', 'GAINZ',
              'GALT', 'GAM', 'GAMB', 'GAMC', 'GAMCU', 'GAMCW', 'GAME', 'GAN', 'GANX', 'GAQ', 'GASS', 'GATE', 'GATEU',
              'GATEW', 'GATO', 'GATX', 'GB', 'GBAB', 'GBBK', 'GBBKR', 'GBCI', 'GBDC', 'GBIO', 'GBLI', 'GBNH', 'GBNY',
              'GBTG', 'GBX', 'GCBC', 'GCI', 'GCMG', 'GCMGW', 'GCO', 'GCT', 'GCTK', 'GCV', 'GD', 'GDC', 'GDDY', 'GDEN',
              'GDEV', 'GDEVW', 'GDHG', 'GDL', 'GDNR', 'GDNRW', 'GDO', 'GDOT', 'GDRX', 'GDS', 'GDST', 'GDSTR', 'GDSTW',
              'GDTC', 'GDV', 'GDYN', 'GE', 'GECC', 'GECCM', 'GECCN', 'GECCO', 'GEF', 'GEG', 'GEGGL', 'GEHC', 'GEHI',
              'GEL', 'GEN', 'GENE', 'GENI', 'GENK', 'GENQ', 'GENQU', 'GENQW', 'GEO', 'GEOS', 'GERN', 'GES', 'GETR',
              'GETY', 'GEVO', 'GF', 'GFAI', 'GFAIW', 'GFF', 'GFGD', 'GFGDR', 'GFGDU', 'GFGDW', 'GFI', 'GFL', 'GFOR',
              'GFS', 'GFX', 'GGAL', 'GGB', 'GGE', 'GGG', 'GGR', 'GGROW', 'GGT', 'GGZ', 'GH', 'GHC', 'GHG', 'GHI',
              'GHIX', 'GHIXW', 'GHL', 'GHLD', 'GHM', 'GHRS', 'GHSI', 'GHY', 'GIA', 'GIB', 'GIC', 'GIFI', 'GIGM',
              'GIII', 'GIL', 'GILD', 'GILT', 'GIM', 'GIPR', 'GIPRW', 'GIS', 'GJH', 'GJO', 'GJP', 'GJR', 'GJS', 'GJT',
              'GKOS', 'GL', 'GLAD', 'GLBE', 'GLBS', 'GLBZ', 'GLDD', 'GLG', 'GLLI', 'GLLIR', 'GLLIW', 'GLMD', 'GLNG',
              'GLOB', 'GLOG', 'GLOP', 'GLP', 'GLPG', 'GLPI', 'GLRE', 'GLSI', 'GLST', 'GLSTR', 'GLSTU', 'GLSTW', 'GLT',
              'GLTO', 'GLUE', 'GLW', 'GLYC', 'GM', 'GMAB', 'GMBL', 'GMBLP', 'GMBLW', 'GMBLZ', 'GMDA', 'GME', 'GMED',
              'GMFI', 'GMFIU', 'GMFIW', 'GMGI', 'GMRE', 'GMS', 'GMVD', 'GMVDW', 'GNE', 'GNFT', 'GNK', 'GNL', 'GNLN',
              'GNLX', 'GNPX', 'GNRC', 'GNSS', 'GNT', 'GNTA', 'GNTX', 'GNTY', 'GNW', 'GO', 'GOCO', 'GODN', 'GODNR',
              'GODNU', 'GOEV', 'GOEVW', 'GOF', 'GOGL', 'GOGO', 'GOL', 'GOLD', 'GOLF', 'GOOD', 'GOODN', 'GOODO', 'GOOG',
              'GOOS', 'GOSS', 'GOTU', 'GOVX', 'GOVXW', 'GP', 'GPAC', 'GPACU', 'GPACW', 'GPC', 'GPCR', 'GPI', 'GPJA',
              'GPK', 'GPMT', 'GPN', 'GPOR', 'GPP', 'GPRE', 'GPRK', 'GPRO', 'GPS', 'GRAB', 'GRABW', 'GRBK', 'GRC',
              'GRCL', 'GREE', 'GREEL', 'GRFS', 'GRI', 'GRIL', 'GRIN', 'GRMN', 'GRND', 'GRNQ', 'GRNT', 'GROM', 'GROMW',
              'GROV', 'GROW', 'GRPH', 'GRPN', 'GRRR', 'GRRRW', 'GRTS', 'GRTX', 'GRVY', 'GRWG', 'GRX', 'GS', 'GSBC',
              'GSBD', 'GSD', 'GSDWU', 'GSDWW', 'GSHD', 'GSIT', 'GSK', 'GSL', 'GSM', 'GSMG', 'GSMGW', 'GSUN', 'GT',
              'GTBP', 'GTEC', 'GTES', 'GTH', 'GTHX', 'GTIM', 'GTLB', 'GTLS', 'GTN', 'GTX', 'GTY', 'GUG', 'GURE', 'GUT',
              'GVA', 'GVP', 'GWAV', 'GWH', 'GWRE', 'GWRS', 'GWW', 'GXO', 'GYRO', 'H', 'HA', 'HAE', 'HAFC', 'HAIA',
              'HAIAU', 'HAIAW', 'HAIN', 'HAL', 'HALL', 'HALO', 'HARP', 'HAS', 'HASI', 'HAYN', 'HAYW', 'HBAN', 'HBANL',
              'HBANM', 'HBANP', 'HBB', 'HBCP', 'HBI', 'HBIO', 'HBM', 'HBNC', 'HBT', 'HCA', 'HCAT', 'HCC', 'HCCI',
              'HCDI', 'HCDIP', 'HCDIW', 'HCDIZ', 'HCI', 'HCKT', 'HCM', 'HCMA', 'HCMAW', 'HCP', 'HCSG', 'HCTI', 'HCVI',
              'HCVIU', 'HCVIW', 'HCWB', 'HCXY', 'HD', 'HDB', 'HDSN', 'HE', 'HEAR', 'HEES', 'HEI', 'HELE', 'HEP',
              'HEPA', 'HEPS', 'HEQ', 'HES', 'HESM', 'HFBL', 'HFFG', 'HFRO', 'HFWA', 'HGBL', 'HGEN', 'HGLB', 'HGTY',
              'HGV', 'HHC', 'HHGC', 'HHGCR', 'HHGCU', 'HHGCW', 'HHLA', 'HHRS', 'HHRSW', 'HHS', 'HI', 'HIBB', 'HIE',
              'HIFS', 'HIG', 'HIHO', 'HII', 'HILS', 'HIMS', 'HIMX', 'HIO', 'HIPO', 'HITI', 'HIVE', 'HIW', 'HIX', 'HKD',
              'HKIT', 'HL', 'HLF', 'HLGN', 'HLI', 'HLIO', 'HLIT', 'HLLY', 'HLMN', 'HLN', 'HLNE', 'HLP', 'HLT', 'HLTH',
              'HLVX', 'HLX', 'HMA', 'HMAC', 'HMACR', 'HMACW', 'HMC', 'HMN', 'HMNF', 'HMPT', 'HMST', 'HMY', 'HNI',
              'HNNA', 'HNNAZ', 'HNRG', 'HNST', 'HNVR', 'HOFT', 'HOFV', 'HOFVW', 'HOG', 'HOLI', 'HOLO', 'HOLOW', 'HOLX',
              'HOMB', 'HON', 'HONE', 'HOOD', 'HOOK', 'HOPE', 'HOTH', 'HOUR', 'HOUS', 'HOV', 'HOVNP', 'HOWL', 'HP',
              'HPCO', 'HPE', 'HPF', 'HPI', 'HPK', 'HPKEW', 'HPLT', 'HPLTW', 'HPP', 'HPQ', 'HPS', 'HQH', 'HQI', 'HQL',
              'HQY', 'HR', 'HRB', 'HRI', 'HRL', 'HRMY', 'HROW', 'HROWL', 'HROWM', 'HRT', 'HRTG', 'HRTX', 'HRZN',
              'HSAI', 'HSBC', 'HSCS', 'HSCSW', 'HSDT', 'HSHP', 'HSIC', 'HSII', 'HSON', 'HSPO', 'HSPOR', 'HSPOW', 'HST',
              'HSTM', 'HSTO', 'HSY', 'HT', 'HTBI', 'HTBK', 'HTCR', 'HTD', 'HTFB', 'HTFC', 'HTGC', 'HTH', 'HTHT',
              'HTIA', 'HTIBP', 'HTLD', 'HTLF', 'HTLFP', 'HTOO', 'HTOOW', 'HTY', 'HTZ', 'HTZWW', 'HUBB', 'HUBC',
              'HUBCW', 'HUBCZ', 'HUBG', 'HUBS', 'HUDA', 'HUDAR', 'HUDI', 'HUGE', 'HUIZ', 'HUM', 'HUMA', 'HUMAW', 'HUN',
              'HURC', 'HURN', 'HUT', 'HUYA', 'HVT', 'HWBK', 'HWC', 'HWCPZ', 'HWEL', 'HWELW', 'HWKN', 'HWM', 'HXL',
              'HY', 'HYB', 'HYFM', 'HYI', 'HYLN', 'HYMC', 'HYMCL', 'HYMCW', 'HYPR', 'HYT', 'HYW', 'HYZN', 'HYZNW',
              'HZNP', 'HZO', 'I', 'IAC', 'IAE', 'IAG', 'IART', 'IAS', 'IBCP', 'IBEX', 'IBKR', 'IBM', 'IBN', 'IBOC',
              'IBP', 'IBRX', 'IBTX', 'ICAD', 'ICCC', 'ICCH', 'ICCM', 'ICD', 'ICE', 'ICFI', 'ICG', 'ICHR', 'ICL',
              'ICLK', 'ICLR', 'ICMB', 'ICNC', 'ICPT', 'ICR', 'ICU', 'ICUCW', 'ICUI', 'ICVX', 'IDA', 'IDAI', 'IDBA',
              'IDCC', 'IDE', 'IDEX', 'IDN', 'IDT', 'IDXX', 'IDYA', 'IEP', 'IESC', 'IEX', 'IFBD', 'IFF', 'IFIN', 'IFN',
              'IFRX', 'IFS', 'IGA', 'IGD', 'IGI', 'IGIC', 'IGICW', 'IGMS', 'IGR', 'IGT', 'IGTA', 'IGTAR', 'IGTAW',
              'IH', 'IHD', 'IHG', 'IHIT', 'IHRT', 'IHS', 'IHTA', 'IIF', 'III', 'IIIN', 'IIIV', 'IIM', 'IINN', 'IINNW',
              'IIPR', 'IKNA', 'IKT', 'ILAG', 'ILLM', 'ILMN', 'ILPT', 'IMAB', 'IMACW', 'IMAQ', 'IMAQR', 'IMAQU',
              'IMAQW', 'IMAX', 'IMCC', 'IMCR', 'IMGN', 'IMKTA', 'IMMP', 'IMMR', 'IMMX', 'IMNM', 'IMNN', 'IMOS', 'IMPL',
              'IMPP', 'IMPPP', 'IMRN', 'IMRX', 'IMTE', 'IMTX', 'IMTXW', 'IMUX', 'IMVT', 'IMXI', 'INAB', 'INAQ',
              'INAQW', 'INBK', 'INBKZ', 'INBS', 'INBX', 'INCR', 'INCY', 'INDB', 'INDI', 'INDIW', 'INDP', 'INDV',
              'INFA', 'INFI', 'INFN', 'INFY', 'ING', 'INGN', 'INGR', 'INKT', 'INM', 'INMB', 'INMD', 'INN', 'INNV',
              'INO', 'INOD', 'INPX', 'INSE', 'INSG', 'INSI', 'INSM', 'INSP', 'INST', 'INSW', 'INTA', 'INTC', 'INTE',
              'INTEU', 'INTEW', 'INTG', 'INTR', 'INTS', 'INTU', 'INTZ', 'INVA', 'INVE', 'INVH', 'INVO', 'INVZ',
              'INVZW', 'INZY', 'IOAC', 'IOACU', 'IOACW', 'IOBT', 'IONM', 'IONQ', 'IONR', 'IONS', 'IOSP', 'IOT', 'IOVA',
              'IP', 'IPA', 'IPAR', 'IPDN', 'IPG', 'IPGP', 'IPHA', 'IPI', 'IPSC', 'IPW', 'IPWR', 'IPX', 'IPXX', 'IPXXU',
              'IPXXW', 'IQ', 'IQI', 'IQV', 'IR', 'IRAA', 'IRAAW', 'IRBT', 'IRDM', 'IREN', 'IRIX', 'IRM', 'IRMD',
              'IRNT', 'IRON', 'IROQ', 'IRRX', 'IRS', 'IRT', 'IRTC', 'IRWD', 'ISD', 'ISIG', 'ISPC', 'ISPO', 'ISPOW',
              'ISPR', 'ISRG', 'ISRL', 'ISRLU', 'ISRLW', 'ISSC', 'ISTR', 'ISUN', 'IT', 'ITAQ', 'ITAQW', 'ITCI', 'ITCL',
              'ITGR', 'ITI', 'ITIC', 'ITOS', 'ITRI', 'ITRM', 'ITRN', 'ITT', 'ITUB', 'ITW', 'IVA', 'IVAC', 'IVCA',
              'IVCAU', 'IVCAW', 'IVCB', 'IVCBW', 'IVCP', 'IVCPW', 'IVDA', 'IVDAW', 'IVR', 'IVT', 'IVVD', 'IVZ', 'IX',
              'IXAQ', 'IXAQU', 'IXAQW', 'IXHL', 'IZEA', 'IZM', 'J', 'JACK', 'JAGX', 'JAKK', 'JAMF', 'JAN', 'JANX',
              'JAQC', 'JAQCW', 'JAZZ', 'JBGS', 'JBHT', 'JBI', 'JBK', 'JBL', 'JBLU', 'JBSS', 'JBT', 'JCE', 'JCI',
              'JCSE', 'JCTCF', 'JD', 'JEF', 'JELD', 'JEQ', 'JEWL', 'JFBR', 'JFBRW', 'JFIN', 'JFR', 'JFU', 'JG', 'JGGC',
              'JGGCR', 'JGGCW', 'JGH', 'JHAA', 'JHG', 'JHI', 'JHS', 'JHX', 'JILL', 'JJSF', 'JKHY', 'JKS', 'JLL', 'JLS',
              'JMIA', 'JMM', 'JMSB', 'JNJ', 'JNPR', 'JNVR', 'JOAN', 'JOBY', 'JOE', 'JOF', 'JOUT', 'JPC', 'JPI', 'JPM',
              'JPS', 'JPT', 'JQC', 'JRI', 'JRO', 'JRS', 'JRSH', 'JRVR', 'JSD', 'JSM', 'JSPR', 'JSPRW', 'JT', 'JUN',
              'JUPW', 'JUPWW', 'JVA', 'JWEL', 'JWN', 'JXJT', 'JXN', 'JYD', 'JYNT', 'JZ', 'JZXN', 'K', 'KA', 'KACL',
              'KACLR', 'KACLW', 'KAI', 'KALA', 'KALU', 'KALV', 'KAMN', 'KAR', 'KARO', 'KAVL', 'KB', 'KBH', 'KBNT',
              'KBNTW', 'KBR', 'KC', 'KCGI', 'KD', 'KDNY', 'KDP', 'KE', 'KELYA', 'KELYB', 'KEN', 'KEP', 'KEQU', 'KERN',
              'KERNW', 'KEX', 'KEY', 'KEYS', 'KF', 'KFFB', 'KFRC', 'KFS', 'KFY', 'KGC', 'KGS', 'KHC', 'KIDS', 'KIM',
              'KIND', 'KINS', 'KIO', 'KIRK', 'KITT', 'KITTW', 'KKR', 'KKRS', 'KLAC', 'KLIC', 'KLR', 'KLTR', 'KLXE',
              'KMB', 'KMDA', 'KMF', 'KMI', 'KMPB', 'KMPR', 'KMT', 'KMX', 'KN', 'KNDI', 'KNF', 'KNOP', 'KNSA', 'KNSL',
              'KNSW', 'KNTE', 'KNTK', 'KNX', 'KO', 'KOD', 'KODK', 'KOF', 'KOP', 'KOPN', 'KORE', 'KOS', 'KOSS', 'KPLT',
              'KPLTW', 'KPRX', 'KPTI', 'KR', 'KRBP', 'KRC', 'KREF', 'KRG', 'KRKR', 'KRMD', 'KRNL', 'KRNLU', 'KRNLW',
              'KRNT', 'KRNY', 'KRO', 'KRON', 'KROS', 'KRP', 'KRT', 'KRTX', 'KRUS', 'KRYS', 'KSCP', 'KSM', 'KSS', 'KT',
              'KTB', 'KTCC', 'KTF', 'KTH', 'KTN', 'KTOS', 'KTRA', 'KTTA', 'KTTAW', 'KUKE', 'KURA', 'KVACU', 'KVHI',
              'KVSA', 'KVUE', 'KW', 'KWE', 'KWESW', 'KWR', 'KXIN', 'KYCH', 'KYCHR', 'KYCHW', 'KYMR', 'KYN', 'KZIA',
              'KZR', 'L', 'LAB', 'LABP', 'LAC', 'LAD', 'LADR', 'LAES', 'LAKE', 'LAMR', 'LANC', 'LAND', 'LANDM',
              'LANDO', 'LANDP', 'LANV', 'LARK', 'LASE', 'LASR', 'LATGU', 'LAUR', 'LAW', 'LAZ', 'LAZR', 'LAZY', 'LBAI',
              'LBBB', 'LBC', 'LBPH', 'LBRDA', 'LBRDK', 'LBRDP', 'LBRT', 'LBTYA', 'LBTYB', 'LBTYK', 'LC', 'LCA', 'LCAA',
              'LCAAW', 'LCAHU', 'LCAHW', 'LCFY', 'LCFYW', 'LCID', 'LCII', 'LCNB', 'LCUT', 'LCW', 'LDI', 'LDOS', 'LDP',
              'LE', 'LEA', 'LECO', 'LEDS', 'LEE', 'LEG', 'LEGH', 'LEGN', 'LEJU', 'LEN', 'LEO', 'LESL', 'LEV', 'LEVI',
              'LEXX', 'LEXXW', 'LFACU', 'LFACW', 'LFCR', 'LFLY', 'LFLYW', 'LFMD', 'LFMDP', 'LFST', 'LFT', 'LFUS',
              'LFVN', 'LGHL', 'LGHLW', 'LGI', 'LGIH', 'LGMK', 'LGND', 'LGO', 'LGST', 'LGSTU', 'LGSTW', 'LGVC', 'LGVCW',
              'LGVN', 'LH', 'LHC', 'LHX', 'LI', 'LIAN', 'LIBY', 'LIBYW', 'LICN', 'LICY', 'LIDR', 'LIDRW', 'LIFE',
              'LIFW', 'LIFWW', 'LIFWZ', 'LII', 'LILA', 'LILAK', 'LILM', 'LILMW', 'LIN', 'LINC', 'LIND', 'LINK', 'LIPO',
              'LIQT', 'LITB', 'LITE', 'LITM', 'LIVB', 'LIVBU', 'LIVBW', 'LIVE', 'LIVN', 'LIXT', 'LIXTW', 'LIZI',
              'LKCO', 'LKFN', 'LKQ', 'LL', 'LLAP', 'LLY', 'LMAT', 'LMB', 'LMDX', 'LMDXW', 'LMFA', 'LMND', 'LMNL',
              'LMNR', 'LMT', 'LNC', 'LND', 'LNKB', 'LNN', 'LNSR', 'LNT', 'LNTH', 'LNW', 'LNZA', 'LNZAW', 'LOAN', 'LOB',
              'LOCC', 'LOCL', 'LOCO', 'LOGI', 'LOMA', 'LOOP', 'LOPE', 'LOV', 'LOVE', 'LOW', 'LPCN', 'LPG', 'LPL',
              'LPLA', 'LPRO', 'LPSN', 'LPTH', 'LPTX', 'LPX', 'LQDA', 'LQDT', 'LRCX', 'LRFC', 'LRMR', 'LRN', 'LSAK',
              'LSBK', 'LSCC', 'LSDI', 'LSEA', 'LSEAW', 'LSPD', 'LSTA', 'LSTR', 'LSXMA', 'LSXMB', 'LSXMK', 'LTBR',
              'LTC', 'LTCH', 'LTCHW', 'LTH', 'LTHM', 'LTRN', 'LTRPA', 'LTRPB', 'LTRX', 'LTRY', 'LTRYW', 'LU', 'LUCD',
              'LUCY', 'LUCYW', 'LULU', 'LUMN', 'LUMO', 'LUNA', 'LUNG', 'LUNR', 'LUNRW', 'LUV', 'LUXH', 'LVLU', 'LVO',
              'LVOX', 'LVOXW', 'LVRO', 'LVROW', 'LVS', 'LVTX', 'LVWR', 'LW', 'LWAY', 'LWLG', 'LX', 'LXEH', 'LXP',
              'LXRX', 'LXU', 'LYB', 'LYEL', 'LYFT', 'LYG', 'LYRA', 'LYT', 'LYTS', 'LYV', 'LZ', 'LZB', 'LZM', 'M', 'MA',
              'MAA', 'MAC', 'MACA', 'MACAW', 'MACK', 'MAIN', 'MAN', 'MANH', 'MANU', 'MAPS', 'MAPSW', 'MAQC', 'MAQCU',
              'MAQCW', 'MAR', 'MARA', 'MARK', 'MARPS', 'MARX', 'MAS', 'MASI', 'MASS', 'MAT', 'MATH', 'MATV', 'MATW',
              'MATX', 'MAV', 'MAX', 'MAXN', 'MAYS', 'MBAC', 'MBC', 'MBCN', 'MBI', 'MBIN', 'MBINM', 'MBINN', 'MBINO',
              'MBINP', 'MBIO', 'MBLY', 'MBNKP', 'MBOT', 'MBRX', 'MBSC', 'MBTC', 'MBUU', 'MBWM', 'MC', 'MCAA', 'MCAAW',
              'MCAC', 'MCACR', 'MCAF', 'MCAG', 'MCB', 'MCBC', 'MCBS', 'MCD', 'MCFT', 'MCHP', 'MCHX', 'MCI', 'MCK',
              'MCLD', 'MCLDW', 'MCN', 'MCO', 'MCOM', 'MCOMW', 'MCR', 'MCRB', 'MCRI', 'MCS', 'MCVT', 'MCW', 'MCY', 'MD',
              'MDB', 'MDC', 'MDGL', 'MDGS', 'MDIA', 'MDJH', 'MDLZ', 'MDNA', 'MDRR', 'MDRRP', 'MDRX', 'MDT', 'MDU',
              'MDV', 'MDVL', 'MDWD', 'MDWT', 'MDXG', 'MDXH', 'ME', 'MEC', 'MED', 'MEDP', 'MEDS', 'MEG', 'MEGI', 'MEGL',
              'MEI', 'MEIP', 'MELI', 'MEOH', 'MER', 'MERC', 'MESA', 'MESO', 'MET', 'META', 'METC', 'METCB', 'METCL',
              'METX', 'METXW', 'MF', 'MFA', 'MFC', 'MFD', 'MFG', 'MFH', 'MFIC', 'MFIN', 'MFM', 'MFV', 'MG', 'MGA',
              'MGAM', 'MGEE', 'MGF', 'MGIC', 'MGIH', 'MGM', 'MGNI', 'MGNX', 'MGOL', 'MGPI', 'MGR', 'MGRB', 'MGRC',
              'MGRD', 'MGRM', 'MGRX', 'MGTA', 'MGTX', 'MGY', 'MGYR', 'MHD', 'MHF', 'MHI', 'MHK', 'MHLA', 'MHLD', 'MHN',
              'MHNC', 'MHO', 'MHUA', 'MICS', 'MIDD', 'MIGI', 'MIN', 'MIND', 'MINDP', 'MINM', 'MIO', 'MIR', 'MIRM',
              'MIRO', 'MIST', 'MITA', 'MITAU', 'MITAW', 'MITK', 'MITT', 'MIXT', 'MIY', 'MKC', 'MKFG', 'MKL', 'MKSI',
              'MKTW', 'MKTX', 'MKUL', 'ML', 'MLAB', 'MLCO', 'MLEC', 'MLECW', 'MLGO', 'MLI', 'MLKN', 'MLM', 'MLNK',
              'MLP', 'MLR', 'MLTX', 'MLYS', 'MMAT', 'MMC', 'MMD', 'MMI', 'MMLP', 'MMM', 'MMMB', 'MMP', 'MMS', 'MMSI',
              'MMT', 'MMU', 'MMV', 'MMVWW', 'MMYT', 'MNDO', 'MNDY', 'MNKD', 'MNMD', 'MNOV', 'MNP', 'MNPR', 'MNRO',
              'MNSB', 'MNSBP', 'MNSO', 'MNST', 'MNTK', 'MNTN', 'MNTS', 'MNTSW', 'MNTX', 'MO', 'MOB', 'MOBBW', 'MOBQ',
              'MOBQW', 'MOBV', 'MOBVU', 'MOD', 'MODD', 'MODG', 'MODN', 'MODV', 'MOFG', 'MOGO', 'MOGU', 'MOH', 'MOLN',
              'MOMO', 'MOND', 'MOR', 'MORF', 'MORN', 'MOS', 'MOTS', 'MOV', 'MOVE', 'MOXC', 'MP', 'MPA', 'MPAA', 'MPB',
              'MPC', 'MPLN', 'MPLX', 'MPV', 'MPW', 'MPWR', 'MPX', 'MQ', 'MQT', 'MQY', 'MRAI', 'MRAM', 'MRBK', 'MRC',
              'MRCC', 'MRCY', 'MRDB', 'MREO', 'MRIN', 'MRK', 'MRKR', 'MRM', 'MRNA', 'MRNS', 'MRO', 'MRSN', 'MRTN',
              'MRTX', 'MRUS', 'MRVI', 'MRVL', 'MS', 'MSA', 'MSB', 'MSBI', 'MSBIP', 'MSC', 'MSCI', 'MSD', 'MSEX',
              'MSFT', 'MSGE', 'MSGM', 'MSGS', 'MSI', 'MSM', 'MSSA', 'MSSAU', 'MSSAW', 'MSTR', 'MSVB', 'MT', 'MTAC',
              'MTACU', 'MTACW', 'MTAL', 'MTB', 'MTBL', 'MTC', 'MTCH', 'MTD', 'MTDR', 'MTEK', 'MTEKW', 'MTEM', 'MTEX',
              'MTG', 'MTH', 'MTLS', 'MTN', 'MTR', 'MTRN', 'MTRX', 'MTRY', 'MTRYW', 'MTSI', 'MTTR', 'MTW', 'MTX', 'MTZ',
              'MU', 'MUA', 'MUC', 'MUE', 'MUFG', 'MUI', 'MUJ', 'MULN', 'MUR', 'MURF', 'MURFU', 'MURFW', 'MUSA', 'MUX',
              'MVBF', 'MVF', 'MVIS', 'MVLA', 'MVLAW', 'MVO', 'MVST', 'MVSTW', 'MVT', 'MWA', 'MX', 'MXCT', 'MXE', 'MXF',
              'MXL', 'MYD', 'MYE', 'MYFW', 'MYGN', 'MYI', 'MYMD', 'MYN', 'MYNA', 'MYNZ', 'MYPS', 'MYPSW', 'MYRG',
              'MYSZ', 'MYTE', 'N', 'NA', 'NAAS', 'NABL', 'NAC', 'NAD', 'NAII', 'NAMS', 'NAMSW', 'NAN', 'NAOV', 'NAPA',
              'NARI', 'NAT', 'NATH', 'NATI', 'NATR', 'NAUT', 'NAVI', 'NAZ', 'NB', 'NBB', 'NBHC', 'NBIX', 'NBN', 'NBR',
              'NBRV', 'NBSE', 'NBST', 'NBSTU', 'NBSTW', 'NBTB', 'NBTX', 'NBXG', 'NC', 'NCA', 'NCAC', 'NCACU', 'NCACW',
              'NCLH', 'NCMI', 'NCNA', 'NCNO', 'NCPL', 'NCPLW', 'NCR', 'NCRA', 'NCSM', 'NCTY', 'NCV', 'NCZ', 'NDAQ',
              'NDLS', 'NDMO', 'NDP', 'NDRA', 'NDSN', 'NE', 'NEA', 'NECB', 'NEE', 'NEGG', 'NEM', 'NEO', 'NEOG', 'NEON',
              'NEOV', 'NEOVW', 'NEP', 'NEPH', 'NEPT', 'NERV', 'NET', 'NETC', 'NETDU', 'NETI', 'NEU', 'NEWR', 'NEWT',
              'NEWTL', 'NEWTZ', 'NEX', 'NEXA', 'NEXI', 'NEXT', 'NFBK', 'NFE', 'NFG', 'NFJ', 'NFLX', 'NFNT', 'NFTG',
              'NFYS', 'NGG', 'NGL', 'NGM', 'NGMS', 'NGS', 'NGVC', 'NGVT', 'NHI', 'NHTC', 'NI', 'NIC', 'NICE', 'NICK',
              'NIE', 'NIM', 'NIMC', 'NINE', 'NIO', 'NIOBW', 'NIR', 'NIRWW', 'NISN', 'NIU', 'NJR', 'NKE', 'NKLA',
              'NKSH', 'NKTR', 'NKTX', 'NKX', 'NL', 'NLS', 'NLSP', 'NLSPW', 'NLTX', 'NLY', 'NM', 'NMAI', 'NMCO', 'NMFC',
              'NMG', 'NMI', 'NMIH', 'NMK', 'NMM', 'NMR', 'NMRD', 'NMRK', 'NMS', 'NMT', 'NMTC', 'NMTR', 'NMZ', 'NN',
              'NNAVW', 'NNBR', 'NNDM', 'NNI', 'NNN', 'NNOX', 'NNY', 'NOA', 'NOAH', 'NOC', 'NODK', 'NOG', 'NOGN',
              'NOGNW', 'NOK', 'NOM', 'NOMD', 'NOTE', 'NOTV', 'NOV', 'NOVA', 'NOVN', 'NOVT', 'NOVV', 'NOVVR', 'NOW',
              'NPAB', 'NPABW', 'NPCE', 'NPCT', 'NPFD', 'NPK', 'NPO', 'NPV', 'NPWR', 'NQP', 'NR', 'NRAC', 'NRACU',
              'NRACW', 'NRBO', 'NRC', 'NRDS', 'NRDY', 'NREF', 'NRG', 'NRGV', 'NRGX', 'NRIM', 'NRIX', 'NRK', 'NRP',
              'NRSN', 'NRSNW', 'NRT', 'NRUC', 'NRXP', 'NRXPW', 'NS', 'NSA', 'NSC', 'NSIT', 'NSL', 'NSP', 'NSPR', 'NSS',
              'NSSC', 'NSTC', 'NSTG', 'NSTS', 'NSYS', 'NTAP', 'NTB', 'NTCO', 'NTCT', 'NTES', 'NTG', 'NTGR', 'NTIC',
              'NTLA', 'NTNX', 'NTR', 'NTRA', 'NTRB', 'NTRBW', 'NTRS', 'NTRSO', 'NTST', 'NTWK', 'NTZ', 'NU', 'NUBI',
              'NUBIW', 'NUE', 'NURO', 'NUS', 'NUTX', 'NUV', 'NUVA', 'NUVB', 'NUVL', 'NUW', 'NUWE', 'NUZE', 'NVAC',
              'NVACR', 'NVACW', 'NVAX', 'NVCR', 'NVCT', 'NVDA', 'NVEC', 'NVEE', 'NVEI', 'NVFY', 'NVG', 'NVGS', 'NVIV',
              'NVMI', 'NVNO', 'NVO', 'NVOS', 'NVR', 'NVRI', 'NVRO', 'NVS', 'NVST', 'NVT', 'NVTA', 'NVTS', 'NVVE',
              'NVVEW', 'NVX', 'NWBI', 'NWE', 'NWFL', 'NWG', 'NWL', 'NWLI', 'NWN', 'NWPX', 'NWS', 'NWSA', 'NWTN',
              'NWTNW', 'NX', 'NXC', 'NXDT', 'NXE', 'NXG', 'NXGL', 'NXGLW', 'NXGN', 'NXJ', 'NXL', 'NXLIW', 'NXN', 'NXP',
              'NXPI', 'NXPL', 'NXPLW', 'NXRT', 'NXST', 'NXT', 'NXTC', 'NXTP', 'NXU', 'NYAX', 'NYC', 'NYCB', 'NYMT',
              'NYMTL', 'NYMTM', 'NYMTN', 'NYMTZ', 'NYT', 'NYXH', 'NZF', 'O', 'OABI', 'OABIW', 'OAK', 'OAKU', 'OAKUU',
              'OAKUW', 'OB', 'OBDC', 'OBIO', 'OBK', 'OBLG', 'OBT', 'OC', 'OCAX', 'OCC', 'OCCI', 'OCCIN', 'OCCIO',
              'OCEA', 'OCEAW', 'OCFC', 'OCFCP', 'OCFT', 'OCG', 'OCGN', 'OCN', 'OCS', 'OCSAW', 'OCSL', 'OCTO', 'OCUL',
              'OCUP', 'OCX', 'ODC', 'ODD', 'ODFL', 'ODP', 'ODV', 'ODVWW', 'OEC', 'OESX', 'OFC', 'OFED', 'OFG', 'OFIX',
              'OFLX', 'OFS', 'OFSSH', 'OGE', 'OGI', 'OGN', 'OGS', 'OHI', 'OI', 'OIA', 'OIG', 'OII', 'OIS', 'OKE',
              'OKTA', 'OKYO', 'OLB', 'OLED', 'OLIT', 'OLITU', 'OLITW', 'OLK', 'OLLI', 'OLMA', 'OLN', 'OLO', 'OLP',
              'OLPX', 'OM', 'OMAB', 'OMC', 'OMCL', 'OMER', 'OMEX', 'OMF', 'OMGA', 'OMH', 'OMI', 'OMIC', 'OMQS', 'ON',
              'ONB', 'ONBPO', 'ONBPP', 'ONCT', 'ONCY', 'ONDS', 'ONEW', 'ONFO', 'ONFOW', 'ONL', 'ONON', 'ONTF', 'ONTO',
              'ONTX', 'ONVO', 'ONYX', 'ONYXW', 'OOMA', 'OP', 'OPA', 'OPAD', 'OPAL', 'OPBK', 'OPCH', 'OPEN', 'OPFI',
              'OPGN', 'OPHC', 'OPI', 'OPINL', 'OPK', 'OPOF', 'OPP', 'OPRA', 'OPRT', 'OPRX', 'OPT', 'OPTN', 'OPXS',
              'OPY', 'OR', 'ORA', 'ORAN', 'ORC', 'ORCL', 'ORGN', 'ORGNW', 'ORGO', 'ORGS', 'ORI', 'ORIC', 'ORLY',
              'ORMP', 'ORN', 'ORRF', 'ORTX', 'OSA', 'OSAAW', 'OSBC', 'OSCR', 'OSG', 'OSI', 'OSIS', 'OSK', 'OSPN',
              'OSS', 'OST', 'OSTK', 'OSUR', 'OSW', 'OTEC', 'OTECU', 'OTEX', 'OTIS', 'OTLK', 'OTLY', 'OTMO', 'OTMOW',
              'OTRK', 'OTRKP', 'OTTR', 'OUST', 'OUT', 'OVBC', 'OVID', 'OVLY', 'OVV', 'OWL', 'OWLT', 'OXAC', 'OXACW',
              'OXBR', 'OXBRW', 'OXLC', 'OXLCL', 'OXLCM', 'OXLCN', 'OXLCO', 'OXLCP', 'OXLCZ', 'OXM', 'OXSQ', 'OXSQG',
              'OXSQL', 'OXSQZ', 'OXUS', 'OXUSU', 'OXUSW', 'OXY', 'OZK', 'OZKAP', 'P', 'PAA', 'PAAS', 'PAC', 'PACB',
              'PACK', 'PACW', 'PACWP', 'PAG', 'PAGP', 'PAGS', 'PAHC', 'PAI', 'PALI', 'PALT', 'PAM', 'PANL', 'PANW',
              'PAR', 'PARA', 'PARAA', 'PARAP', 'PARR', 'PASG', 'PATH', 'PATI', 'PATK', 'PAVM', 'PAVS', 'PAX', 'PAXS',
              'PAY', 'PAYC', 'PAYO', 'PAYOW', 'PAYS', 'PAYX', 'PB', 'PBA', 'PBAX', 'PBAXU', 'PBAXW', 'PBBK', 'PBF',
              'PBFS', 'PBH', 'PBHC', 'PBI', 'PBLA', 'PBPB', 'PBR', 'PBT', 'PBTS', 'PBYI', 'PCAR', 'PCB', 'PCCT',
              'PCCTW', 'PCF', 'PCG', 'PCGU', 'PCH', 'PCK', 'PCM', 'PCN', 'PCOR', 'PCQ', 'PCRX', 'PCSA', 'PCT', 'PCTI',
              'PCTTU', 'PCTTW', 'PCTY', 'PCVX', 'PCYG', 'PCYO', 'PD', 'PDCE', 'PDCO', 'PDD', 'PDEX', 'PDFS', 'PDI',
              'PDLB', 'PDM', 'PDO', 'PDS', 'PDSB', 'PDT', 'PEAK', 'PEB', 'PEBK', 'PEBO', 'PECO', 'PEG', 'PEGA', 'PEGR',
              'PEGRU', 'PEGRW', 'PEGY', 'PEN', 'PENN', 'PEO', 'PEP', 'PEPG', 'PEPL', 'PEPLW', 'PERF', 'PERI', 'PESI',
              'PET', 'PETQ', 'PETS', 'PETV', 'PETVW', 'PETWW', 'PETZ', 'PEV', 'PFBC', 'PFC', 'PFD', 'PFE', 'PFG',
              'PFGC', 'PFH', 'PFIE', 'PFIN', 'PFIS', 'PFL', 'PFLT', 'PFMT', 'PFN', 'PFO', 'PFS', 'PFSI', 'PFSW',
              'PFTA', 'PFTAU', 'PFTAW', 'PFX', 'PFXNZ', 'PG', 'PGC', 'PGEN', 'PGNY', 'PGP', 'PGR', 'PGRE', 'PGRU',
              'PGSS', 'PGTI', 'PGY', 'PGYWW', 'PGZ', 'PH', 'PHAR', 'PHAT', 'PHD', 'PHG', 'PHI', 'PHIN', 'PHIO', 'PHK',
              'PHM', 'PHR', 'PHT', 'PHUN', 'PHUNW', 'PHVS', 'PHX', 'PHXM', 'PHYT', 'PI', 'PIAI', 'PII', 'PIII',
              'PIIIW', 'PIK', 'PIM', 'PINC', 'PINE', 'PINS', 'PIPR', 'PIRS', 'PIXY', 'PJT', 'PK', 'PKBK', 'PKE', 'PKG',
              'PKOH', 'PKST', 'PKX', 'PL', 'PLAB', 'PLAO', 'PLAOU', 'PLAOW', 'PLAY', 'PLBC', 'PLBY', 'PLCE', 'PLD',
              'PLL', 'PLMI', 'PLMIW', 'PLMR', 'PLNT', 'PLOW', 'PLPC', 'PLRX', 'PLSE', 'PLTK', 'PLTN', 'PLTNR', 'PLTNU',
              'PLTNW', 'PLTR', 'PLUG', 'PLUR', 'PLUS', 'PLXS', 'PLYA', 'PLYM', 'PM', 'PMCB', 'PMD', 'PMF', 'PML',
              'PMM', 'PMN', 'PMO', 'PMT', 'PMTS', 'PMVP', 'PMX', 'PNAC', 'PNACR', 'PNACW', 'PNBK', 'PNC', 'PNF',
              'PNFP', 'PNFPP', 'PNI', 'PNM', 'PNNT', 'PNR', 'PNRG', 'PNT', 'PNTG', 'PNW', 'POAI', 'POCI', 'PODD',
              'POET', 'POLA', 'POOL', 'POR', 'PORT', 'POST', 'POWI', 'POWL', 'POWW', 'POWWP', 'PPBI', 'PPBT', 'PPC',
              'PPG', 'PPHP', 'PPHPR', 'PPHPW', 'PPIH', 'PPL', 'PPSI', 'PPT', 'PPTA', 'PPYA', 'PR', 'PRA', 'PRAA',
              'PRAX', 'PRCH', 'PRCT', 'PRDO', 'PRDS', 'PRE', 'PRENW', 'PRFT', 'PRFX', 'PRG', 'PRGO', 'PRGS', 'PRH',
              'PRI', 'PRIF', 'PRIM', 'PRLB', 'PRLD', 'PRLH', 'PRLHU', 'PRLHW', 'PRM', 'PRME', 'PRMW', 'PRO', 'PROC',
              'PROCW', 'PROF', 'PROK', 'PROV', 'PRPC', 'PRPH', 'PRPL', 'PRPO', 'PRQR', 'PRS', 'PRSO', 'PRSR', 'PRSRU',
              'PRSRW', 'PRST', 'PRSTW', 'PRT', 'PRTA', 'PRTC', 'PRTG', 'PRTH', 'PRTK', 'PRTS', 'PRU', 'PRVA', 'PSA',
              'PSEC', 'PSF', 'PSFE', 'PSHG', 'PSMT', 'PSN', 'PSNL', 'PSNY', 'PSNYW', 'PSO', 'PSQH', 'PSTG', 'PSTL',
              'PSTV', 'PSTX', 'PSX', 'PT', 'PTA', 'PTC', 'PTCT', 'PTEN', 'PTGX', 'PTHR', 'PTHRU', 'PTHRW', 'PTIX',
              'PTIXW', 'PTLO', 'PTMN', 'PTON', 'PTPI', 'PTRA', 'PTRS', 'PTSI', 'PTVE', 'PTWO', 'PTWOW', 'PTY', 'PUBM',
              'PUCK', 'PUCKU', 'PUCKW', 'PUK', 'PULM', 'PUMP', 'PUYI', 'PVBC', 'PVH', 'PVL', 'PWFL', 'PWM', 'PWOD',
              'PWP', 'PWR', 'PWSC', 'PWUP', 'PWUPU', 'PWUPW', 'PX', 'PXD', 'PXLW', 'PXMD', 'PXS', 'PXSAP', 'PXSAW',
              'PYCR', 'PYN', 'PYPD', 'PYPL', 'PYR', 'PYT', 'PYXS', 'PZC', 'PZZA', 'Q', 'QBTS', 'QCOM', 'QCRH', 'QD',
              'QDEL', 'QDRO', 'QDROW', 'QFIN', 'QFTA', 'QGEN', 'QH', 'QIPT', 'QLGN', 'QLI', 'QLYS', 'QMCO', 'QNCX',
              'QNRX', 'QNST', 'QOMO', 'QQQX', 'QRHC', 'QRTEA', 'QRTEB', 'QRTEP', 'QRVO', 'QS', 'QSG', 'QSI', 'QSIAW',
              'QSR', 'QTRX', 'QTWO', 'QUAD', 'QUBT', 'QUIK', 'QUOT', 'QURE', 'QVCC', 'QVCD', 'R', 'RA', 'RACE', 'RAD',
              'RADI', 'RAIL', 'RAIN', 'RAMP', 'RAND', 'RANI', 'RAPT', 'RARE', 'RAVE', 'RAYA', 'RBA', 'RBB', 'RBBN',
              'RBC', 'RBCAA', 'RBCP', 'RBKB', 'RBLX', 'RBOT', 'RBT', 'RC', 'RCA', 'RCAC', 'RCACU', 'RCACW', 'RCAT',
              'RCB', 'RCC', 'RCEL', 'RCFA', 'RCI', 'RCKT', 'RCKTW', 'RCKY', 'RCL', 'RCLF', 'RCLFU', 'RCLFW', 'RCM',
              'RCMT', 'RCON', 'RCRT', 'RCRTW', 'RCS', 'RCUS', 'RDCM', 'RDFN', 'RDHL', 'RDI', 'RDIB', 'RDN', 'RDNT',
              'RDVT', 'RDW', 'RDWR', 'RDY', 'REAL', 'REAX', 'REBN', 'REE', 'REFI', 'REFR', 'REG', 'REGN', 'REKR',
              'RELI', 'RELL', 'RELX', 'RELY', 'RENE', 'RENEU', 'RENEW', 'RENT', 'REPL', 'RERE', 'RES', 'RETA', 'RETO',
              'REUN', 'REVB', 'REVBW', 'REVG', 'REX', 'REXR', 'REYN', 'REZI', 'RF', 'RFAC', 'RFACR', 'RFACW', 'RFI',
              'RFIL', 'RFL', 'RFM', 'RFMZ', 'RGA', 'RGC', 'RGCO', 'RGEN', 'RGF', 'RGLD', 'RGLS', 'RGNX', 'RGP', 'RGR',
              'RGS', 'RGT', 'RGTI', 'RGTIW', 'RH', 'RHI', 'RHP', 'RIBT', 'RICK', 'RIG', 'RIGL', 'RILY', 'RILYG',
              'RILYK', 'RILYL', 'RILYM', 'RILYN', 'RILYO', 'RILYP', 'RILYT', 'RILYZ', 'RIO', 'RIOT', 'RITM', 'RIV',
              'RIVN', 'RJF', 'RKDA', 'RKLB', 'RKT', 'RL', 'RLAY', 'RLI', 'RLJ', 'RLMD', 'RLTY', 'RLX', 'RLYB', 'RM',
              'RMAX', 'RMBI', 'RMBL', 'RMBS', 'RMCF', 'RMD', 'RMGC', 'RMGCU', 'RMGCW', 'RMI', 'RMM', 'RMMZ', 'RMNI',
              'RMPL', 'RMR', 'RMT', 'RMTI', 'RNA', 'RNAZ', 'RNG', 'RNGR', 'RNLX', 'RNP', 'RNR', 'RNST', 'RNW', 'RNWWW',
              'RNXT', 'ROAD', 'ROCK', 'ROCL', 'ROCLW', 'ROG', 'ROIC', 'ROIV', 'ROIVW', 'ROK', 'ROKU', 'ROL', 'ROOT',
              'ROP', 'ROSE', 'ROSEU', 'ROSEW', 'ROSS', 'ROST', 'ROVR', 'RPAY', 'RPD', 'RPHM', 'RPID', 'RPM', 'RPRX',
              'RPT', 'RPTX', 'RQI', 'RRAC', 'RRBI', 'RRC', 'RRGB', 'RRR', 'RRX', 'RS', 'RSF', 'RSG', 'RSI', 'RSKD',
              'RSLS', 'RSSS', 'RSVR', 'RSVRW', 'RTC', 'RTL', 'RTLPO', 'RTLPP', 'RTO', 'RTX', 'RUM', 'RUMBW', 'RUN',
              'RUSHA', 'RUSHB', 'RVLP', 'RVLV', 'RVMD', 'RVNC', 'RVPH', 'RVPHW', 'RVSB', 'RVSN', 'RVSNW', 'RVT',
              'RVTY', 'RVYL', 'RWAY', 'RWAYL', 'RWAYZ', 'RWLK', 'RWOD', 'RWODW', 'RWT', 'RXO', 'RXRX', 'RXST', 'RXT',
              'RY', 'RYAAY', 'RYAM', 'RYAN', 'RYI', 'RYN', 'RYTM', 'RZB', 'RZC', 'RZLT', 'S', 'SA', 'SABR', 'SABRP',
              'SABS', 'SABSW', 'SAFE', 'SAFT', 'SAGA', 'SAGAR', 'SAGE', 'SAH', 'SAI', 'SAIA', 'SAIC', 'SAITW', 'SAJ',
              'SAL', 'SALM', 'SAM', 'SAMAW', 'SAMG', 'SAN', 'SANA', 'SAND', 'SANG', 'SANM', 'SANW', 'SAP', 'SAR',
              'SASI', 'SASR', 'SAT', 'SATL', 'SATLW', 'SATS', 'SAVA', 'SAVE', 'SAY', 'SAZ', 'SB', 'SBAC', 'SBBA',
              'SBCF', 'SBET', 'SBFG', 'SBFM', 'SBFMW', 'SBGI', 'SBH', 'SBI', 'SBIG', 'SBIGW', 'SBLK', 'SBOW', 'SBR',
              'SBRA', 'SBS', 'SBSI', 'SBSW', 'SBT', 'SBUX', 'SBXC', 'SCCO', 'SCD', 'SCE', 'SCHL', 'SCHN', 'SCHW',
              'SCI', 'SCKT', 'SCL', 'SCLX', 'SCLXW', 'SCM', 'SCOR', 'SCPH', 'SCPL', 'SCRM', 'SCRMU', 'SCRMW', 'SCS',
              'SCSC', 'SCTL', 'SCU', 'SCVL', 'SCWO', 'SCWX', 'SCX', 'SCYX', 'SD', 'SDA', 'SDAWW', 'SDC', 'SDGR',
              'SDHY', 'SDIG', 'SDRL', 'SE', 'SEAC', 'SEAL', 'SEAS', 'SEAT', 'SEATW', 'SECO', 'SEDG', 'SEE', 'SEED',
              'SEEL', 'SEER', 'SEIC', 'SELB', 'SELF', 'SEM', 'SEMR', 'SENEA', 'SENEB', 'SEPA', 'SEPAW', 'SERA', 'SES',
              'SEVN', 'SF', 'SFB', 'SFBC', 'SFBS', 'SFE', 'SFIX', 'SFL', 'SFM', 'SFNC', 'SFR', 'SFRWW', 'SFST', 'SFT',
              'SFWL', 'SG', 'SGA', 'SGBX', 'SGC', 'SGEN', 'SGH', 'SGHC', 'SGHT', 'SGIIW', 'SGLY', 'SGMA', 'SGML',
              'SGMO', 'SGMT', 'SGRP', 'SGRY', 'SGTX', 'SGU', 'SHAK', 'SHAP', 'SHBI', 'SHC', 'SHCO', 'SHCR', 'SHCRW',
              'SHEL', 'SHEN', 'SHFS', 'SHFSW', 'SHG', 'SHIP', 'SHLS', 'SHLT', 'SHO', 'SHOO', 'SHOP', 'SHPH', 'SHPW',
              'SHUA', 'SHUAW', 'SHW', 'SHYF', 'SIBN', 'SID', 'SIDU', 'SIEB', 'SIEN', 'SIFY', 'SIG', 'SIGA', 'SIGI',
              'SIGIP', 'SII', 'SILC', 'SILK', 'SILO', 'SIMO', 'SINT', 'SIRI', 'SISI', 'SITC', 'SITE', 'SITM', 'SIX',
              'SJ', 'SJM', 'SJT', 'SJW', 'SKE', 'SKGR', 'SKGRW', 'SKIL', 'SKIN', 'SKLZ', 'SKM', 'SKT', 'SKWD', 'SKX',
              'SKY', 'SKYT', 'SKYW', 'SKYX', 'SLAB', 'SLAC', 'SLACU', 'SLACW', 'SLAM', 'SLAMU', 'SLAMW', 'SLB', 'SLCA',
              'SLDB', 'SLDP', 'SLDPW', 'SLF', 'SLG', 'SLGC', 'SLGCW', 'SLGG', 'SLGL', 'SLGN', 'SLM', 'SLMBP', 'SLN',
              'SLNA', 'SLNAW', 'SLNG', 'SLNH', 'SLNHP', 'SLNO', 'SLP', 'SLQT', 'SLRC', 'SLRN', 'SLRX', 'SLS', 'SLVM',
              'SLVR', 'SLVRW', 'SM', 'SMAP', 'SMAPW', 'SMAR', 'SMBC', 'SMBK', 'SMCI', 'SMFG', 'SMFL', 'SMG', 'SMHI',
              'SMID', 'SMLP', 'SMLR', 'SMMF', 'SMMT', 'SMP', 'SMPL', 'SMR', 'SMRT', 'SMSI', 'SMTC', 'SMTI', 'SMWB',
              'SMX', 'SMXWW', 'SNA', 'SNAL', 'SNAP', 'SNAX', 'SNAXW', 'SNBR', 'SNCE', 'SNCR', 'SNCRL', 'SNCY', 'SND',
              'SNDA', 'SNDL', 'SNDR', 'SNDX', 'SNES', 'SNEX', 'SNFCA', 'SNGX', 'SNN', 'SNOA', 'SNOW', 'SNPO', 'SNPS',
              'SNPX', 'SNSE', 'SNT', 'SNTG', 'SNTI', 'SNV', 'SNX', 'SNY', 'SO', 'SOBR', 'SOFI', 'SOFO', 'SOHO',
              'SOHOB', 'SOHON', 'SOHOO', 'SOHU', 'SOI', 'SOJC', 'SOJD', 'SOJE', 'SOL', 'SOLO', 'SOLOW', 'SON', 'SOND',
              'SONDW', 'SONM', 'SONN', 'SONO', 'SONX', 'SONY', 'SOPA', 'SOPH', 'SOR', 'SOS', 'SOTK', 'SOUN', 'SOUNW',
              'SOVO', 'SP', 'SPB', 'SPCB', 'SPCE', 'SPE', 'SPFI', 'SPG', 'SPGI', 'SPH', 'SPHR', 'SPI', 'SPIR', 'SPLK',
              'SPLP', 'SPNS', 'SPNT', 'SPOK', 'SPOT', 'SPPI', 'SPR', 'SPRB', 'SPRC', 'SPRO', 'SPRU', 'SPRY', 'SPSC',
              'SPT', 'SPTN', 'SPWH', 'SPWR', 'SPXC', 'SPXX', 'SQ', 'SQFT', 'SQFTP', 'SQFTW', 'SQL', 'SQLLW', 'SQM',
              'SQNS', 'SQSP', 'SR', 'SRAD', 'SRC', 'SRCE', 'SRCL', 'SRDX', 'SRE', 'SREA', 'SRG', 'SRI', 'SRL', 'SRPT',
              'SRRK', 'SRT', 'SRTS', 'SRV', 'SRZN', 'SRZNW', 'SSB', 'SSBI', 'SSBK', 'SSD', 'SSIC', 'SSKN', 'SSL',
              'SSNC', 'SSNT', 'SSP', 'SSRM', 'SSSS', 'SSSSL', 'SST', 'SSTI', 'SSTK', 'SSU', 'SSYS', 'ST', 'STAA',
              'STAF', 'STAG', 'STBA', 'STBX', 'STC', 'STCN', 'STE', 'STEL', 'STEM', 'STEP', 'STER', 'STEW', 'STG',
              'STGW', 'STHO', 'STIM', 'STIX', 'STIXW', 'STK', 'STKH', 'STKL', 'STKS', 'STLA', 'STLD', 'STM', 'STN',
              'STNE', 'STNG', 'STOK', 'STR', 'STRA', 'STRC', 'STRCW', 'STRL', 'STRM', 'STRO', 'STRR', 'STRRP', 'STRS',
              'STRT', 'STSS', 'STSSW', 'STT', 'STTK', 'STVN', 'STWD', 'STX', 'STZ', 'SU', 'SUAC', 'SUI', 'SUM', 'SUN',
              'SUNL', 'SUNW', 'SUP', 'SUPN', 'SUPV', 'SURF', 'SURG', 'SURGW', 'SUZ', 'SVC', 'SVFD', 'SVII', 'SVIIR',
              'SVIIU', 'SVIIW', 'SVRA', 'SVRE', 'SVREW', 'SVV', 'SVVC', 'SWAG', 'SWAV', 'SWBI', 'SWI', 'SWIM', 'SWK',
              'SWKH', 'SWKS', 'SWN', 'SWSS', 'SWSSW', 'SWTX', 'SWVL', 'SWVLW', 'SWX', 'SWZ', 'SXC', 'SXI', 'SXT',
              'SXTC', 'SXTP', 'SXTPW', 'SY', 'SYBT', 'SYBX', 'SYF', 'SYK', 'SYM', 'SYNA', 'SYNH', 'SYPR', 'SYRS',
              'SYT', 'SYTA', 'SYTAW', 'SYY', 'SZZL', 'T', 'TAC', 'TACT', 'TAIT', 'TAK', 'TAL', 'TALK', 'TALKW', 'TALO',
              'TALS', 'TANH', 'TAOP', 'TAP', 'TARA', 'TARO', 'TARS', 'TASK', 'TAST', 'TATT', 'TAYD', 'TBB', 'TBBK',
              'TBC', 'TBCP', 'TBCPW', 'TBI', 'TBIO', 'TBLA', 'TBLAW', 'TBLD', 'TBLT', 'TBLTW', 'TBMC', 'TBMCR', 'TBNK',
              'TBPH', 'TC', 'TCBC', 'TCBI', 'TCBIO', 'TCBK', 'TCBP', 'TCBPW', 'TCBS', 'TCBX', 'TCI', 'TCJH', 'TCMD',
              'TCN', 'TCOA', 'TCOM', 'TCON', 'TCPC', 'TCRT', 'TCRX', 'TCS', 'TCX', 'TD', 'TDC', 'TDCX', 'TDF', 'TDG',
              'TDOC', 'TDS', 'TDUP', 'TDW', 'TDY', 'TEAF', 'TEAM', 'TECH', 'TECK', 'TECTP', 'TEDU', 'TEF', 'TEI',
              'TEL', 'TELA', 'TENB', 'TENK', 'TENKR', 'TENX', 'TEO', 'TER', 'TERN', 'TETE', 'TEVA', 'TEX', 'TFC',
              'TFFP', 'TFII', 'TFIN', 'TFINP', 'TFPM', 'TFSA', 'TFSL', 'TFX', 'TG', 'TGAA', 'TGAAU', 'TGAAW', 'TGAN',
              'TGH', 'TGI', 'TGL', 'TGLS', 'TGNA', 'TGS', 'TGT', 'TGTX', 'TGVCW', 'TH', 'THC', 'THCH', 'THCP', 'THCPW',
              'THFF', 'THG', 'THMO', 'THO', 'THQ', 'THR', 'THRD', 'THRM', 'THRN', 'THRX', 'THRY', 'THS', 'THTX', 'THW',
              'THWWW', 'TIGO', 'TIGR', 'TIL', 'TILE', 'TIMB', 'TIO', 'TIPT', 'TIRX', 'TISI', 'TITN', 'TIVC', 'TIXT',
              'TJX', 'TK', 'TKC', 'TKLF', 'TKNO', 'TKR', 'TLF', 'TLGA', 'TLGY', 'TLGYW', 'TLIS', 'TLK', 'TLRY', 'TLS',
              'TLSA', 'TLYS', 'TM', 'TMC', 'TMCI', 'TMCWW', 'TMDX', 'TME', 'TMHC', 'TMKR', 'TMKRW', 'TMO', 'TMPO',
              'TMPOW', 'TMST', 'TMTC', 'TMTCR', 'TMTCU', 'TMUS', 'TNC', 'TNDM', 'TNET', 'TNGX', 'TNK', 'TNL', 'TNON',
              'TNONW', 'TNP', 'TNXP', 'TNYA', 'TOI', 'TOIIW', 'TOL', 'TOMZ', 'TOP', 'TOPS', 'TORO', 'TOST', 'TOUR',
              'TOWN', 'TPB', 'TPC', 'TPCS', 'TPG', 'TPH', 'TPIC', 'TPL', 'TPR', 'TPST', 'TPTA', 'TPVG', 'TPX', 'TPZ',
              'TR', 'TRC', 'TRCA', 'TRDA', 'TREE', 'TREX', 'TRGP', 'TRHC', 'TRI', 'TRIB', 'TRIN', 'TRINL', 'TRIP',
              'TRIS', 'TRKA', 'TRKAW', 'TRMB', 'TRMD', 'TRMK', 'TRMR', 'TRN', 'TRNO', 'TRNR', 'TRNS', 'TRON', 'TROO',
              'TROW', 'TROX', 'TRP', 'TRS', 'TRST', 'TRTL', 'TRTN', 'TRTX', 'TRU', 'TRUE', 'TRUP', 'TRV', 'TRVG',
              'TRVI', 'TRVN', 'TS', 'TSAT', 'TSBK', 'TSBX', 'TSCO', 'TSE', 'TSEM', 'TSHA', 'TSI', 'TSLA', 'TSLX',
              'TSM', 'TSN', 'TSP', 'TSQ', 'TSRI', 'TSVT', 'TT', 'TTC', 'TTD', 'TTE', 'TTEC', 'TTEK', 'TTGT', 'TTI',
              'TTMI', 'TTNP', 'TTOO', 'TTP', 'TTSH', 'TTWO', 'TU', 'TUP', 'TURN', 'TUSK', 'TUYA', 'TV', 'TVC', 'TVE',
              'TVTX', 'TW', 'TWCBW', 'TWI', 'TWIN', 'TWKS', 'TWLO', 'TWLV', 'TWLVU', 'TWLVW', 'TWN', 'TWNK', 'TWO',
              'TWOA', 'TWOU', 'TWST', 'TX', 'TXG', 'TXMD', 'TXN', 'TXO', 'TXRH', 'TXT', 'TY', 'TYG', 'TYGO', 'TYGOW',
              'TYL', 'TYRA', 'TZOO', 'U', 'UA', 'UAA', 'UAL', 'UAN', 'UBA', 'UBCP', 'UBER', 'UBFO', 'UBP', 'UBS',
              'UBSI', 'UBX', 'UCAR', 'UCBI', 'UCBIO', 'UCL', 'UCTT', 'UDMY', 'UDR', 'UE', 'UEIC', 'UFCS', 'UFI',
              'UFPI', 'UFPT', 'UG', 'UGI', 'UGIC', 'UGP', 'UGRO', 'UHAL', 'UHG', 'UHGWW', 'UHS', 'UHT', 'UI', 'UIHC',
              'UIS', 'UK', 'UKOMW', 'UL', 'ULBI', 'ULCC', 'ULH', 'ULTA', 'UMBF', 'UMC', 'UMH', 'UNB', 'UNCY', 'UNF',
              'UNFI', 'UNH', 'UNIT', 'UNM', 'UNMA', 'UNP', 'UNTY', 'UNVR', 'UONE', 'UONEK', 'UP', 'UPBD', 'UPC', 'UPH',
              'UPLD', 'UPS', 'UPST', 'UPTD', 'UPTDU', 'UPTDW', 'UPWK', 'UPXI', 'URBN', 'URGN', 'URI', 'UROY', 'USA',
              'USAC', 'USAP', 'USAU', 'USB', 'USCB', 'USCT', 'USCTU', 'USCTW', 'USDP', 'USEA', 'USEG', 'USFD', 'USGO',
              'USGOW', 'USIO', 'USLM', 'USM', 'USNA', 'USPH', 'UTAA', 'UTAAU', 'UTAAW', 'UTF', 'UTHR', 'UTI', 'UTL',
              'UTMD', 'UTME', 'UTRS', 'UTSI', 'UTZ', 'UVE', 'UVSP', 'UVV', 'UWMC', 'UXIN', 'UZD', 'UZE', 'UZF', 'V',
              'VABK', 'VAC', 'VACC', 'VAL', 'VALE', 'VALN', 'VALU', 'VANI', 'VAPO', 'VAQC', 'VATE', 'VAXX', 'VBF',
              'VBFC', 'VBIV', 'VBLT', 'VBNK', 'VBTX', 'VC', 'VCEL', 'VCIF', 'VCIG', 'VCNX', 'VCSA', 'VCTR', 'VCV',
              'VCXA', 'VCXAU', 'VCXAW', 'VCXB', 'VCYT', 'VECO', 'VEDU', 'VEEE', 'VEEV', 'VEL', 'VEON', 'VERA', 'VERB',
              'VERBW', 'VERI', 'VERO', 'VERU', 'VERV', 'VERX', 'VERY', 'VET', 'VEV', 'VFC', 'VFF', 'VGAS', 'VGASW',
              'VGI', 'VGM', 'VGR', 'VHC', 'VHI', 'VHNA', 'VHNAU', 'VHNAW', 'VIA', 'VIAO', 'VIASP', 'VIAV', 'VICI',
              'VICR', 'VIEW', 'VIEWW', 'VIGL', 'VII', 'VIIAU', 'VINC', 'VINO', 'VINP', 'VIOT', 'VIPS', 'VIR', 'VIRC',
              'VIRI', 'VIRT', 'VIRX', 'VISL', 'VIST', 'VITL', 'VIV', 'VIVK', 'VJET', 'VKQ', 'VKTX', 'VLCN', 'VLD',
              'VLGEA', 'VLN', 'VLO', 'VLRS', 'VLT', 'VLY', 'VLYPO', 'VLYPP', 'VMAR', 'VMC', 'VMCA', 'VMCAU', 'VMCAW',
              'VMD', 'VMEO', 'VMI', 'VMO', 'VMW', 'VNCE', 'VNDA', 'VNET', 'VNO', 'VNOM', 'VNT', 'VOC', 'VOD', 'VOR',
              'VOXR', 'VOXX', 'VOYA', 'VPG', 'VPV', 'VQS', 'VRA', 'VRAR', 'VRAX', 'VRAY', 'VRCA', 'VRDN', 'VRE',
              'VREX', 'VRM', 'VRME', 'VRMEW', 'VRNA', 'VRNS', 'VRNT', 'VRPX', 'VRRM', 'VRSK', 'VRSN', 'VRT', 'VRTS',
              'VRTV', 'VRTX', 'VS', 'VSAC', 'VSACW', 'VSAT', 'VSCO', 'VSEC', 'VSH', 'VSSYW', 'VST', 'VSTA', 'VSTM',
              'VSTO', 'VTEX', 'VTGN', 'VTLE', 'VTMX', 'VTN', 'VTNR', 'VTOL', 'VTR', 'VTRS', 'VTRU', 'VTS', 'VTSI',
              'VTVT', 'VTYX', 'VUZI', 'VVI', 'VVOS', 'VVPR', 'VVR', 'VVV', 'VVX', 'VWE', 'VWEWW', 'VXRT', 'VYGR',
              'VYNE', 'VZIO', 'W', 'WAB', 'WABC', 'WAFD', 'WAFDP', 'WAFU', 'WAL', 'WALD', 'WALDW', 'WASH', 'WAT',
              'WATT', 'WAVC', 'WAVD', 'WAVE', 'WAVS', 'WAVSU', 'WAVSW', 'WB', 'WBA', 'WBD', 'WBS', 'WBX', 'WCC', 'WCN',
              'WD', 'WDAY', 'WDC', 'WDFC', 'WDH', 'WDI', 'WDS', 'WE', 'WEA', 'WEAV', 'WEC', 'WEL', 'WELL', 'WEN',
              'WERN', 'WES', 'WEST', 'WESTW', 'WETG', 'WEX', 'WEYS', 'WF', 'WFC', 'WFCF', 'WFG', 'WFRD', 'WGO', 'WGS',
              'WGSWW', 'WH', 'WHD', 'WHF', 'WHG', 'WHLM', 'WHLR', 'WHLRD', 'WHLRP', 'WHR', 'WIA', 'WILC', 'WIMI',
              'WINA', 'WING', 'WINT', 'WINV', 'WIRE', 'WISA', 'WISH', 'WIT', 'WIW', 'WIX', 'WK', 'WKC', 'WKEY', 'WKHS',
              'WKME', 'WKSP', 'WKSPW', 'WLDN', 'WLDS', 'WLDSW', 'WLFC', 'WLGS', 'WLK', 'WLKP', 'WLY', 'WLYB', 'WM',
              'WMB', 'WMC', 'WMG', 'WMK', 'WMPN', 'WMS', 'WMT', 'WNC', 'WNEB', 'WNNR', 'WNS', 'WNW', 'WOLF', 'WOOF',
              'WOR', 'WORX', 'WOW', 'WPC', 'WPM', 'WPP', 'WPRT', 'WRAP', 'WRB', 'WRBY', 'WRK', 'WRLD', 'WRNT', 'WSBC',
              'WSBCP', 'WSBF', 'WSC', 'WSFS', 'WSM', 'WSO', 'WSR', 'WST', 'WT', 'WTBA', 'WTER', 'WTFC', 'WTFCM',
              'WTFCP', 'WTI', 'WTM', 'WTMA', 'WTMAR', 'WTRG', 'WTS', 'WTTR', 'WTW', 'WU', 'WULF', 'WVE', 'WVVI',
              'WVVIP', 'WW', 'WWAC', 'WWACU', 'WWACW', 'WWD', 'WWE', 'WWW', 'WY', 'WYNN', 'X', 'XAIR', 'XBIO', 'XBIOW',
              'XBIT', 'XCUR', 'XEL', 'XELA', 'XELAP', 'XELB', 'XENE', 'XERS', 'XFIN', 'XFINU', 'XFLT', 'XFOR', 'XGN',
              'XHR', 'XIN', 'XLO', 'XMTR', 'XNCR', 'XNET', 'XOM', 'XOMA', 'XOMAO', 'XOMAP', 'XOS', 'XOSWW', 'XP',
              'XPAX', 'XPAXU', 'XPAXW', 'XPDB', 'XPDBW', 'XPEL', 'XPER', 'XPEV', 'XPO', 'XPOF', 'XPON', 'XPRO', 'XRAY',
              'XRTX', 'XRX', 'XTLB', 'XWEL', 'XXII', 'XYF', 'XYL', 'Y', 'YALA', 'YELL', 'YELP', 'YETI', 'YEXT', 'YGF',
              'YGMZ', 'YI', 'YJ', 'YMAB', 'YMM', 'YORW', 'YOSH', 'YOTA', 'YOTAR', 'YOTAW', 'YOU', 'YPF', 'YQ', 'YRD',
              'YS', 'YSBPW', 'YSG', 'YTEN', 'YTRA', 'YUM', 'YUMC', 'YVR', 'YY', 'Z', 'ZAPP', 'ZAPPW', 'ZBH', 'ZBRA',
              'ZCMD', 'ZD', 'ZENV', 'ZEPP', 'ZETA', 'ZEUS', 'ZEV', 'ZFOX', 'ZFOXW', 'ZG', 'ZGN', 'ZH', 'ZI', 'ZIM',
              'ZIMV', 'ZING', 'ZINGU', 'ZINGW', 'ZION', 'ZIONL', 'ZIONO', 'ZIONP', 'ZIP', 'ZIVO', 'ZIVOW', 'ZJYL',
              'ZKIN', 'ZLAB', 'ZM', 'ZNTL', 'ZS', 'ZTEK', 'ZTO', 'ZTR', 'ZTS', 'ZUMZ', 'ZUO', 'ZURA', 'ZURAW', 'ZVIA',
              'ZVRA', 'ZVSA', 'ZWS', 'ZYME', 'ZYNE', 'ZYXI']


# 모든 주식 정보를 딕셔너리 엘리먼트 형태로 담는 리스트
total_stock_info_list = []

# 오늘 날짜를 8자리 숫자로
today = int(date.today().strftime('%Y%m%d'))

# 오늘 날짜를 '2020-07-01' 형태의 변수로
today_date_str = date.today().strftime('%Y-%m-%d')

# 오늘 날짜에서 5년 전 날짜를 '2020-07-01' 형태의 변수로
today = date.today()
five_years_back = today - timedelta(days=365 * 5)
five_years_back_str = five_years_back.strftime('%Y-%m-%d')

"""K O S P I"""
# 코스피 주식 정보를 total_stock_info_list에 담기
for ticker in KOSPI_tickers:
 dic = {}

 stock_name = stock.get_market_ticker_name(ticker)
 dic["stock_name"] = stock_name
 dic["ticker"] = ticker

 # 주식 가격 추출
 d1 = yf.Ticker(ticker + ".KS")
 last_close_price = d1.history()['Close'].iloc[-1]
 dic["price"] = last_close_price

 try:
  d1 = wrap(yf.download(ticker + ".KS", five_years_back_str, today_date_str))

  dic["rsi"] = d1['rsi'][-1]
  dic["macd"] = d1['macd'][-1]
  dic["mfi"] = d1['mfi'][-1]
  dic['eribull'] = d1['eribull'][-1]
  dic['ker'] = d1['ker'][-1]
  dic['stochrsi'] = d1['stochrsi'][-1]
  dic['wt1'] = d1['wt1'][-1]

  dic['close_7_smma'] = d1['close_7_smma'][-1]
  dic['close_10_roc'] = d1['close_10_roc'][-1]
  dic['high_5_roc'] = d1['high_5_roc'][-1]
  dic['close_10_mad'] = d1['close_10_mad'][-1]

  dic['trix'] = d1['trix'][-1]
  dic['tema'] = d1['tema'][-1]
  dic['vr'] = d1['vr'][-1]
  dic['wr'] = d1['wr'][-1]
  dic['cci'] = d1['cci'][-1]
  dic['atr'] = d1['atr'][-1]

  dic['supertrend'] = d1['supertrend'][-1]
  dic['pdi'] = d1['pdi'][-1]
  dic['ndi'] = d1['ndi'][-1]
  dic['adx'] = d1['adx'][-1]
  dic['kdjk'] = d1['kdjk'][-1]

  dic['kdjk'] = d1['kdjk'][-1]
  dic['kdjd'] = d1['kdjd'][-1]
  dic['kdjj'] = d1['kdjj'][-1]

  dic['cr'] = d1['cr'][-1]
  dic['boll_ub'] = d1['boll_ub'][-1]
  dic['boll_lb'] = d1['boll_lb'][-1]

  dic['ppo'] = d1['ppo'][-1]
  dic['ppos'] = d1['ppos'][-1]

  dic['vwma'] = d1['vwma'][-1]
  dic['chop'] = d1['chop'][-1]

  dic['eribull'] = d1['eribull'][-1]
  dic['eribear'] = d1['eribear'][-1]

  dic['eribull_5'] = d1['eribull_5'][-1]
  dic['eribear_5'] = d1['eribear_5'][-1]

  dic['high_5_ker'] = d1['high_5_ker'][-1]
  dic['aroon'] = d1['aroon'][-1]

  dic['coppock'] = d1['coppock'][-1]
  dic['ftr'] = d1['ftr'][-1]
  dic['rvgi'] = d1['rvgi'][-1]
  dic['rvgis'] = d1['rvgis'][-1]
  dic['rvgi_5'] = d1['rvgi_5'][-1]

  dic['inertia'] = d1['inertia'][-1]
  dic['inertia_10'] = d1['inertia_10'][-1]
  dic['kst'] = d1['kst'][-1]
  dic['pgo'] = d1['pgo'][-1]

  dic['psl'] = d1['psl'][-1]
  dic['pvo'] = d1['pvo'][-1]
  dic['qqe'] = d1['qqe'][-1]

  Gross_Profit_bool = int(d1.quarterly_financials.iloc[-4:-3][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-4:-3][" 2022-12-31"])
  Total_Revenue_bool = int(d1.quarterly_financials.iloc[-2:-1][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-2:-1][" 2022-12-31"])

  cnt = 0
  if (Gross_Profit_bool and Total_Revenue_bool):
   cnt = 2
  elif (Gross_Profit_bool or Total_Revenue_bool):
   cnt = 1
  dic['revenue_status'] = cnt

 except Exception:
  pass

 total_stock_info_list.append(dic)



"""K O S D A Q"""
# 코스피 주식 정보를 total_stock_info_list에 담기
for ticker in KOSDAQ_tickers:
 dic = {}

 stock_name = stock.get_market_ticker_name(ticker)
 dic["stock_name"] = stock_name
 dic["ticker"] = ticker

 # 주식 가격 추출
 d1 = yf.Ticker(ticker + ".KQ")
 last_close_price = d1.history()['Close'].iloc[-1]
 dic["price"] = last_close_price

 try:
  d1 = wrap(yf.download(ticker + ".KQ", five_years_back_str, today_date_str))

  dic["rsi"] = d1['rsi'][-1]
  dic["macd"] = d1['macd'][-1]
  dic["mfi"] = d1['mfi'][-1]
  dic['eribull'] = d1['eribull'][-1]
  dic['ker'] = d1['ker'][-1]
  dic['stochrsi'] = d1['stochrsi'][-1]
  dic['wt1'] = d1['wt1'][-1]

  dic['close_7_smma'] = d1['close_7_smma'][-1]
  dic['close_10_roc'] = d1['close_10_roc'][-1]
  dic['high_5_roc'] = d1['high_5_roc'][-1]
  dic['close_10_mad'] = d1['close_10_mad'][-1]

  dic['trix'] = d1['trix'][-1]
  dic['tema'] = d1['tema'][-1]
  dic['vr'] = d1['vr'][-1]
  dic['wr'] = d1['wr'][-1]
  dic['cci'] = d1['cci'][-1]
  dic['atr'] = d1['atr'][-1]

  dic['supertrend'] = d1['supertrend'][-1]
  dic['pdi'] = d1['pdi'][-1]
  dic['ndi'] = d1['ndi'][-1]
  dic['adx'] = d1['adx'][-1]
  dic['kdjk'] = d1['kdjk'][-1]

  dic['kdjk'] = d1['kdjk'][-1]
  dic['kdjd'] = d1['kdjd'][-1]
  dic['kdjj'] = d1['kdjj'][-1]

  dic['cr'] = d1['cr'][-1]
  dic['boll_ub'] = d1['boll_ub'][-1]
  dic['boll_lb'] = d1['boll_lb'][-1]

  dic['ppo'] = d1['ppo'][-1]
  dic['ppos'] = d1['ppos'][-1]

  dic['vwma'] = d1['vwma'][-1]
  dic['chop'] = d1['chop'][-1]

  dic['eribull'] = d1['eribull'][-1]
  dic['eribear'] = d1['eribear'][-1]

  dic['eribull_5'] = d1['eribull_5'][-1]
  dic['eribear_5'] = d1['eribear_5'][-1]

  dic['high_5_ker'] = d1['high_5_ker'][-1]
  dic['aroon'] = d1['aroon'][-1]

  dic['coppock'] = d1['coppock'][-1]
  dic['ftr'] = d1['ftr'][-1]
  dic['rvgi'] = d1['rvgi'][-1]
  dic['rvgis'] = d1['rvgis'][-1]
  dic['rvgi_5'] = d1['rvgi_5'][-1]

  dic['inertia'] = d1['inertia'][-1]
  dic['inertia_10'] = d1['inertia_10'][-1]
  dic['kst'] = d1['kst'][-1]
  dic['pgo'] = d1['pgo'][-1]

  dic['psl'] = d1['psl'][-1]
  dic['pvo'] = d1['pvo'][-1]
  dic['qqe'] = d1['qqe'][-1]

  Gross_Profit_bool = int(d1.quarterly_financials.iloc[-4:-3][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-4:-3][" 2022-12-31"])
  Total_Revenue_bool = int(d1.quarterly_financials.iloc[-2:-1][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-2:-1][" 2022-12-31"])

  cnt = 0
  if (Gross_Profit_bool and Total_Revenue_bool):
   cnt = 2
  elif (Gross_Profit_bool or Total_Revenue_bool):
   cnt = 1
  dic['revenue_status'] = cnt

 except Exception:
  pass

 total_stock_info_list.append(dic)



""" U S S T O C K"""
"""
# 미국 주식 정보를 total_stock_info_list에 담기
for ticker in US_tickers:
 dic = {}

 dic["stock_name"] = yf.Ticker(ticker).info["longName"]
 dic["ticker"] = ticker

 # 주식 가격 추출
 d1 = yf.Ticker(ticker)
 last_close_price = d1.history()['Close'].iloc[-1]
 dic["price"] = last_close_price

 try:
  d1 = wrap(yf.download(ticker, five_years_back_str, today_date_str))

  dic["rsi"] = d1['rsi'][-1]
  dic["macd"] = d1['macd'][-1]
  dic["mfi"] = d1['mfi'][-1]
  dic['eribull'] = d1['eribull'][-1]
  dic['ker'] = d1['ker'][-1]
  dic['stochrsi'] = d1['stochrsi'][-1]
  dic['wt1'] = d1['wt1'][-1]

  dic['close_7_smma'] = d1['close_7_smma'][-1]
  dic['close_10_roc'] = d1['close_10_roc'][-1]
  dic['high_5_roc'] = d1['high_5_roc'][-1]
  dic['close_10_mad'] = d1['close_10_mad'][-1]

  dic['trix'] = d1['trix'][-1]
  dic['tema'] = d1['tema'][-1]
  dic['vr'] = d1['vr'][-1]
  dic['wr'] = d1['wr'][-1]
  dic['cci'] = d1['cci'][-1]
  dic['atr'] = d1['atr'][-1]

  dic['supertrend'] = d1['supertrend'][-1]
  dic['pdi'] = d1['pdi'][-1]
  dic['ndi'] = d1['ndi'][-1]
  dic['adx'] = d1['adx'][-1]
  dic['kdjk'] = d1['kdjk'][-1]

  dic['kdjk'] = d1['kdjk'][-1]
  dic['kdjd'] = d1['kdjd'][-1]
  dic['kdjj'] = d1['kdjj'][-1]

  dic['cr'] = d1['cr'][-1]
  dic['boll_ub'] = d1['boll_ub'][-1]
  dic['boll_lb'] = d1['boll_lb'][-1]

  dic['ppo'] = d1['ppo'][-1]
  dic['ppos'] = d1['ppos'][-1]

  dic['vwma'] = d1['vwma'][-1]
  dic['chop'] = d1['chop'][-1]

  dic['eribull'] = d1['eribull'][-1]
  dic['eribear'] = d1['eribear'][-1]

  dic['eribull_5'] = d1['eribull_5'][-1]
  dic['eribear_5'] = d1['eribear_5'][-1]

  dic['high_5_ker'] = d1['high_5_ker'][-1]
  dic['aroon'] = d1['aroon'][-1]

  dic['coppock'] = d1['coppock'][-1]
  dic['ftr'] = d1['ftr'][-1]
  dic['rvgi'] = d1['rvgi'][-1]
  dic['rvgis'] = d1['rvgis'][-1]
  dic['rvgi_5'] = d1['rvgi_5'][-1]

  dic['inertia'] = d1['inertia'][-1]
  dic['inertia_10'] = d1['inertia_10'][-1]
  dic['kst'] = d1['kst'][-1]
  dic['pgo'] = d1['pgo'][-1]

  dic['psl'] = d1['psl'][-1]
  dic['pvo'] = d1['pvo'][-1]
  dic['qqe'] = d1['qqe'][-1]

  Gross_Profit_bool = int(d1.quarterly_financials.iloc[-4:-3][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-4:-3][" 2022-12-31"])
  Total_Revenue_bool = int(d1.quarterly_financials.iloc[-2:-1][" 2023-03-31"]) > int(
   d1.quarterly_financials.iloc[-2:-1][" 2022-12-31"])

  cnt = 0
  if (Gross_Profit_bool and Total_Revenue_bool):
   cnt = 2
  elif (Gross_Profit_bool or Total_Revenue_bool):
   cnt = 1
  dic['revenue_status'] = cnt

 except Exception:
  pass

 total_stock_info_list.append(dic)
"""

# home.html - 랜딩 홈페이지
@app.route('/')
def home():
	return render_template('home.html')

# signup.html - 회원가입 페이지
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    success_message = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not validate_username(username):
            return "Username must be at least 3 characters long."

        if not validate_email(email):
            flash('잘못된 형식의 이메일입니다', 'error')
            # return "Invalid email address. Please enter a valid email."
            return render_template('signup.html')

        if not validate_password(password):
            return "Password must be at least 8 characters long."

        user = get_user(username)
        if user:
            flash('이미 등록된 닉네임입니다', 'error')
            # return "Username already registered. Please choose a different username."
            return render_template('signup.html')

        if insert_user(username, email, password):
            return redirect(url_for('signup_success'))
        else:
            flash('이미 등록된 이메일입니다', 'error')
            # return "Email address already registered. Please use a different email."
            return render_template('signup.html')

        success_message = "Signup successful! You can now login."

    return render_template('signup.html', success_message=success_message)

# signup_success.html - 회원가입 성공 페이지
@app.route('/signup_success')
def signup_success():
    return render_template('signup_success.html')

# signup_failure.html - 회원가입 실패 페이지
"""@app.route('/signup_failure')
def signup_failure():
    return render_template('signup_failure.html')
"""

# login.html - 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_password = get_user_by_email(email)

        if hashed_password and bcrypt.check_password_hash(hashed_password[0], password):
            session['user_id'] = email
            
            # After Verify the validity of username and password
            session.permanent = True

            flash('로그인 성공! 환영합니다', 'success')
            return redirect(url_for('home'))
        else:
            flash('E Mail 혹은 비밀번호가 틀렸습니다.', 'error')

    return render_template('login.html')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            flash('확인 이메일이 일치하지 않습니다', 'error')
            return redirect(url_for('change_password'))

        # 닉네임 & 이메일 둘 다 확인되면
        if get_user(username) and get_user_by_email(email):
            update_password(username, email, new_password)

            flash('비밀번호 변경 완료 :)', 'success')
            return render_template('change_password.html')

        else:
            flash('무언가 잘못 되었습니다.', 'error')
            return render_template('change_password.html')

    return render_template('change_password.html')


#  stats.html - KOSPI 모든 주가 정보 - RAW DATA (주가랑 모든 요소 추가 해야 할듯)
@app.route('/raw_data')
def raw_data():
	return render_template('raw_data.html', data=total_stock_info_list)

# quant.html - 10가지 퀀트 수식
@app.route('/quant')
def quant():
	return render_template('quant.html', data=quant)

# ai_forcast.html - streamlit 웹사이트
@app.route('/ai_forecast')
def ai_forecast():
	return render_template('ai_forecast.html')

@app.route('/time_feed')
def time_feed():
    def generate():
        yield datetime.now().strftime("%Y.%m.%d|%H:%M:%S")  # return also will work
    return Response(generate(), mimetype='text')

if __name__ == '__main__':
	app.run(debug=True)