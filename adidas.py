
from locale import normalize
import requests
import mysql.connector
from bs4 import BeautifulSoup
import threading
sem = threading.Semaphore()

import json
import re
import pyperclip

mydb = mysql.connector.connect(
    host="171.22.24.215", user="anenkov", db="annenkovstore", password="anenanenkovkov"
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

def insertIntoDb(link, title, price, totalPrice, styleNum, availableSizesInNumber, mappedImages):
    sem.acquire()
    try:
        mycursor.execute("SELECT id from brands where brandName = 'adidas'")
        brandId = mycursor.fetchall()
        sql = "INSERT INTO products (title, price, totalPrice, styleNumber, currencyId, brandId, mainAndCategoryId, typeId, linkId, link, colorId, sColorId) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (title, price, totalPrice, styleNum, 1, brandId[0]['id'], 4, 1, 1, link,3, 2)
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

        mycursor.execute("UPDATE links SET inserted=%s where id = %s", [1, 1])
        mydb.commit()
        sem.release()
    except Exception as e: 
        print("error")
        print(link)
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

adiheaders = {
    'origin': 'www.adidas.com.tr',
    'cookie': '',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}


# curl 'https://www.adidas.com/us/predator-edge.1-firm-ground-cleats/H02933.html' \
#   -H 'authority: www.adidas.com' \
#   -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
#   -H 'accept-language: en-US,en;q=0.9,fa;q=0.8,de;q=0.7' \
#   -H 'cache-control: max-age=0' \
#   -H 'cookie: geo_ip=23.88.57.107; onesite_country=US; akacd_Phased_www_adidas_com_Generic=3838949924~rv=15~id=b28afbb494af8abfb53eacd1b6bb4f1c; akacd_phased_PDP=3838949924~rv=25~id=22b86e8d967533b5ff0b0ffb5eb5e3b6; glass-canary=baseline|1|baseline; bm_sz=0056D1CBC6CBD0FE09883DB22885DFB1~YAAQFFgDF4prwsmCAQAAjC3y2BAjDyQj4xvTMp1DkEcOrRFDhDNSeI5nOaYi3pU5wF/G5uPeI2hqggqhR7R7jyLO9CmHhiZ4/EyC4Xezu43HTbao7iYTCwZXor9oKUPgn86t49g0EtX7d3T7E7f3dSueMSGHFTKyA3dG3ogwIoHS6j1or7PVkzIofsmWsJ+o/YxCYS6VA976rDMtrRJ8Mfu2b+4uECByaFI5unSARn5fFh9DoQaJPewvHncDgGuT18f+GXNKS+W1IloaeNhNGfqHtzWOaxIIX3LiSPEgLql0Zi0AP5OYEGU+VvmBjsWIzkW651CB1G04rGzvFFE3Mhn61SashEoq536sZnJn8n4yItzoIHC1JxzQ3ESYxZsC5lFnmCYsXC6Mu69cW0BtzQ==~3491397~4473143; ak_bmsc=A8A07BF2C85D2FD02CC689A93029054D~000000000000000000000000000000~YAAQFFgDF8drwsmCAQAAUzvy2BArumrWZGiJS7hoTnhLU1V7GIU36WF4zT2cwngGI0bbVjXu2kAbmx1roAVHseKNH/9YsRXNR32+nqV/7OwFW+bk9M4HJg1tW8mKsfBRPxngd4mKkRYhY1MtLM/iCfTe8FobD2gXxFwwOyz1UEvEc8LjNdJ4TCc4m6TYp9o4+xOSEY+li+Z3WU1VtCdfrFZWsfJoEGZAk0sAFCDxlI3rgs2BXYD0ppwU/kx1F27BKKdV0JruzaE7D7p3IkBK2wO9R0ULM1FJC5srgsoQAIU3VxCOZq8Sp05uDLwqKo+ArsazsbT10VpJ4CvOWQlasJ5Raew0Yq+XVWYr/RLzcqeNHoOxeLXmbAdDMDygt0CyP0/rNXoAPDLIn4tl2jsmYiOBoGLCaJQqrxS1iUXCcnxJYkaJquOdgE7bTUuDPstpFIMo56F71QG0xNZkzUiZhDXlxhLsqYX77QwPy7agv0EZb4n13mJJyak=; isHomePageStartCurtainOpened=false; persistentBasketCount=0; userBasketCount=0; newsletterShownOnVisit=false; notice_preferences=2; badab=false; akacd_phased_PLP=3838949956~rv=88~id=971786b1387b6cb7fad3758e72a54dc8; mt.v=5.825523053.1661497202275; ab_qm=b; _gid=GA1.2.334108434.1661497210; _gcl_au=1.1.1830130951.1661497210; AMCVS_7ADA401053CCF9130A490D4C%40AdobeOrg=1; s_cc=true; _scid=a1d8e639-e117-4ef7-a57b-80ef5c1a9bef; AMCV_7ADA401053CCF9130A490D4C%40AdobeOrg=-227196251%7CMCIDTS%7C19231%7CMCMID%7C39903099673156995951556432084816710674%7CMCAID%7CNONE%7CMCAAMLH-1662102010%7C6%7CMCAAMB-1662102010%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCOPTOUT-1661504411s%7CNONE; IR_gbd=adidas.com; BVBRANDID=0b12dd54-028d-490c-b5e9-ee0be269c472; BVBRANDSID=e328d6a1-6b97-454c-aec0-41e24154229e; QSI_SI_1HBh4b3ZpUvgHMV_intercept=true; _clck=bn3mn8|1|f4c|0; _pin_unauth=dWlkPU5URTVPV0poWkdJdFpHTmtPQzAwWWpFekxXSTBOV1V0TVRNM05XTTJabVJpTkRWbA; s_sess=%5B%5BB%5D%5D; RES_TRACKINGID=274714550377680; RES_SESSIONID=282381693933240; ResonanceSegment=1; checkedIfOnlineRecentlyViewed=true; dwsid=3ArP7bHIYo042VvAicbeSiUNDn24RFwgBxG5GPc48JOV0iIDbZi-w1e8dZtNxOd5G_Xs3oUUmBVMzoyYRgVhzQ==; fallback_dwsid=3ArP7bHIYo042VvAicbeSiUNDn24RFwgBxG5GPc48JOV0iIDbZi-w1e8dZtNxOd5G_Xs3oUUmBVMzoyYRgVhzQ==; pagecontext_cookies=; pagecontext_secure_cookies=; __olapicU=a751956747c963feb96af5c6d486d7af; fita.sid.adidas=ZVm0MVa6a1u-Nk_9ZpFQ_u7lgBHyMYMZ; UserSignUpAndSave=11; geo_country=DE; geo_state=BY; geo_coordinates=lat=49.45, long=11.07; _abck=B0042B3814A42314F7099A2AE8C57329~-1~YAAQFFgDF3CgwsmCAQAAy9f+2Agcc+rLccXTzI/LT8KSudGhyGs/csyR/qpo26meAvwmf4QD73XR+Z4BEmznRwTGECKGvRszy/GVFkHXRH3sLsvzsEMKmO5A4jspxzzg4UsQXh6ubKZ1XIDaE130h1I7+NpTKzDTGMSVpVS+y9FpbxrN0RYgb5vjbKRh2EMxHF+64foI3+t/A4iBIU6gP7tb59A1Qc86qYksDXFzWz2PAK8/BFV7gL4MhwpV7n93/CD4YMKnNVkXNu8JPxymVBJHrw3T53tChF8qTlUFgfNyB4YTmjzFWHlBP8Z1H4yVoVJp+j03hWZOFRijbP4iq6OykM0pq5snGSWdUhbZEGLkPP0SbKg6DXVD/4Q2A8DpUvcNfsCcz6sqVxj3ZCqJyZ4wKTRbsqwvoi40bPH+r3K+YJLZKRQzqOIHjkz+X2Le8O5Azi1hbg==~-1~-1~1661501446; s_pers=%20s_vnum%3D1661974200347%2526vn%253D1%7C1661974200347%3B%20s_invisit%3Dtrue%7C1661499756915%3B; utag_main=v_id:0182d8f36f680013f53621ee680505065003505d00bd0$_sn:1$_se:21$_ss:0$_st:1661499756345$ses_id:1661497208682%3Bexp-session$_pn:5%3Bexp-session$_vpn:10%3Bexp-session$ab_dc:TEST%3Bexp-1666681956362$_prevpage:PRODUCT%7CPREDATOR%20EDGE.1%20FIRM%20GROUND%20CLEATS%20(H02933)%3Bexp-1661501556896$ttdsyncran:1%3Bexp-session$dcsyncran:1%3Bexp-session$dc_visit:1$dc_event:6%3Bexp-session; _uetsid=b9fc9230250c11edaa62a1c4f77be736; _uetvid=b9fcbbc0250c11edab41f9db2270946c; IR_4270=1661497957101%7C232829%7C1661497957101%7C%7C; IR_PI=1661497211227.bzi5cx58nw5%7C1661584357101; _gat_tealium_0=1; _ga_4DGGV4HV95=GS1.1.1661497211.1.1.1661497957.0.0.0; _ga=GA1.1.2032556734.1661497210; _clsk=9wfrqn|1661497959481|7|0|e.clarity.ms/collect; RT="z=1&dm=adidas.com&si=39a9d76e-bef7-40bf-b0e3-e1e2d61a062b&ss=l7a4j4xt&sl=4&tt=g0l&bcn=%2F%2F0217990f.akstat.io%2F&ul=glp9"' \
#   -H 'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Linux"' \
#   -H 'sec-fetch-dest: document' \
#   -H 'sec-fetch-mode: navigate' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'sec-fetch-user: ?1' \
#   -H 'upgrade-insecure-requests: 1' \
#   -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36' \
#   --compressed
print("\n\n******** ADIDAS *********\n\n")
adiheaders = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-language": "en-US,en;q=0.9,fa;q=0.8,de;q=0.7",
    "cache-control": "max-age=0",
    "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    "upgrade-insecure-requests": "1",
 }
URL = "https://www.adidas.com/us/ultraboost-22-shoes/GX9158.html"

AdidasMenSize = {
"4": "36",
"4.5": "36 2/3",
"5": "37 1/3",
"5.5": "38",
"6": "38 2/3",
"6.5": "39 1/3",
"7": "40",
"7.5": "40 2/3",
"8": "41 1/3",
"8.5": "42",
"9": "42 2/3",
"9.5": "43 1/3",
"10": "44",
"10.5": "44 2/3",
"11": "45 1/3",
"11.5": "46",
"12": "46 2/3",
"12.5": "47 1/3",
"13": "48",
"13.5": "48 2/3",
"14": "49 1/3",
"14.5": "50",
"15": "50 2/3",
"16": "51 1/3",
"17": "52 2/3",
"18": "53 1/3",
"19": "54 2/3",
"20": "55 2/3"
}

AdidasWomenSize = {
"5": "36",
"5.5": "36 2/3",
"6": "37 1/3",
"6.5": "38",
"7": "38 2/3",
"7.5": "39 1/3",
"8": "40",
"8.5": "40 2/3",
"9": "41 1/3",
"9.5": "42",
"10": "42 2/3",
"10.5": "43 1/3",
"11": "44",
"11.5": "44 2/3",
"12": "45 1/3",
"12.5": "46",
"13": "46 2/3",
"13.5": "47 1/3",
"14": "48",
"14.5": "48 2/3",
"15": "49 1/3",
"15.5": "50"
}

styleNum = URL.split('/')[-1]
styleNum = re.findall("^(.*?)\.html", styleNum)[0]
page = requests.get(URL, headers=adiheaders)
soup = BeautifulSoup(page.content, "html.parser")
# print(soup)
scripts = soup.find_all("script")
# for sc in script:
#     print(sc.text, end="\n\n")
# print(scripts)
details = ''
for script in scripts:
  if(script.text.find("@context") != -1):
    details = script.text
pyperclip.copy(details)
details = json.loads(details)
sizes = requests.get("https://www.adidas.com/api/products/"+ styleNum + "/availability?sitePath=us", headers=adiheaders)
# print(sizes.json())
filtered = list(filter(lambda var: var["availability_status"] == "IN_STOCK", sizes.json()["variation_list"]))
mappedSizes = list(map(lambda x: x["size"], filtered))
price = extractPrice(str(details["offers"]["price"]))
morePrice = price
if (soup.find("div", class_="gl-price-item--crossed")):
    morePrice = extractPrice(soup.find("div", class_="gl-price-item--crossed").text.strip())

normalizeSize = []
for size in mappedSizes:
    normalizeSize.append(AdidasMenSize[size])
print(styleNum)
print(morePrice)
print(normalizeSize)
print(details["image"])

# insertIntoDb("https://www.adidas.com.tr/tr/ultimashow-ayakkabi/FX3633.html", details["name"].replace('Ayakkabı', ''),price, price, styleNum, mappedSizes, details["image"])


