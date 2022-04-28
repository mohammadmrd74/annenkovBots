from matplotlib.style import available
from numpy import size
from regex import P
import requests
from bs4 import BeautifulSoup
import json
import pyperclip

headers = {
  'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
  'Cookie': '',
  'origin': 'https://www.nike.com'
}

s = requests.Session()
URL = "https://www.nike.com/tr/t/space-hippie-04-ayakkab%C4%B1s%C4%B1-Sdb1hD/DQ2897-001"
page = s.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
# print(soup)
scripts = soup.find_all("script")
details = ''
for script in scripts:
    if(script.text.find("INITIAL_REDUX_STATE") != -1):
        details = script.text
styleNum = URL.split('/')[-1]
details = details.replace('window.INITIAL_REDUX_STATE=', '')
details = details[0:-1]
jsonDetails = json.loads(details)
images = jsonDetails['Threads']['products'][styleNum]['nodes'][0]['nodes']
mappedImages = list(map(lambda x: x["properties"]['squarishURL'].replace('t_default', 't_PDP_1280_v1/f_auto,q_auto:eco'), images))
price = jsonDetails['Threads']['products'][styleNum]['currentPrice']
allSizes = jsonDetails['Threads']['products'][styleNum]['skus']
availableSizes = jsonDetails['Threads']['products'][styleNum]['availableSkus']
availableSizesInNumber = []
for size in allSizes:
    for asize in availableSizes:
        if(size['skuId'] == asize['id']):
            availableSizesInNumber.append(size['localizedSize'])
print(styleNum)
print(price)
print(availableSizesInNumber)
print(mappedImages)
pyperclip.copy(json.dumps(availableSizesInNumber))