import datetime
import func_timeout
import mimetypes
import os
import poplib
import requests
import threading
import time
from bs4 import BeautifulSoup
from email.parser import BytesParser, Parser
from email.policy import default
from flask import Flask, render_template, request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, EWSDateTime, EWSTimeZone, Configuration, NTLM, \
    GSSAPI, CalendarItem, Message, Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, HTMLBody, \
    Build, Version, FolderCollection
from urllib.parse import urlparse

import pymysql

db_host = os.environ.get("DB_HOST", "localhost")
db_port = os.environ.get("DB_PORT", 3306)
db_user = os.environ.get("DB_USER", "root")
db_pwd = os.environ.get("DB_PASSWORD", "straker")
db_name = os.environ.get("DB_NAME", "straker_db")

connn = pymysql.connect(host=db_host,
                        port=int(db_port),
                        user=db_user,
                        passwd=db_pwd,
                        db=db_name)

lock = threading.Lock()

is_on = True

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


def sendmail(applicant_email, mail_html_content, title):
    message = MIMEText(mail_html_content, 'html', 'utf-8')
    message['From'] = Header("straker_watcher@wistronits.com")  # sender
    message['To'] = Header(applicant_email)  # receiver
    message['Subject'] = Header(title, 'utf-8')

    import smtplib
    try:

        smtpObj = smtplib.SMTP(SMTP_SERVER)
        smtpObj.sendmail("straker_watcher@wistronits.com", [applicant_email, ], message.as_string())
        print("%s 郵件傳送成功!" % applicant_email)
    except smtplib.SMTPException:
        print("Error: %s 無法傳送郵件" % applicant_email)


tw_translator_names = [
    'Alison Su',
    'Amy Yeh',
    'Belle Chang',
    'Jennifer Kuo',
    'Meichuan Lee',
    'Polly Chang',
    'Simon Wei',
    'Susan Fang',
    'Vesta Weng'
]

cn_translator_names = [
    'Angela Yuan',
    'Ekin Zhang',
    'Guangzhi Zhu',
    'Ivy Lee',
    'Jojo Yang',
    'Naomi Zhao',
    'Thomas Cui',
    'Tina Gong',
    'Zoe Zhou'
]

is_cn_version = False
targeted_language = 'en-us > zh-tw'
targeted_language_short = 'tw'
translators = tw_translator_names

try:
    if (os.environ['LANGUAGE'] == 'cn'):
        print("CN version")
        is_cn_version = True
        targeted_language = 'en-us > zh-cn'
        targeted_language_short = 'cn'
        translators = cn_translator_names
    else:
        print("TW version")
except:
    print("TW version")

pem_path = os.path.join(os.getcwd(), 'wistronits-com-chain.pem')


class RootCAAdapter(requests.adapters.HTTPAdapter):

    def cert_verify(self, conn, url, verify, cert):
        cert_file = {
            'mapi.wistronits.com': pem_path
        }[urlparse(url).hostname]
        super(RootCAAdapter, self).cert_verify(conn=conn, url=url, verify=cert_file, cert=cert)


BaseProtocol.HTTP_ADAPTER_CLS = RootCAAdapter

credentials = Credentials(username='straker_watcher@wistronits.com', password='')
config = Configuration(server='mapi.wistronits.com', credentials=credentials, auth_type=NTLM)
account = Account('straker_watcher@wistronits.com', credentials=credentials, config=config, autodiscover=False)

temp_save = (account.root / '資訊存放區頂端' / '封存')

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

message_num = account.inbox.all().count()

translator_index = 0

with connn.cursor() as cursor:

    cursor.execute('SELECT translator FROM job WHERE accepted AND language = "{language}" ORDER BY time DESC LIMIT 1'.format(language = targeted_language_short) )

    translator_index = 0 # default

    result = (cursor.fetchone())

    if result is not None:

        print(result[0])
        print(translators.index(result[0]))

        translator_index = translators.index(result[0]) + 1

        if (translator_index >= len(translators)):
            translator_index = 0


print("translator index = ", translator_index)

job_offer = ''

def checking_email():
    global message_num, job_offer, translator_index, new_message_num, lock, account, credentials, config

    while (is_on):

        try:
            func_timeout.func_timeout(2, account.inbox.refresh)
            # account.inbox.refresh()
            new_message_num = account.inbox.all().count()

        except Exception as e:
            print("Can't access email")
            print(e)
            credentials = Credentials(username='straker_watcher@wistronits.com', password='')
            config = Configuration(server='mapi.wistronits.com', credentials=credentials, auth_type=NTLM)
            account = Account('straker_watcher@wistronits.com', credentials=credentials, config=config,
                              autodiscover=False)

            if (not is_cn_version):
                for item in account.inbox.all().order_by('datetime_received')[1:]:
                    item.move(to_folder=temp_save)

            continue

        accept_url = ''

        if (new_message_num < message_num):
            message_num = new_message_num
            print(message_num)
        elif (new_message_num > message_num):
            lock.acquire()

            new_num = new_message_num - message_num

            if (new_num <= 0):
                lock.release()
                print("RELEASE the lock")
                continue

            message_num = new_message_num

            lock.release()

            for item in account.inbox.all().order_by('-datetime_received')[:new_num]:
                subject = item.subject
                print('{}: New message with title:'.format(message_num) + subject)
                if ('Job Offer' in subject and targeted_language in subject and 'IBM workbench job - IBM LAB' in subject):

                    soup = BeautifulSoup(item.body, 'lxml')
                    for link in soup.find_all('a'):
                        if ('https://translator.strakertranslations.com/o/?action=purchaseorder' in link.get(
                                'href')):
                            driver.get(link.get('href'))
                            accept_url = link.get('href')
                            break

                    print("accept URL = ", accept_url)

                    job_offer = subject[subject.index('TJ'): subject.index('TJ') + 9]

                    try:

                        scrollB = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "agency_translatorid"))
                        )
                        scrollB.send_keys(translators[translator_index])
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

                        print("{name} got this job: {job}, word count = {word_count}".format(
                            name=translators[translator_index], job=job_offer, word_count=word_count))
                        mail_html_content = """
                                    <p>Hi Straker Team,</p>
                                    <p>Straker Job Offer - {foffer}</p>
                                    <p>Weighted Words: {fword}</p>
                                    <p>已分配給翻譯者 {ftranslator}，謝謝！</p>
                                    """.format(foffer=job_offer, fword=word_count,
                                               ftranslator=translators[translator_index])

                        title = '自動搶案 {foffer} 翻譯者：{ftranslator}'.format(foffer=job_offer,
                                                                         ftranslator=translators[translator_index])

                        receiver = 'straker_wits@wistronits.com'

                        try:
                            sendmail(receiver, mail_html_content, title)
                        except:
                            print("Fail to send mail")

                        try:

                            with connn.cursor() as cursor:
                                cursor.execute(
                                    "INSERT INTO job (job_id, weighted_words, translator, accepted, language) VALUES ('%s', '%s', '%s', '%s', '%s')" % (
                                        job_offer, word_count, translators[translator_index], 1, 'cn'))
                                connn.commit()

                        except Exception as e:
                            print(e)

                        translator_index = translator_index + 1

                        if (translator_index >= len(translators)):
                            translator_index = 0

                    elif('Create Purchase Order Success' in soup.get_text()):
                        print("Need to assign a translator")
                        with connn.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO job (job_id, weighted_words, accepted, language, note) VALUES ('%s', '%s', '%s', '%s', '%s')" % (
                                    job_offer, word_count, 1, targeted_language_short, 'Need to assign a translator'))
                            connn.commit()

                    else:

                        print("Didn't get this job")

                        with connn.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO job (job_id, weighted_words, accepted, language) VALUES ('%s', '%s', '%s', '%s')" % (
                                    job_offer, word_count, 0, targeted_language_short))
                            connn.commit()

                    if (not is_cn_version):
                        item.move(to_folder=temp_save)

app = Flask(__name__)

threading.Thread(target=checking_email, daemon=True).start()
if (not is_cn_version):
    for item in account.inbox.all().order_by('datetime_received')[1:]:
        item.move(to_folder=temp_save)

@app.route("/", methods=['GET', 'POST'])
def index():
    global is_on, message_num, credentials, config, account
    print("is_on ", is_on)

    with connn.cursor() as cursor:
        cursor.execute('SELECT * FROM job WHERE language = "{language}"'.format(language = targeted_language_short))
        result = (cursor.fetchall())
        connn.commit()

    if request.method == 'POST':
        if request.form.get('on_button') == 'On' or request.form.get("toggle_off") == 'on':
            print("Turn On")
            if (not is_on):
                credentials = Credentials(username='straker_watcher@wistronits.com', password='')
                config = Configuration(server='mapi.wistronits.com', credentials=credentials, auth_type=NTLM)
                account = Account('straker_watcher@wistronits.com', credentials=credentials, config=config,
                                  autodiscover=False)

                for item in account.inbox.all().order_by('datetime_received')[1:]:
                    item.move(to_folder=temp_save)

                account.inbox.refresh()
                message_num = account.inbox.all().count()

                is_on = True

                threading.Thread(target=checking_email, daemon=True, name="FIRST").start()

        elif request.form.get('off_button') == 'Off' or request.form.get("toggle_off") == None:
            print("Turn Off")
            is_on = False

    return render_template("form.html", testform=result, status="on" if is_on else 'off', language = targeted_language_short)

app.run(host="0.0.0.0", port=5000)
