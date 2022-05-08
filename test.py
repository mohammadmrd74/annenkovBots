from joblib import PrintTime
from matplotlib import style
from matplotlib.style import available
from numpy import size
import decimal
from regex import P
import requests
import mysql.connector
from bs4 import BeautifulSoup
import threading
sem = threading.Semaphore()

import json
import re
import pyperclip

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    db="annencov",
    password="sarisco123"
)

mycursor = mydb.cursor(dictionary=True)


def Diff(first, second):
    return list(set(first) - set(second))

def updateDb(productId, price, totalPrice, sizes):
    sem.acquire()
    try:
        print(productId)
        mycursor.execute("select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s", [productId])
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        print(beforeSizes)

        print(Diff(sizes, beforeSizes)) #sizes to insert
        print(Diff(beforeSizes, sizes)) #sizes to update available = 0
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)

        if(len(sizesToInsert)):
          for size in sizesToInsert:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        if(len(sizezToUpdate)):
          for size in sizezToUpdate:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        mycursor.execute("UPDATE products SET price=%s, totalPrice = %s where productId = %s", [price, totalPrice, productId])
        mydb.commit()
        sem.release()
    except Exception as e: 
        print("error")
        print(productId)
        print(e)
        sem.release()


def extractPrice(price, sep='.'):
  r = re.compile(r'(\d[\d.,]*)\b')
  if(sep == ','):
    extPrice = [x for x in re.findall(r, price)][0]
    if(extPrice.find('.') != -1):
      extPrice = int(extPrice.split('.')[0]) + 1
  else:
    extPrice = [x.replace('.', '') for x in re.findall(r, price)][0]
    if(extPrice.find(',') != -1):
      extPrice = int(extPrice.split(',')[0]) + 1
  
  return extPrice

headers = {
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
'Cookie': '',
'origin': 'https://www.nike.com'
}

# mycursor.execute("select * from products where productId = 124")
 
# products = mycursor.fetchall()

# try:
s = requests.Session()
URL = 'https://www.nike.com/tr/u/custom-nike-air-zoom-pegasus-flyease-by-you-10001267/2943873055'


# s = requests.Session()
# URL =  'https://www.timberland.com.tr/bradstreet-ultra-gri-nubuk-erkek-spor-ayakkabi-p_127238'
page = s.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
page = s.get(URL, headers=headers)
soup = BeautifulSoup(page.content, "html.parser")
scripts = soup.find_all("script")
details = ''
for script in scripts:
    if(script.text.find("INITIAL_REDUX_STATE") != -1):
        details = script.text
fstyleNum = soup.find("li", class_="description-preview__style-color ncss-li").text.strip().replace('Stil: ', '')
styleNum = ''
details = details.replace('window.INITIAL_REDUX_STATE=', '')
details = details[0:-1]
pyperclip.copy(details)
jsonDetails = json.loads(details)
if(fstyleNum not in jsonDetails['Threads']['products']):
    urlst = URL.split('/')[-1]
    print(urlst)
    if(urlst in jsonDetails['Threads']['products']):
        styleNum = urlst
    else:
        styleNum = list(jsonDetails['Threads']['products'].keys())[0]
    
print(styleNum)
price = jsonDetails['Threads']['products'][styleNum]['currentPrice']
print(price)
fullPrice = jsonDetails['Threads']['products'][styleNum]['fullPrice']
allSizes = jsonDetails['Threads']['products'][styleNum]['skus']
availableSizes = jsonDetails['Threads']['products'][styleNum]['availableSkus']
availableSizesInNumber = []
for size in allSizes:
    for asize in availableSizes:
        if(size['skuId'] == asize['id']):
            availableSizesInNumber.append(size['localizedSize'])
price = extractPrice(str(price), ',')
fullPrice = extractPrice(str(fullPrice), ',')
# print(mappedSizes)
# print(title)
print(price)
# print(mappedImages)
# except Exception as e: 
#     # f.write(str(link['link']) + '\n')
#     # print(link)
#     print(e)
#     # print("**")

