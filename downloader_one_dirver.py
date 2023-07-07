import threading
from queue import Queue
from pathlib import Path
import time
import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from ip_checker import ip_checker

class my_driver(webdriver.Chrome):
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument(r"--user-data-dir=C:\Users\shounen51\AppData\Local\Google\Chrome\User Data") 
        chrome_options.add_argument("--profile-directory=Defult")
        super().__init__(chrome_options)
        self._LOCK = False
        self._wait_count = 0
        self._condition = threading.Condition()

    def __enter__(self):
        if self._LOCK == True:
            self._wait_count += 1
            print(f"now {self._wait_count} threads waitting.")
            with self._condition:
                self._condition.wait()
                self._wait_count -= 1
        else:
            self._LOCK = True
    
    def __exit__(self, exc_type, exc_value, exc_tracebac):
        if self._wait_count > 0:
            with self._condition:
                print("my_driver notify")
                self._condition.notify()
        else:
            self._LOCK = False

    def join(self):
        while self._LOCK or self._wait_count>0:
            time.sleep(5)

    def enable_download_in_headless_chrome(self, driver, download_dir:Path):
        download_dir.mkdir(exist_ok=True)
        # add missing support for chrome "send_command"  to selenium webdriver
        driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': str(download_dir)}}
        command_result = driver.execute("send_command", params)

class downloader():
    def __init__(self, download_dir, max_thread=5):
        self.driver = my_driver()
        self.ip_checker = ip_checker()
        self.download_dir = Path(download_dir)
        self.max_thread = max_thread
        self.url = ""
        self.main_thread = threading.Thread(target=self.run, daemon=True)
        self.threads_count = 0
        self.title = ""

    def download(self, url):
        self.url = url
        self.main_thread.start()

    def __get_pic_page_queue(self):
        with self.driver:
            self.driver.get(self.url)
            self.title = self.driver.title
            dir = self.download_dir / self.title
            self.driver.enable_download_in_headless_chrome(self.driver, dir)
            text = self.driver.find_element(By.XPATH, '//*[@id="gdd"]/table/tbody/tr[6]/td[2]').text
            total_images = int(text.split(" ")[0])
            self.page_queue = Queue(total_images)
            while not self.page_queue.full():
                pages = self.driver.find_element(By.XPATH, '//*[@id="gdt"]').find_elements(By.CLASS_NAME, "gdtl")
                for p in pages:
                    url = p.find_element(By.TAG_NAME, 'a').get_property('href')
                    print(url)
                    self.page_queue.put(url)
                next_page_button = self.driver.find_element(By.CLASS_NAME, 'ptt').\
                    find_element(By.TAG_NAME, 'tbody').\
                    find_element(By.TAG_NAME, 'tr').\
                    find_elements(By.TAG_NAME, 'td')[-1]
                next_page_button.click()

    def __download_ori_image(self, page_url):
        self.threads_count += 1
        with self.driver:
            self.driver.get(page_url)
            try:
                download_url = self.driver.find_element(By.XPATH, '//*[@id="i7"]')
                if download_url.text == "":
                    print(f"fail to download {page_url}. download_url.text == ''")
                    self.threads_count -= 1
                    return
            except:
                print(f"fail to download {page_url}. no element")
                self.threads_count -= 1
                return
            print(f"start download {page_url}")
            download_url.click()
            try:
                while self.driver.find_element(By.XPATH, '/html/body').text.startswith("You have reached the image limit"):
                    print("Download readched limit. Sleep 1 hour or change your ip.")
                    self.page_queue.put(page_url)
                    self.ip_checker.wait_ip_change(60*60)
            except:
                pass
            self.threads_count -= 1

    def run(self):
        self.__get_pic_page_queue()
        while not self.page_queue.empty():
            if self.threads_count < self.max_thread:
                page_url=self.page_queue.get()
                threading.Thread(target=self.__download_ori_image,daemon=True,args=[page_url,]).start()
            time.sleep(1)
        while not self.threads_count==0:
            time.sleep(5)
        print(f"Done {self.title}.")
        self.driver.quit()

    def join(self):
        time.sleep(10)
        self.driver.join()

if __name__ == "__main__":
    d = downloader(r"D:\e-download", 1)
    d.download("https://e-hentai.org/g/2522327/90bed708f0/")
    time.sleep(300)
