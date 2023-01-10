from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from exchangelib import DELEGATE, IMPERSONATION, Account, Credentials, EWSDateTime, EWSTimeZone, Configuration, NTLM, GSSAPI, CalendarItem, Message, Mailbox, Attendee, Q, ExtendedProperty, FileAttachment, ItemAttachment, HTMLBody, Build, Version, FolderCollection

import os
import requests

from urllib.parse import urlparse

from bs4 import BeautifulSoup

pem_path = os.path.join(os.getcwd(), 'wistronits-com-chain.pem')
class RootCAAdapter(requests.adapters.HTTPAdapter):
    # An HTTP adapter that uses a custom root CA certificate at a hard coded location
    def cert_verify(self, conn, url, verify, cert):
        cert_file = {
            'mapi.wistronits.com': pem_path
            }[urlparse(url).hostname]
        super(RootCAAdapter, self).cert_verify(conn=conn, url=url, verify=cert_file, cert=cert)

# Tell exchangelib to use this adapter class instead of the default
BaseProtocol.HTTP_ADAPTER_CLS = RootCAAdapter

credentials = Credentials(username='straker_watcher@wistronits.com', password='jo3tj;4bj03wu3')
config = Configuration(server='mapi.wistronits.com', credentials=credentials, auth_type=NTLM)
account = Account('straker_watcher@wistronits.com',  credentials=credentials, config=config, autodiscover=False)

for item in account.inbox.all().order_by('-datetime_received')[:2]:
    # print(item.subject, item.sender, item.datetime_received)
    print("?????")
    print(item.subject)
    # print(type(item.body))
    # soup = BeautifulSoup(item.body, 'lxml')
    # #print(soup.get_text())
    # for link in soup.find_all('a'):
    #     print(link)
    #     if ('https://translator.strakertranslations.com/o/?action=purchaseorder' in link.get(
    #             'href')):
    #         accept_url = link.get('href')
    #         print(accept_url)
    #         break


# print(account.root.tree())
temp_save = (account.root / '資訊存放區頂端' / '封存')
#
# for item in temp_save.all().order_by('-datetime_received')[:1]:
#     print(item.subject)
#     print(item.body )

# account.inbox.all().move(to_folder = temp_save)

num = account.inbox.all().count()
import time
start = time.time()
c = 0
while(True):
    print("checking")
    account.inbox.refresh()
    print(account.inbox.all().count())
    c += 1
    if(account.inbox.all().count() > num):
        print("NEW MESSAGE!!!")
        num = account.inbox.all().count()
        print(account.inbox.all().order_by('-datetime_received')[-1].subject )


    if(time.time() - start >= 1):
        break

print("c = ", c)
