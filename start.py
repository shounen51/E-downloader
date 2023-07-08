import yaml

from clipboard import clipboard
from downloader_one_dirver_one_thread import downloader

if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)
    download_dir = data["downloadPath"]
    cb = clipboard()
    cb.start()
    while True:
        print("Ready for download. Copy a url.")
        url = cb.get_url()
        print(f"get url {url}")
        d = downloader(download_dir=download_dir)
        d.download(url)