from selenium import webdriver
from selenium.webdriver.common.by import By
import time

link = "https://youtu.be/vQHVGXdcqEQ"
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options = options, executable_path="C:\\chromedriver.exe")
driver.set_window_size(300,300)
driver.get(link)
time.sleep(1)
links=[]
xpath = By.XPATH
elements = driver.find_elements(by = xpath, value = '//*[@class="yt-simple-endpoint style-scope ytd-compact-video-renderer"]')
for l in elements:
    if l.get_attribute('href') != None and ("radio" not in l.get_attribute('href')) and ("shorts" not in l.get_attribute('href')):
        links.append("https://youtu.be/" + l.get_attribute('href').strip('https://www.youtube.com/watch?v')[1:12])


for i in range(5):
    try:
        print(links[i])
    except:
        print('nothing')
        break