import yaml

from clipboard import clipboard
from downloader_one_dirver_one_thread import downloader

if __name__ == "__main__":
    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)
    download_dir = data["downloadPath"]
    cb = clipboard(key_word_url="https://e-hentai.org/g/")
    cb.start()
    while True:
        url = cb.get_url()
        print(f"get_url {url}")
        d = downloader(download_dir=download_dir)
        d.download(url)