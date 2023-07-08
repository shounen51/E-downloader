import yaml
from pathlib import Path
import os

from clipboard import clipboard
from downloader_one_dirver_one_thread import downloader

if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)
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
            d = downloader(download_dir)
            d.download(url)
        else:
            user_input = input(f"是否下載 {url} (Y/N):")
            if user_input == "Y" or user_input == "y":
                d = downloader(download_dir)
                d.download(url)
            else:
                print("取消下載")
                continue
        d.join()