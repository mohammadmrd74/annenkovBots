

from matplotlib import style
from matplotlib.pyplot import title
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time

software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value,
                     OperatingSystem.LINUX.value]
user_agent_rotator = UserAgent(
    software_names=software_names, operating_systems=operating_systems, limit=100)

user_agent = user_agent_rotator.get_random_user_agent()
print(user_agent)

DRIVER_PATH = '/home/mohammad/Downloads/chromedriver_linux64/chromedriver'
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument(f'user-agent={user_agent}')
caps = DesiredCapabilities().CHROME
# print(caps)
caps["pageLoadStrategy"] = "eager"

# class wait_for_all(object):
#     def __init__(self, methods):
#         self.methods = methods

#     def __call__(self, driver):
#         try:
#             for method in self.methods:
#                 if not method(driver):
#                     return False
#             return True
#         except TimeoutException:
#             return False

driver = webdriver.Chrome(desired_capabilities=caps,
                          options=options, executable_path=DRIVER_PATH)

driver.get("https://www.adidas.com.tr/en/duramo-10-shoes/GW8343.html")

try:
    WebDriverWait(driver, 3).until(EC.alert_is_present(),
                                   'Timed out waiting for PA creation ' +
                                   'confirmation popup to appear.')

    alert = driver.switch_to.alert
    alert.dismiss()
    print("alert dismissed")
except TimeoutException:
    print("no alert")
    try:
        myElem = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, 'img')))
        pics = []
        # time.sleep(5)
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[1]/div/div/img').get_attribute('src'))
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[2]/div/div/img').get_attribute('src'))
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[3]/div/div/img').get_attribute('src'))
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[4]/div/div/img').get_attribute('src'))
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[5]/div/div/img').get_attribute('src'))
        pics.append(driver.find_element(By.XPATH, '//*[@id="navigation-target-gallery"]/section/div[1]/div[1]/div/div[6]/div/div/img').get_attribute('src'))

        for p in pics:
            print(p)

        title = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/h1/span').text
        print(title)

        price = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div[2]/div[1]/div/div/div').text
        print(price)

        # styleNum = link['link'].split('/')[-1]
        # print(styleNum)

        
        newSizes = driver.find_elements(By.CLASS_NAME, 'size___TqqSo')
        for size in newSizes:
            print(size.text)



    except TimeoutException:
        print("Loading took too much time!")


driver.quit()
