import datetime
import func_timeout
import mimetypes
import os.path
import poplib
import requests
import threading
import time
from bs4 import BeautifulSoup
from email.parser import BytesParser, Parser
from email.policy import default
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Float, Date, text, Time, \
    Boolean

from app import app

lock = threading.Lock()

IS_WACHING = True

engine = create_engine('sqlite:////app/auto_straker.db', echo=True, connect_args={"check_same_thread": False})

db_conn = engine.connect()

meta = MetaData()

job = Table(
    'job', meta,
    Column('job_offer', String, primary_key=True),
    Column('weighted_words', Float),
    Column('accepted', Boolean),
    Column('translator', String),
    Column('time', DateTime, default=datetime.datetime.now),
    Column('note', String),
)

import os
import base64
import logging
import random
import ssl
import string
from email.header import Header
from email.mime.text import MIMEText

import requests
from ldap3 import Tls, Server, Connection, NTLM, SUBTREE, MODIFY_REPLACE

SMTP_SERVER = os.environ.get("SMTP_SERVER", 'mail.wistronits.com')

is_cn_version = False
targeted_language = 'en-us > zh-tw'

try:
    if( os.environ['LANGUAGE'] == 'cn'):
        print("CN version")
        is_cn_version = True
        targeted_language = 'en-us > zh-cn'

    else:
        print("TW version")
except:
    print("TW version")




def sendmail(applicant_email, mail_html_content, title):
    message = MIMEText(mail_html_content, 'html', 'utf-8')
    message['From'] = Header("straker_watcher@wistronits.com")  # 傳送者
    message['To'] = Header(applicant_email)  # 接收者
    message['Subject'] = Header(title, 'utf-8')

    import smtplib
    try:

        smtpObj = smtplib.SMTP(SMTP_SERVER)
        smtpObj.sendmail("straker_watcher@wistronits.com", [applicant_email, ], message.as_string())
        print("%s 郵件傳送成功!" % applicant_email)
    except smtplib.SMTPException:
        print("Error: %s 無法傳送郵件" % applicant_email)


chrome_options = Options()
chrome_options.add_argument('--headless')

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

# 輸入郵件地址, 口令和POP3服務器地址
email = 'straker_watcher@wistronits.com'
password = ''
pop3_server = 'mapi.wistronits.com'

# 連接pop3服務器
conn = poplib.POP3_SSL(pop3_server, 995)

conn.user(email)
conn.pass_(password)

message_num, total_size = conn.stat()
print('郵件數：%s, 總大小：%s' % (message_num, total_size))

resp, mails, octets = conn.list()

translator_names = [
    'Alison Su',
    'Jennifer Kuo',
    'Meichuan Lee',
    'Polly Chang',
    'Susan Fang'
]

cn_translator_names = [
    'Angela Yuan',
    'Jojo Yang',
    'Naomi Zhao',
    'Thomas Cui',
    'Tina Gong'
]

translator_index = 0

try:
    last_file = open('last.txt', 'r')
    last_translator = last_file.read()
    translator_index = int(last_translator)
    print("translator_index start with {}".format(last_translator))
    last_file.close()
except:
    with open('last.txt', 'w') as f:
        f.write('0')
    print("Can't find last.txt, translator_index = 0")

job_offer = ''

def checking_email():
    global message_num, job_offer, translator_index, new_message_num, lock

    while (IS_WACHING):

        try:
            conn = func_timeout.func_timeout(3, poplib.POP3_SSL,
                                             args=[pop3_server, 995])

            func_timeout.func_timeout(3, conn.user, args=[email])
            func_timeout.func_timeout(3, conn.pass_, args=[password])
            # conn.set_debuglevel(1)
            new_message_num, total_size = func_timeout.func_timeout(3,
                                                                    conn.stat)

        except func_timeout.FunctionTimedOut:
            print("TIMEOUT")
            continue

        except Exception as e:
            print("Can't access email")
            print(e)
            continue

        accept_url = ''

        if (new_message_num < message_num):
            message_num = new_message_num
            print(message_num)
        elif (new_message_num > message_num):
            lock.acquire()

            new_num = new_message_num - message_num

            if(new_num <= 0):
                lock.release()
                print("RELEASE the lock")
                continue

            message_num = new_message_num

            lock.release()

            for i in range(message_num, message_num - new_num, -1):
                resp, data, octets = conn.retr(i)
                msg_data = b'\r\n'.join(data)
                msg = BytesParser(policy=default).parsebytes(msg_data)
                subject = msg['Subject']
                print('{}: New message with title:'.format(message_num) + subject)

                if ('Job Offer' in subject and targeted_language in subject and 'IBM workbench job - IBM LAB' in subject):

                    for part in msg.walk():
                        if part.get_content_maintype() == 'text':
                            soup = BeautifulSoup(part.get_content(), 'lxml')

                            for link in soup.find_all('a'):

                                if ('https://translator.strakertranslations.com/o/?action=purchaseorder' in link.get(
                                        'href')):
                                    accept_url = link.get('href')
                                    break

                    driver.get(accept_url)

                    print("accept URL = ", accept_url)

                    job_offer = subject[subject.index('TJ'): subject.index('TJ') + 9]

                    try:

                        scrollB = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "agency_translatorid"))
                        )

                        if(is_cn_version):
                            scrollB.send_keys( cn_translator_names[translator_index] )
                        else:
                            scrollB.send_keys( translator_names[translator_index] )

                        submit = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, "btn.green"))
                        )

                        submit.click()



                    except Exception as e:
                        print("FAIL TO LOCATE ELEMENT!!!")
                        fail_html = driver.page_source
                        fail_soup = BeautifulSoup(fail_html, 'lxml')
                        simplified_lines = [l for l in fail_soup.get_text().splitlines() if l]
                        print(simplified_lines)


                    html_source = driver.page_source

                    soup = BeautifulSoup(html_source, 'lxml')
                    word_count = float(subject[subject.index('words') + 5: subject.index(' weighted words')])

                    if ('Job Accepted' in soup.get_text()):

                        title = ''
                        mail_html_content = ''

                        if(is_cn_version):
                            print("{name} got this job: {job}, word count = {word_count}".format(name=cn_translator_names[translator_index], job=job_offer, word_count = word_count))
                            mail_html_content = """
                                        <p>Hi Straker Team,</p>
                                        <p>Straker Job Offer - {foffer}</p>
                                        <p>Weighted Words: {fword}</p>
                                        <p>已分配給翻譯者 {ftranslator}，謝謝！</p>
                                        """.format(foffer=job_offer, fword=word_count,
                                                   ftranslator=cn_translator_names[translator_index])

                            title = '自動搶案 {foffer} 翻譯者：{ftranslator}'.format(foffer=job_offer,
                                                                             ftranslator=cn_translator_names[translator_index])

                        else:
                            print("{name} got this job: {job}, word count = {word_count}".format(name=translator_names[translator_index], job=job_offer, word_count = word_count))
                            mail_html_content = """
                                        <p>Hi Straker Team,</p>
                                        <p>Straker Job Offer - {foffer}</p>
                                        <p>Weighted Words: {fword}</p>
                                        <p>已分配給翻譯者 {ftranslator}，謝謝！</p>
                                        """.format(foffer=job_offer, fword=word_count,
                                                   ftranslator=translator_names[translator_index])

                            title = '自動搶案 {foffer} 翻譯者：{ftranslator}'.format(foffer=job_offer,
                                                                             ftranslator=translator_names[translator_index])

                        receiver = 'straker_wits@wistronits.com'

                        try:
                            sendmail(receiver, mail_html_content, title)
                        except:
                            print("Fail to send mail")

                        try:
                            if(is_cn_version):
                                db_conn.execute(job.insert(), [
                                    {'job_offer': job_offer, 'weighted_words': word_count,
                                     'translator': cn_translator_names[translator_index], 'accepted': True}, ])
                            else:
                                db_conn.execute(job.insert(), [
                                    {'job_offer': job_offer, 'weighted_words': word_count,
                                     'translator': translator_names[translator_index], 'accepted': True}, ])

                        except:
                            print("The database already has this data")

                        translator_index = translator_index + 1

                        if(is_cn_version):

                            if (translator_index >= len(cn_translator_names) ):
                                translator_index = 0
                        else:
                            if (translator_index >= len(translator_names) ):
                                translator_index = 0

                        last_file = open('last.txt', 'w+')
                        last_file.write(str(translator_index))
                        last_file.close()

                    else:

                        print("Didn't get this job")
                        db_conn.execute(job.insert(), [
                            {'job_offer': job_offer, 'weighted_words': word_count, 'accepted': False}, ])


db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://///app/auto_straker.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

threading.Thread(target=checking_email, daemon=True).start()

@app.route("/", methods=['GET', 'POST'])
def index():
    global IS_WACHING, message_num, total_size
    print("IS_WACHING ", IS_WACHING)

    sql = 'SELECT * FROM job'
    result = db.engine.execute(sql).fetchall()

    if request.method == 'POST':
        if request.form.get('on_button') == 'On' or request.form.get("toggle_off") == 'on':
            print("ON!!")
            if (not IS_WACHING):

                IS_WACHING = True
                while True:
                    try:
                        conn = func_timeout.func_timeout(3, poplib.POP3_SSL, args=[pop3_server,
                                                                                   995])

                        func_timeout.func_timeout(3, conn.user, args=[email])
                        func_timeout.func_timeout(3, conn.pass_, args=[password])
                        message_num, total_size = func_timeout.func_timeout(3,
                                                                            conn.stat)
                        print("WHILE TRUE")
                        break

                    except func_timeout.FunctionTimedOut:
                        print("TIMEOUT")
                        continue

                    except Exception as e:
                        print("Can't access email")
                        print(e)
                print("NEW THREAD")
                threading.Thread(target=checking_email, daemon=True, name="FIRST").start()
                threading.Thread(target=checking_email, daemon=True, name="SECOND").start()
                threading.Thread(target=checking_email, daemon=True, name="THIRD").start()
                threading.Thread(target=checking_email, daemon=True, name="FOURTH").start()
                threading.Thread(target=checking_email, daemon=True, name="FIFTH").start()

                for thread in threading.enumerate():
                    print(thread.name)
            # checking_email()
        elif request.form.get('off_button') == 'Off' or request.form.get("toggle_off") == None:
            print("OFF!!")
            IS_WACHING = False

        else:
            print("PASSS")
            pass

    return render_template("form.html", testform=result, status="on" if IS_WACHING else 'off')
