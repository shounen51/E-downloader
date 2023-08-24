import yaml
from pathlib import Path
import os
import sys
import shutil

from clipboard import clipboard
from downloader_one_dirver_one_thread import downloader
from utils import self_restart, update_package

if __name__ == "__main__":    
    print("version: 1.7")
    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)
    user_dir = Path(os.path.expandvars(data["userDir"]))

    first_time = not user_dir.exists()
    if first_time:
        print(" 第一次使用先開啟 chrome 搜尋 chrome://version/\n\
 把設定檔路徑的資料夾建立一個捷徑在 E-Downloader 資料夾中，並且命名為 profile\n \
 (按著 Ctrl + Shift 拖曳資料夾)\n\
 順便把下載資料夾路徑設定好(config.yaml 的 downloadPath)\n")
        input("完成後按 Enter 再重啟")
        sys.exit()

    if data["checkUpdate"]:
        update_package("selenium")
    else:
        print(" \
              ******************************************\n\
              *** 更新 chrome 後將 checkUpdate 改為 1 ***\n\
              ***    將 auto 改為 1 自動下載不用 Y    ***\n\
              ******************************************")

    download_dir = Path(data["downloadPath"])
    if not download_dir.is_absolute():
        download_dir = download_dir.absolute()
    auto = True if data["auto"]==1 else False
    cb = clipboard()
    cb.start()
    
    while True:
        print("已準備好下載，複製一個網址")
        url = cb.get_url()
        if auto:
            print(f"開始下載 {url}")
            d = downloader(download_dir, user_dir)
            d.download(url)
        else:
            user_input = input(f"是否下載 {url} (Y/N):")
            if user_input == "Y" or user_input == "y":
                d = downloader(download_dir, user_dir)
                d.download(url)
            else:
                print("取消下載")
                continue
        d.join()