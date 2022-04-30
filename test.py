from joblib import PrintTime
from matplotlib import style
from matplotlib.style import available
from numpy import size
import decimal
from regex import P
import requests
from bs4 import BeautifulSoup

import json
import re
import pyperclip

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


print("\n\n******** NEWBALANCE *********\n\n")
        
s = requests.Session()
URL = "https://www.newbalance.com.tr/urun/new-balance-520-411182.html"
page = s.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
product = soup.find_all("h1", class_="emos_H1")
title = product[0].text.strip()
price = soup.find(id="ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00_lblSatisFiyat").text.strip()
cloudId = URL.split("/")[-1]
cloudId = cloudId.split("-")[-1].replace(".html", "")
extPrice = extractPrice(price)
styleNum = soup.find("div", class_="ems-prd-sort-desc").text.strip()
tags = soup.find_all("ul", class_="swiper-wrapper slide-wrp")[0]
images = tags.find_all("a")
mappedImages = []
for image in images:
    try:
        if(image["data-large"]):
            mappedImages.append(image["data-large"])
    except KeyError:
        continue

sizes = page = s.get("https://www.newbalance.com.tr/usercontrols/urunDetay/ajxUrunSecenek.aspx?urn="+cloudId+"&fn=dty&std=True&type=scd1&index=0&objectId=ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00&runatId=urunDetay&scd1=0&lang=tr-TR")
soup = BeautifulSoup(page.content, "html.parser")
realSizes = []
sizes = soup.find_all("a")
for size in sizes:
    try:
        if(size["class"] and size["class"].count("stokYok") != 0):     
            continue
        else:
            realSizes.append(size.text.strip())
    except KeyError:
        realSizes.append(size.text.strip())

print(title)
print(extPrice)
print(realSizes)
print(mappedImages)
print(styleNum.split(" ")[-1])