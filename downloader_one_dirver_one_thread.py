import os
import shutil
import threading
from queue import Queue
from pathlib import Path
import time
import re

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
        chrome_options.add_argument("--download.protects=true")
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

    def enable_download_in_headless_chrome(self, download_dir:Path):
        download_dir.mkdir(exist_ok=True)
        # add missing support for chrome "send_command"  to selenium webdriver
        self.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': str(download_dir)}}
        command_result = self.execute("send_command", params)

class downloader():
    def __init__(self, target_dir:Path):
        self.temp_dir = Path(os.path.expandvars('%temp%/E-download/'))
        self.temp_dir.mkdir(exist_ok=True)
        self.target_dir = target_dir
        self.driver = my_driver()
        self.ip_checker = ip_checker()
        self.url = ""
        self.main_thread = threading.Thread(target=self.run, daemon=True)
        self.threads_count = 0
        self.title = ""
        self.download_count = 1

    def download(self, url):
        self.url = url
        self.main_thread.start()

    def __trans_2_legal_dir(self, path:str):
        replaced_string = re.sub(r'\/|\\|\:|\?|\*|\"|\<|\>|\|', "_", path)
        return replaced_string
    
    def __get_pic_page_queue(self):
        with self.driver:
            self.driver.get(self.url)
            time.sleep(1)
            self.title = self.__trans_2_legal_dir(self.driver.title)
            self.download_dir = self.temp_dir / self.title
            self.target_dir = self.target_dir / self.title
            downloaded_amunt = 0
            if self.target_dir.exists():
                downloaded_amunt = sum(1 for _ in self.target_dir.iterdir())
                self.download_count += downloaded_amunt
                print(f"{downloaded_amunt} pics already downloads.")
            self.driver.enable_download_in_headless_chrome(self.download_dir)
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
                time.sleep(1)
            for _ in range(downloaded_amunt):
                self.page_queue.get()
   
    def __download_ori_image(self, page_url:str):
        def __skip_to_last(url):
            self.page_queue.put(url)
            self.driver.quit()
            self.driver = my_driver()
            self.driver.enable_download_in_headless_chrome(self.download_dir)

        with self.driver:
            page_url = page_url.split("?")[0]
            print(f"start download {page_url}")
            try:
                self.driver.get(page_url)
            except:
                print(f"{page_url} timeout.")
                __skip_to_last(page_url)
                return
            time.sleep(2)
            try:
                download_url = self.driver.find_element(By.XPATH, '//*[@id="i7"]')
                if download_url.text == "":
                    print(f"fail to download {page_url}. download_url.text == ''")
                    return
            except:
                print(f"fail to download {page_url}. no element")
                return
            download_url.click()
            try:
                while self.driver.find_element(By.XPATH, '/html/body').text.startswith("You have reached the image limit"):
                    print("Download readched limit. Sleep 1 hour or change your ip.")
                    self.ip_checker.wait_ip_change(60*60)
                    __skip_to_last(page_url)
            except:
                pass
            self.__rename_loop()

    def __rename_loop(self):
        def is_file_written(file_path:Path):
            if file_path.is_file():
                B_size = file_path.stat().st_size
                time.sleep(1)
                A_size = file_path.stat().st_size
                return B_size == A_size
            else:
                return False
        self.target_dir.mkdir(exist_ok=True)
        self.download_dir.mkdir(exist_ok=True)
        while True:
            st_min = time.time()
            mv_file = None
            for f in self.download_dir.iterdir():
                if f.suffix.lower() not in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".raw", ".apng"]:
                    continue
                if f.stat().st_ctime < st_min:
                    st_min = f.stat().st_ctime
                    mv_file = f
            if mv_file is not None:
                while not is_file_written(mv_file):
                    pass
                shutil.copy(str(f), str(self.target_dir / (self.title + f"_{self.download_count}" + f.suffix)))
                f.unlink()
                self.download_count += 1
                break
            time.sleep(1)

    def run(self):
        self.__get_pic_page_queue()
        print("[debug] Done fetching urls. Start downloading.")
        while not self.page_queue.empty():
            page_url=self.page_queue.get()
            self.__download_ori_image(page_url)
            time.sleep(1)
        print(f"Done {self.title}.")
        shutil.rmtree(str(self.download_dir))
        self.driver.quit()

    def join(self):
        self.main_thread.join()

if __name__ == "__main__":
    d = downloader(r"D:\e-download")
    d.download("https://e-hentai.org/g/2522327/90bed708f0/")
    time.sleep(300)
