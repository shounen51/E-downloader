import threading
from queue import Queue
from pathlib import Path
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class my_driver(webdriver.Chrome):
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument(r"--user-data-dir=C:\Users\shounen51\AppData\Local\Google\Chrome\User Data") 
        chrome_options.add_argument("--profile-directory=Defult")
        super().__init__(chrome_options)

class downloader():
    def __init__(self, download_dir, max_thread=5):
        self.download_dir = Path(download_dir)
        self.max_thread = max_thread
        self.url = ""
        self.main_thread = threading.Thread(target=self.run, daemon=True)
        self.threads_count = 0
        self.title = ""

    def download(self, url):
        self.url = url
        self.main_thread.start()

    def __enable_download_in_headless_chrome(self, driver, download_dir):
        # add missing support for chrome "send_command"  to selenium webdriver
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        command_result = driver.execute("send_command", params)

    def __get_pic_page_queue(self):
        driver = my_driver()
        driver.get(self.url)
        self.title = driver.title
        text = driver.find_element(By.XPATH, '//*[@id="gdd"]/table/tbody/tr[6]/td[2]').text
        total_images = int(text.split(" ")[0])
        self.page_queue = Queue(total_images)
        while not self.page_queue.full():
            pages = driver.find_element(By.XPATH, '//*[@id="gdt"]').find_elements(By.CLASS_NAME, "gdtl")
            for p in pages:
                url = p.find_element(By.TAG_NAME, 'a').get_property('href')
                print(url)
                self.page_queue.put(url)
            next_page_button = driver.find_element(By.CLASS_NAME, 'ptt').\
                    find_element(By.TAG_NAME, 'tbody').\
                    find_element(By.TAG_NAME, 'tr').\
                    find_elements(By.TAG_NAME, 'td')[-1]
            next_page_button.click()
        driver.close()

    def __download_ori_image(self, page_url):
        self.threads_count += 1
        driver = my_driver()
        driver.get(page_url)
        dir = self.download_dir / self.title
        dir.mkdir(exist_ok=True)
        self.__enable_download_in_headless_chrome(driver, str(dir))
        try:
            download_url = driver.find_element(By.XPATH, '//*[@id="i7"]')
            if download_url.text == "":
                print(f"fail to download {page_url}")
                return
        except:
            print(f"fail to download {page_url}")
            return
        print(f"start download {page_url} at {str(dir)}")
        download_url.click()
        time.sleep(5)
        driver.quit()
        self.threads_count -= 1

    def run(self):
        self.__get_pic_page_queue()
        while not self.page_queue.empty():
            if self.threads_count < self.max_thread:
                page_url=self.page_queue.get()
                threading.Thread(target=self.__download_ori_image,daemon=True,args=[page_url,]).start()
        while not self.threads_count==0:
            time.sleep(5)

if __name__ == "__main__":
    d = downloader(r"D:\e-download", 4)
    d.download("https://e-hentai.org/g/2522327/90bed708f0/")
    time.sleep(300)