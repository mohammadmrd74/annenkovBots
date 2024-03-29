from multiprocessing.pool import ThreadPool
import re
import mysql.connector
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import threading
import random
sem = threading.Semaphore()
sem1 = threading.Semaphore()

path = os.path.abspath(os.getcwd())
print(path)

mydb = mysql.connector.connect(
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
)

mycursor = mydb.cursor(dictionary=True)

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
    print("sem get", productId)
    sem.acquire()
    try:
        mycursor.execute(
            "select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s",
            [productId],
        )
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)
        print("sizesToInsert", sizesToInsert)
        print("sizezToUpdate", sizezToUpdate)
        if len(sizesToInsert):
            for size in sizesToInsert:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute("select sizeId from linkSizeAndProduct lsp where productId = %s and sizeId = %s and available = 0", [productId, sizeId[0]["sizeId"]])
                isSizeThere = mycursor.fetchall()
                if( len(isSizeThere[0]) > 0):
                    mycursor.execute(
                    "UPDATE linkSizeAndProduct SET available = 1  where sizeId = %s AND productId = %s",
                    [sizeId[0]["sizeId"], productId],
                    )
                    mydb.commit()
                else :
                    mycursor.execute(
                        "INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)",
                        [sizeId[0]["sizeId"], productId],
                    )
                    mydb.commit()

        if len(sizezToUpdate):
            #   print('sizezToUpdate', productId)
            for size in sizezToUpdate:
                mycursor.execute("SELECT sizeId from size where size = %s", [size])
                sizeId = mycursor.fetchall()
                mycursor.execute(
                    "UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s",
                    [sizeId[0]["sizeId"], productId],
                )
                mydb.commit()
        mycursor.execute("SELECT count(*) as count from linkSizeAndProduct where productId = %s and available = 1", [productId])
        availableSizes = mycursor.fetchall()
        availableSizes = availableSizes[0]["count"]
        print(type(availableSizes))
        if(availableSizes == 0):
            print(availableSizes)
            mycursor.execute(
                "UPDATE products SET price=%s, totalPrice = %s,  active=0 where productId = %s",
                [price, totalPrice, productId],
            )
        else: 
            mycursor.execute(
                "UPDATE products SET price=%s, totalPrice = %s,  active=1 where productId = %s",
                [price, totalPrice, productId],
            )
        mydb.commit()
        sem.release()
        print("sem rel", productId)

    except Exception as e:
        print(e)
        f.write(str("update error" + str(productId)) + "\n")

        sem.release()

    print('sem get', productId)
    sem.acquire()
    try:
        mycursor.execute("select size from size join linkSizeAndProduct lsp on size.sizeId = lsp.sizeId where productId = %s", [productId])
        beforeSizes = mycursor.fetchall()
        beforeSizes = list(map(lambda x: x["size"], beforeSizes))
        # print(Diff(sizes, beforeSizes)) #sizes to insert
        # print(Diff(beforeSizes, sizes)) #sizes to update available = 0
        sizesToInsert = Diff(sizes, beforeSizes)
        sizezToUpdate = Diff(beforeSizes, sizes)

        if(len(sizesToInsert)):
        #   print('sizesToInsert', productId)
          for size in sizesToInsert:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("INSERT INTO linkSizeAndProduct(sizeId, productId) VALUES (%s, %s)", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        if(len(sizezToUpdate)):
        #   print('sizezToUpdate', productId)
          for size in sizezToUpdate:
              mycursor.execute("SELECT sizeId from size where size = %s", [size])
              sizeId = mycursor.fetchall()
              mycursor.execute("UPDATE linkSizeAndProduct SET available = 0 where sizeId = %s AND productId = %s", [sizeId[0]['sizeId'], productId])
              mydb.commit()

        mycursor.execute("UPDATE products SET price=%s, totalPrice = %s,  active=1 where productId = %s", [price, totalPrice, productId])
        mydb.commit()
        sem.release()
        print('sem rel', productId)

    except Exception as e:
        print(e)
        f.write(str("update error" + str(productId)) + '\n')

        sem.release()

def disableProduct(id):
    print('disableProduct', id)
    sem.acquire()
    mycursor.execute("UPDATE products SET active=0 where productId = %s", [id])
    mydb.commit()
    sem.release()




def insertIntoDb():
    return 1


TYPE = 'update'
  
def df_loops(link):
    print(link)
    sucess = True
    mycursor.execute("select productId, link, brandId, (select brandName from brands where id = brandId) as brand from products where productId = %s", [link])

    link = mycursor.fetchall()
    print(link)
    link = link[0]
    print(link)
    if link["brand"] == "nike" or link["brand"] == "jordan":
        print("\n\n******** " + link["brand"] + " *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "origin": "https://www.nike.com/tr",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        }

        try:
            URL = link["link"]
            s = requests.Session()
            page = s.get(URL, headers=headers, timeout=10)
            soup = BeautifulSoup(page.content, "html.parser")


            mains = soup.find("script", id="__NEXT_DATA__").text.strip()

            fstyleNum = (
                soup.find("li", class_="description-preview__style-color ncss-li")
                .text.strip()
                .replace("Stil: ", "")
            )

            jsonDetails = json.loads(mains)["props"]["pageProps"]["initialState"]
            styleNum = fstyleNum
            if fstyleNum not in jsonDetails["Threads"]["products"]:
                urlst = URL.strip().split("/")[-1]
                if urlst in jsonDetails["Threads"]["products"]:
                    styleNum = urlst
                else:
                    styleNum = list(jsonDetails["Threads"]["products"].keys())[0]

            images = jsonDetails["Threads"]["products"][styleNum]["nodes"][0]["nodes"]

            mappedImages = list(
                map(
                    lambda x: x["properties"]["squarishURL"].replace(
                        "t_default", "t_PDP_1280_v1/f_auto,q_auto:eco"
                    )
                    if ("squarishURL" in x["properties"])
                    else None,
                    images,
                )
            )
            mappedImages = list(filter(None, mappedImages))
            price = jsonDetails["Threads"]["products"][styleNum]["currentPrice"]
            fullPrice = jsonDetails["Threads"]["products"][styleNum]["fullPrice"]
            allSizes = jsonDetails["Threads"]["products"][styleNum]["skus"]
            availableSizes = jsonDetails["Threads"]["products"][styleNum]["availableSkus"]
            title = jsonDetails["Threads"]["products"][styleNum]["title"]
            availableSizesInNumber = []
            for size in allSizes:
                for asize in availableSizes:
                    if size["skuId"] == asize["id"]:
                        availableSizesInNumber.append(size["localizedSize"])
            price = extractPrice(str(price), ",")
            fullPrice = extractPrice(str(fullPrice), ",")

         
            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    fullPrice + 60,
                    price + 60,
                    fstyleNum,
                    availableSizesInNumber,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], fullPrice + 60, price + 60, availableSizesInNumber)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "new balance":
        print("\n\n******** NEWBALANCE *********\n\n")

        s = requests.Session()
        URL = link["link"]
        try:
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")
            product = soup.find_all("h1", class_="emos_H1")
            title = product[0].text.strip()
            price = extractPrice(
                soup.find(
                    id="ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00_lblSatisFiyat"
                ).text.strip()
            )
            morePrice = price
            if soup.find(id="plhSatisIlkFiyat").text:
                morePrice = extractPrice(soup.find(id="plhSatisIlkFiyat").text.strip())
            cloudId = URL.strip().split("/")[-1]
            cloudId = cloudId.split("-")[-1].replace(".html", "")

            styleNum = soup.find("div", class_="ems-prd-sort-desc").text.strip()
            tags = soup.find_all("ul", class_="swiper-wrapper slide-wrp")[0]
            images = tags.find_all("a")
            mappedImages = []
            for image in images:
                try:
                    if image["data-large"]:
                        mappedImages.append(image["data-large"])
                except KeyError:
                    continue

            sizes = page = s.get(
                "https://www.newbalance.com.tr/usercontrols/urunDetay/ajxUrunSecenek.aspx?urn="
                + cloudId
                + "&fn=dty&std=True&type=scd1&index=0&objectId=ctl00_u23_ascUrunDetay_dtUrunDetay_ctl00&runatId=urunDetay&scd1=0&lang=tr-TR"
            )
            soup = BeautifulSoup(page.content, "html.parser")
            realSizes = []
            sizes = soup.find_all("a")
            for size in sizes:
                try:
                    if size["class"] and size["class"].count("stokYok") != 0:
                        continue
                    else:
                        realSizes.append(size.text.strip())
                except KeyError:
                    realSizes.append(size.text.strip())
            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    morePrice,
                    price,
                    styleNum.split(" ")[-1],
                    realSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], morePrice, price, realSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "reebok":
        print("\n\n******** REEBOK *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try: 
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="image-blur")
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(image["src"])
                except KeyError:
                    continue

            title = soup.find("h1", class_="gl-heading--m mb-2px").text.strip()
            price = soup.find_all("span", class_="gl-price__value")
            if price[0]:
                mainPrice = extractPrice(price[0].text.strip())
            if price[1]:
                mainTotalPrice = extractPrice(price[1].text.strip())

            styleNum = (
                soup.find("div", class_="p-info").find("p", class_="gl-label").text.strip()
            )
            sizes = soup.find("div", class_="size-options").find_all("option")
            realSizes = []
            for size in sizes:
                realSizes.append(size.text.strip().replace(",", "."))

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title.replace("Ayakkabı", ""),
                    mainTotalPrice,
                    mainPrice,
                    styleNum,
                    realSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], mainTotalPrice, mainPrice, realSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "adidas":
        print("\n\n******** ADIDAS *********\n\n")
        adiheaders = {
            "origin": "www.adidas.com.tr",
            "cookie": "",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
        }
        URL = link["link"]

        try:
            styleNum = URL.split("/")[-1]
            styleNum = re.findall("^(.*?)\.html", styleNum)[0]
            print(URL)
            page = requests.get(URL.strip(), headers=adiheaders)
            print(page)
            soup = BeautifulSoup(page.content, "html.parser")
            scripts = soup.find_all("script")
            # for sc in script:
            #     print(sc.text, end="\n\n")
            details = ""
            for script in scripts:
                if script.text.find("@context") != -1:
                    details = script.text
            # print(details)
            details = json.loads(details)
            sizes = requests.get(
                "https://www.adidas.com.tr/api/products/"
                + styleNum
                + "/availability?sitePath=en",
                headers=adiheaders,
            )
            filtered = list(
                filter(
                    lambda var: var["availability_status"] == "IN_STOCK",
                    sizes.json()["variation_list"],
                )
            )
            mappedSizes = list(map(lambda x: x["size"], filtered))
            price = str(details["offers"]["price"])
            morePrice = price
            if soup.find("div", class_="gl-price-item--crossed"):
                morePrice = extractPrice(
                    soup.find("div", class_="gl-price-item--crossed").text.strip()
                )
            print(price)

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    details["name"].replace("Ayakkabı", ""),
                    morePrice,
                    price,
                    styleNum,
                    mappedSizes,
                    details["image"],
                )
            else:
                updateDb(link["productId"], morePrice, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print(link["link"])
            print(e)
            print("**")

    elif link["brand"] == "puma":
        print("\n\n******** PUMA *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="gallery-item__img")

            mappedImages = []
            for image in images:
                try:
                    if image["src"] and not image.has_attr("data-lazy"):
                        mappedImages.append(image["src"])
                    elif image["data-lazy"]:
                        mappedImages.append(image["data-lazy"])
                except KeyError:
                    continue

            title = soup.find("h1", class_="page-title").text.strip()
            prices1 = soup.find_all("span", class_="price")[0].text.strip()
            prices2 = soup.find_all("span", class_="price")[1].text.strip()
            prices1 = extractPrice(prices1)
            prices2 = extractPrice(prices2)
            price = extractPrice(soup.find("span", class_="price").text.strip())
            if prices1 is None or prices2 is None:
                prices1 = price
                prices2 = price
            styleNum = (
                soup.find("div", class_="product-article")
                .find("span", class_="product-article__value")
                .text.strip()
            )
            color = soup.find("span", class_="colors__text-name").text.strip()
            details = ""
            scripts = soup.find_all("script")
            for script in scripts:
                if script.text.find("spConfig") != -1:
                    details = json.loads(script.text)
            allColors = details["#product_addtocart_form"]["configurable"]["spConfig"][
                "attributes"
            ]["93"]["options"]
            allSizes = details["#product_addtocart_form"]["configurable"]["spConfig"][
                "attributes"
            ]["141"]["options"]
            founded = next(x for x in allColors if x["label"] == color)
            foundedSizes = []
            for size in allSizes:
                for pr in size["products"]:
                    if founded["products"].count(pr) != 0:
                        foundedSizes.append(size["label"])

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title.replace("Ayakkabı", ""),
                    prices2,
                    prices1,
                    styleNum,
                    foundedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], prices2, prices1, foundedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("asics")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "asics":
        print("\n\n******** ASICS *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find("div", class_="swiper-wrapper").find_all(
                "img", class_="swiper-lazy"
            )
            mappedImages = []
            for image in images:
                try:
                    if image["src"]:
                        mappedImages.append(image["data-src"])
                except KeyError:
                    continue

            title = soup.find("span", class_="sk-model-title").text.strip()
            styleNum = soup.find("span", class_="sk-model-alt-title").text.strip()
            price = (0,)
            morePrice = 0
            if len(soup.find_all("span", class_="pPrice")) == 2:
                price = extractPrice(
                    soup.find_all("span", class_="pPrice")[1].text.strip()
                )
                morePrice = extractPrice(
                    soup.find_all("span", class_="pPrice")[0].text.strip()
                )
            else:
                price = extractPrice(
                    soup.find_all("span", class_="pPrice")[0].text.strip()
                )
                morePrice = price

            mappedSizes = []
            sizes = soup.find("div", class_="cl-size-input-container").find_all("label")

            # print(sizes)
            for size in sizes:
                try:
                    if size["data-stock"] != "0":
                        mappedSizes.append(size.text.strip())
                except KeyError:
                    continue

            if (TYPE != "update"):
                insertIntoDb(
                    link,
                    title,
                    morePrice,
                    price,
                    styleNum.split(" ")[-1],
                    mappedSizes,
                    mappedImages,
                )
            else:
                updateDb(link["productId"], morePrice, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("asics")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "salomon":
        print("\n\n******** salomon *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")

            images = soup.find_all("img", class_="cloudzoom")
            mappedImages = []
            for image in images:
                try:
                    if(image["src"]):
                        mappedImages.append("https://www.salomon.com.tr/" + image["src"])
                except KeyError:
                        continue


            title = soup.find("div", class_="ProductName").text.strip()
            price = extractPrice(soup.find("span", class_="spanFiyat").text.strip(), '.')
            styleNum = soup.find("span", class_="productcode").text.strip().replace('(', '').replace(')','')
            mappedSizes = []
            scripts = soup.find("body").find_all("script")[0].text.strip()
            scripts = json.loads(scripts[scripts.find('{'):(scripts.find(';'))])
            filtered = list(filter(lambda var: var["stokAdedi"] > 0 and var["ekSecenekTipiTanim"] == "Beden", scripts["productVariantData"]))
            sizes = list(map(lambda x: x["tanim"][x["tanim"].find('(')+1:x["tanim"].find(')')], filtered))

            if (TYPE != "update"):
                insertIntoDb(link, title, price, price, "", sizes, mappedImages)
            else:
                updateDb(link["productId"], price, price, sizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("salomon")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "mizuno":
        print("\n\n******** mizuno *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
            "origin": "https://www.mizunotr.com",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
            soup = BeautifulSoup(page.content, "html.parser")
            product = soup.find(id="productDetail")
            tags = product.find(id="pageContent")
            images = tags.find_all("a")
            mappedImages = []
            for image in images:
                try:
                    if image["href"].find("http") != -1:
                        mappedImages.append(image["href"])
                except KeyError:
                    continue
            sizes = soup.find_all("div", class_="pos-r fl col-12 ease variantList var-new")[
                0
            ]
            realSize = sizes.find_all("a")
            mappedSizes = []
            for size in realSize:
                mappedSizes.append(size.text.strip())
            price = extractPrice(soup.find("span", class_="product-price").text.strip())
            styleNum = soup.find_all("span", class_="supplier_product_code")[0]
            title = (
                soup.find(id="productName")
                .text.strip()
                .replace("Ayakkabı", "")
                .replace("Spor", "")
                .replace("Erkek", "")
                .replace("Nubuk", "")
                .replace("Yeşil", "")
                .replace("Koyu", "")
                .replace("Kadin", "")
            )
            if (TYPE != "update"):
                insertIntoDb(
                    link, title, price, price, styleNum.text.strip(), mappedSizes, mappedImages
                )
            else:
                updateDb(link["productId"], price, price, mappedSizes)

        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("salomon")
            print(link)
            print(e)
            print("**")

    elif link["brand"] == "timberland":
        print("\n\n******** timberland *********\n\n")
        headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Cookie": "",
        }

        try:
            s = requests.Session()
            URL = link["link"]
            page = s.get(URL.strip())
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

            nprice = ''
            oprice = ''
            if(soup.find("span", class_="one-price")): 
                oprice = extractPrice(soup.find("span", class_="one-price").text.strip())
                nprice = oprice
            if(soup.find("span", class_="new-price")):
                nprice = extractPrice(soup.find("span", class_="new-price").text.strip())
                oprice = extractPrice(soup.find("span", class_="old-price").text.strip())

            print(nprice)
            print(oprice)

            mappedSizes = []
            sizes = soup.find("div", class_="size-options").find_all("a", class_="")
            for size in sizes:
                try:
                    mappedSizes.append(size.text.strip())
                except KeyError:
                    continue
            title = title.replace("Ayakkabı", "").replace("Spor", "").replace("Erkek", "").replace("Nubuk", "").replace("Yeşil", "").replace("Koyu", "").replace("Kadin", "")
            if (TYPE != "update"):
                insertIntoDb(link, title, oprice, nprice, "", mappedSizes, mappedImages)
            else:
                updateDb(link["productId"], oprice, nprice, mappedSizes)
        except Exception as e:
            sucess = False
            if (TYPE == "update"):
                disableProduct(link['productId'])
                f.write(str(link['link']) + '\n')
            print("timberland error")
            print(link)
            print(e)
            print("**")

    time.sleep(3)
    mycursor.execute("SELECT * from products where productId = %s", [link["productId"]])
    productupdate = mycursor.fetchall()
    print('ended')
    if (sucess == False): return False;
    return productupdate[0]
  
        

