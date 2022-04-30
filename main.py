from multiprocessing.pool import ThreadPool
import re
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
import time
import threading
sem = threading.Semaphore()

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

def insertIntoDb(link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = %s", [link['brand']])
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (title, price, totalPrice, styleNum, 1, brandId[0]['id'], link['mainAndCategId'], link['typeId'], link['id'], link['colorId'], link['sColorId'])
        mycursor.execute(sql, val)
        mydb.commit()

        mycursor.execute("SELECT LAST_INSERT_ID() as insertedId")
        insertedId = mycursor.fetchall()
        insertedId = insertedId[0]['insertedId']
        for size in availableSizesInNumber:
            mycursor.execute("SELECT sizeId from size where size = %s", [size])
            sizeId = mycursor.fetchall()
            mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], insertedId])
            mydb.commit()
        
        for image in mappedImages:
            mycursor.execute("INSERT INTO images(imageUrl, productId) VALUES (%s, %s)", [image, insertedId])
            mydb.commit()

        mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, link['id']])
        mydb.commit()
        sem.release()
    except Exception as e: 
        print("error")
        print(link)
        print(e)
        sem.release()

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    db="annencov",
    password="sarisco123"
)

mycursor = mydb.cursor(dictionary=True)

mycursor.execute("select * from links where inserted = 0")

links = mycursor.fetchall()
# print(links)
def df_loops(link):
    if(link['brand'] == 'nike' or link['brand'] == 'nike jordan'):
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
            images = jsonDetails['Threads']['products'][styleNum]['nodes'][0]['nodes']
            mappedImages = list(map(lambda x: x["properties"]['squarishURL'].replace('t_default', 't_PDP_1280_v1/f_auto,q_auto:eco'), images))
            price = jsonDetails['Threads']['products'][styleNum]['currentPrice']
            allSizes = jsonDetails['Threads']['products'][styleNum]['skus']
            availableSizes = jsonDetails['Threads']['products'][styleNum]['availableSkus']
            title = jsonDetails['Threads']['products'][styleNum]['title']
            availableSizesInNumber = []
            for size in allSizes:
                for asize in availableSizes:
                    if(size['skuId'] == asize['id']):
                        availableSizesInNumber.append(size['localizedSize'])
            price = extractPrice(str(price), ',')

            insertIntoDb(link, title, price, price, styleNum, availableSizesInNumber, mappedImages)
        except Exception as e: 
            print(link['link'])
            print(e)
            print("**")

    elif(link['brand'] == 'new balance'):
        print("\n\n******** NEWBALANCE *********\n\n")
        
        s = requests.Session()
        URL = link['link']
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


        insertIntoDb(link, title, extPrice, extPrice, styleNum.split(" ")[-1], realSizes, mappedImages)
    
    elif(link['brand'] == 'reebok'):
        print("\n\n******** REEBOK *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }


        s = requests.Session()
        URL = link['link']
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")

        images = soup.find_all("img", class_="image-blur")
        mappedImages = []
        for image in images:
            try:
                if(image["src"]):
                    mappedImages.append(image["src"])
            except KeyError:
                continue


        title = soup.find("h1", class_="gl-heading--m mb-2px").text.strip()
        price = soup.find_all("span", class_="gl-price__value")
        if(price[0]):
            mainPrice = extractPrice(price[0].text.strip())
        if(price[1]):
            mainTotalPrice = extractPrice(price[1].text.strip())

        styleNum = soup.find("div", class_="p-info").find("p", class_="gl-label").text.strip()
        sizes = soup.find("div", class_="size-options").find_all("option")
        realSizes = []
        for size in sizes:
            realSizes.append(size.text.strip().replace(',','.'))


        insertIntoDb(link, title.replace('Ayakkabı', ''), mainTotalPrice, mainPrice, styleNum, realSizes, mappedImages)

    elif(link['brand'] == 'adidas'):
        print("\n\n******** ADIDAS *********\n\n")
        adiheaders = {
          'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }
        URL = link['link']
        try:
            styleNum = URL.split('/')[-1].replace('.html', '')
            page = requests.get(URL, headers=adiheaders)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            # for sc in script:
            #     print(sc.text, end="\n\n")
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

            insertIntoDb(link, details["name"],price, price, styleNum, mappedSizes, details["image"])
        except Exception as e: 
            print(link['link'])
            print(e)
            print("**")
    
    elif(link['brand'] == 'puma'):
        print("\n\n******** PUMA *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }


        s = requests.Session()
        URL = link['link']
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")

        images = soup.find_all("img", class_="gallery-item__img")
        mappedImages = []
        for image in images:
            try:
                if(image["src"]):
                   mappedImages.append(image["data-lazy"])
            except KeyError:
                   continue


        title = soup.find("h1", class_="page-title").text.strip()
        price = extractPrice(soup.find("span", class_="price").text.strip())
        styleNum = soup.find("div", class_="product-article").find("span", class_="product-article__value").text.strip()
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

        insertIntoDb(link, title.replace('Ayakkabı', ''), price, price, styleNum, foundedSizes, mappedImages)
    
    elif(link['brand'] == 'asics'):
        print("\n\n******** ASICS *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }


        s = requests.Session()
        URL = link['link']
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")

        images = soup.find("div", class_="swiper-wrapper").find_all("img", class_="swiper-lazy")
        mappedImages = []
        for image in images:
            try:
                if(image["src"]):
                    mappedImages.append(image["data-src"])
            except KeyError:
                    continue


        title = soup.find("span", class_="sk-model-title").text.strip()
        styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()
        price = extractPrice(soup.find("span", class_="pPrice").text.strip())

        mappedSizes = []
        sizes = soup.find("div", class_="cl-size-input-container").find_all("span", class_="custom-control-description")
        for size in sizes:
            try:
                mappedSizes.append(size.text.strip())
            except KeyError:
                continue

        insertIntoDb(link, title, price, price, styleNum.split(" ")[-1], mappedSizes, mappedImages)
      
    elif(link['brand'] == 'salomon'):
        print("\n\n******** salomon *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }


        s = requests.Session()
        URL = link['link']
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")

        images = soup.find_all("img", class_="js-fancybox-lg")
        mappedImages = []
        for image in images:
            try:
                if(image["src"]):
                    mappedImages.append(image["data-fancybox-image-lg"])
            except KeyError:
                    continue


        title = soup.find("div", class_="product__content--title").text.strip()
        price = extractPrice(soup.find("div", class_="product__content--price").text.strip(), ',')

        mappedSizes = []
        sizes = soup.find("select", class_="js-variants-select").find_all("option")
        for size in sizes:
            try:
                if(len(size["class"]) == 0):
                    mappedSizes.append(size.text.strip())
            except KeyError:
                    continue

        insertIntoDb(link, title, price, price, "", mappedSizes, mappedImages)
   
    elif(link['brand'] == 'mizuno'):
        print("\n\n******** mizuno *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': '',
        'origin': 'https://www.mizunotr.com'
        }

        s = requests.Session()
        URL = link['link']
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        product = soup.find(id="productDetail")
        tags = product.find(id="pageContent")
        images = tags.find_all("a")
        mappedImages = []
        for image in images:
            try:
                if(image["href"].find('http') != -1):
                  mappedImages.append(image["href"])
            except KeyError:
                continue
        sizes = soup.find_all("div", class_="pos-r fl col-12 ease variantList var-new")[0]
        realSize = sizes.find_all("a")
        mappedSizes = []
        for size in realSize:
            mappedSizes.append(size.text.strip())
        price = extractPrice(soup.find("span", class_="product-price").text.strip())
        styleNum = soup.find_all("span", class_="supplier_product_code")[0]
        title = soup.find(id="productName").text.strip().replace("Ayakkabı", "").replace("Spor", "").replace("Erkek", "").replace("Nubuk", "").replace("Yeşil", "").replace("Koyu", "").replace("Kadin", "")
        insertIntoDb(link, title, price, price, styleNum.text.strip(), mappedSizes, mappedImages)

    elif(link['brand'] == 'timberland'):
        print("\n\n******** timberland *********\n\n")
        headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Cookie': ''
        }


        s = requests.Session()
        URL = "https://www.timberland.com.tr/bradstreet-ultra-koyu-yesil-nubuk-erkek-spor-ayakkabi-p_127237"
        page = s.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")

        images = soup.find("div", class_="main-gallery").find_all("img", class_="image-blur")
        mappedImages = []
        for image in images:
            try:
                if(image["src"]):
                   mappedImages.append(image["data-image"])
            except KeyError:
                   continue


        title = soup.find("h1", class_="p-name").text.strip()
        # styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()
        price = extractPrice(soup.find("span", class_="one-price").text.strip())

        mappedSizes = []
        sizes = soup.find("div", class_="size-options").find_all("a", class_="")
        for size in sizes:
            try:
                mappedSizes.append(size.text.strip())
            except KeyError:
                continue
        title = title.replace("Ayakkabı", "").replace("Spor", "").replace("Erkek", "").replace("Nubuk", "").replace("Yeşil", "").replace("Koyu", "").replace("Kadin", "")
        insertIntoDb(link, title, price, price, "", mappedSizes, mappedImages)
    time.sleep(3)
           
           
           

df = []

links = [links[i:i + 10] for i in range(0, len(links), 10)]

for chLink in links:
    with ThreadPool(10) as pool:
        for result in pool.map(df_loops, chLink):
            df.append(result)
    time.sleep(2)

print(df)



    
        

