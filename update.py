from multiprocessing.pool import ThreadPool
import re
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import threading
sem = threading.Semaphore()

path = os.path.abspath(os.getcwd())
print(path)

f = open(path + "/errorLinks.txt", "a")

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

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

def Diff(first, second):
    return list(set(first) - set(second))

def updateDb(productId, price, totalPrice, sizes):
    print('sem', productId)
    sem.acquire()
    try:
        mycursor.execute("select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s", [productId])
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        print(beforeSizes)

        print(Diff(sizes, beforeSizes)) #sizes to insert
        print(Diff(beforeSizes, sizes)) #sizes to update available = 0
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)

        if(len(sizesToInsert)):
          print('sizesToInsert', productId)
          for size in sizesToInsert:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        if(len(sizezToUpdate)):
          print('sizezToUpdate', productId)
          for size in sizezToUpdate:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        mycursor.execute("UPDATE products SET price=%s, totalPrice = %s where productId = %s", [price, totalPrice, productId])
        mydb.commit()
        sem.release()
        print('sem rel', productId)

    except Exception as e: 
        print("error")
        print(productId)
        print(e)
        print("error end")
        f.write(str("update error" + str(productId)) + '\n')

        sem.release()
        print('sem rel', productId)


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    db="annencov",
    password="sarisco123"
)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("select productId, link, brandId from products where brandId = 3")

products = mycursor.fetchall()
# print(products)
def df_loops(link):
    if(link['brandId'] == 15 or link['brandId'] == 235):
        print("\n\n******** NIKE *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': '',
        'origin': 'https://www.nike.com'
        }

        try:
            
            s = requests.Session()
            URL = link['link']
            page = s.get(URL, headers=headers)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            details = ''
            for script in scripts:
                if(script.text.find("INITIAL_REDUX_STATE") != -1):
                    details = script.text
            styleNum = URL.split('/')[-1]
            details = details.replace('window.INITIAL_REDUX_STATE=', '')
            details = details[0:-1]
            jsonDetails = json.loads(details)
            price = jsonDetails['Threads']['products'][styleNum]['currentPrice']
            allSizes = jsonDetails['Threads']['products'][styleNum]['skus']
            availableSizes = jsonDetails['Threads']['products'][styleNum]['availableSkus']
            availableSizesInNumber = []
            for size in allSizes:
                for asize in availableSizes:
                    if(size['skuId'] == asize['id']):
                        availableSizesInNumber.append(size['localizedSize'])
            price = extractPrice(str(price), ',')

            updateDb(link['productId'], price, price, availableSizesInNumber)
        except Exception as e: 
            print(link)
            f.write(str(link['link']) + '****' + str(link['productId']) + '\n')
            print(e)
            print("**")

    elif(link['brandId'] == 3):
        print("\n\n******** NEWBALANCE *********\n\n")
        
        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            product = soup.find_all("h1", class_="emos_H1")
            price = soup.find(id="ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00_lblSatisFiyat").text.strip()
            cloudId = URL.split("/")[-1]
            cloudId = cloudId.split("-")[-1].replace(".html", "")
            extPrice = extractPrice(price)
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


            updateDb(link['productId'], extPrice, extPrice, realSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")
    
    elif(link['brandId'] == 55):
        print("\n\n******** REEBOK *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")

            price = soup.find_all("span", class_="gl-price__value")
            if(price[0]):
                mainPrice = extractPrice(price[0].text.strip())
            if(price[1]):
                mainTotalPrice = extractPrice(price[1].text.strip())

            sizes = soup.find("div", class_="size-options").find_all("option")
            realSizes = []
            for size in sizes:
                realSizes.append(size.text.strip().replace(',','.'))


            updateDb(link['productId'], mainTotalPrice, mainPrice, realSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")

    elif(link['brandId'] == 25):
        print(link)
        print("\n\n******** ADIDAS *********\n\n")
        adiheaders = {
          'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }
        s = requests.Session()
        URL = link['link']
        print(URL)
        try:
            styleNum = URL.split('/')[-1]
            styleNum = re.findall("^(.*?)\.html", styleNum)[0]
            page = s.get(URL, headers=adiheaders)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            details = ''
            for script in scripts:
                if(script.text.find("@context") != -1):
                    details = script.text
            # print(details)
            details = json.loads(details)
            sizes = requests.get("https://www.adidas.com.tr/api/products/"+ styleNum + "/availability?sitePath=en", headers=adiheaders)
            filtered = list(filter(lambda var: var["availability_status"] == "IN_STOCK", sizes.json()["variation_list"]))
            mappedSizes = list(map(lambda x: x["size"], filtered))
            price = extractPrice(str(details["offers"]["price"]))
            print(link['productId'], price, price, mappedSizes)
            updateDb(link['productId'], price, price, mappedSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")
    
    elif(link['brandId'] == 45):
        print("\n\n******** PUMA *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")

            price = extractPrice(soup.find("span", class_="price").text.strip())
            color = soup.find("span", class_="colors__text-name").text.strip()
            details = ''
            scripts = soup.find_all("script")
            for script in scripts:
                if(script.text.find("spConfig") != -1):
                  details = json.loads(script.text)
            allColors = details["#product_addtocart_form"]["configurable"]["spConfig"]["attributes"]["93"]["options"]
            allSizes = details["#product_addtocart_form"]["configurable"]["spConfig"]["attributes"]["141"]["options"]
            founded = next(x for x in allColors if x["label"] == color)
            foundedSizes = []
            for size in allSizes:
                for pr in size["products"]:
                    if(founded["products"].count(pr) != 0):
                        foundedSizes.append(size["label"])

            updateDb(link['productId'], price, price, foundedSizes)

        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")
    
    elif(link['brandId'] == 65):
        print("\n\n******** ASICS *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")

            price = extractPrice(soup.find("span", class_="pPrice").text.strip())

            mappedSizes = []
            sizes = soup.find("div", class_="cl-size-input-container").find_all("span", class_="custom-control-description")
            for size in sizes:
                try:
                    mappedSizes.append(size.text.strip())
                except KeyError:
                    continue
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")

        updateDb(link['productId'], price, price, mappedSizes)
      
    elif(link['brandId'] == 75):
        print("\n\n******** salomon *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")

            price = extractPrice(soup.find("div", class_="product__content--price").text.strip(), ',')

            mappedSizes = []
            sizes = soup.find("select", class_="js-variants-select").find_all("option")
            for size in sizes:
                try:
                    if(len(size["class"]) == 0):
                        mappedSizes.append(size.text.strip())
                except KeyError:
                        continue
            updateDb(link['productId'], price, price, mappedSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")

   
    elif(link['brandId'] == 115):
        print("\n\n******** mizuno *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': '',
        'origin': 'https://www.mizunotr.com'
        }
        try: 
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            sizes = soup.find_all("div", class_="pos-r fl col-12 ease variantList var-new")[0]
            realSize = sizes.find_all("a")
            mappedSizes = []
            for size in realSize:
                mappedSizes.append(size.text.strip())
            price = extractPrice(soup.find("span", class_="product-price").text.strip())

            updateDb(link['productId'], price, price, mappedSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")

    elif(link['brandId'] == 95):
        print("\n\n******** timberland *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }

        try:
            s = requests.Session()
            URL = link['link']
            page = s.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            
            price = extractPrice(soup.find("span", class_="one-price").text.strip())

            mappedSizes = []
            sizes = soup.find("div", class_="size-options").find_all("a", class_="")
            for size in sizes:
                try:
                    mappedSizes.append(size.text.strip())
                except KeyError:
                    continue
            updateDb(link['productId'], price, price, mappedSizes)
        except Exception as e: 
            f.write(str(link['link']) + '\n')
            print(link)
            print(e)
            print("**")

    time.sleep(2)
           
           
           

df = []

links = [products[i:i + 10] for i in range(0, len(products), 10)]

for chLink in links:
    with ThreadPool(10) as pool:
        for result in pool.map(df_loops, chLink):
            df.append(result)
    # time.sleep(10)

print(df)
f.close()



    
        

