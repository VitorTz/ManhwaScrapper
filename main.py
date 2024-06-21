from selenium.webdriver import Firefox, FirefoxOptions
from bs4 import BeautifulSoup
from pathlib import Path
from multiprocessing.pool import ThreadPool
from PIL import Image
import time
import random
import requests
import json


MANGA_DIR = Path("/mnt/HD/Manhwa")


def load_manhwas() -> dict[str, str]:
    with open("manhwas.json", "r") as file:
        return json.load(file)


def get_soup(link: str, driver: Firefox) -> BeautifulSoup:
    while True:
        try:
            print(f"[GET {link}]")
            driver.get(link)
            return BeautifulSoup(driver.page_source, "lxml")    
        except Exception as e:
            print(f"[GET EXCEPTION {e}]")



def get_chapters(page: BeautifulSoup) -> list[str]:
    links: list[str] = []
    d = page.find("div", id="chapters-box")
    for a in d.find_all("a"):
        link = a["href"]
        if "https://toondex.net" not in link:
            link = f"https://toondex.net{link}"
        links.append(link)
    return links[::-1]


    


def download_image(img_source: tuple[str, Path]) -> None:
    link, path = img_source
    path.parent.mkdir(exist_ok=True, parents=True)
    if (path.exists()): return
    while True:
        try:
            time.sleep(random.random())
            print(f"[DOWNLOADING IMAGE {path}]")
            r = requests.get(link, stream=True, timeout=10)
            with open(path, "wb") as file:
                for chunk in r.iter_content(1024):
                    file.write(chunk)
            image = Image.open(path)
            image = image.convert("RGBA")
            image.save(path)
            return
        except Exception as e:
            print(f"[IMAGE DOWNLOADING EXCEPTION {e}]")


def download_cover(manga_name: str, manga_page: BeautifulSoup) -> None:
    img = manga_page.find("img", class_="w-96 m-auto")
    src = f"https://toondex.net{img['src']}"    
    download_image((src, MANGA_DIR / manga_name / "cover.png"))


def download_chapter(
        link: str, 
        manga_name: str, 
        chapter_name: str,
        driver: Firefox
    ) -> None:
    print(f"[DOWNLOADING CHAPTER {chapter_name} for manga {manga_name}]")
    
    page: BeautifulSoup = get_soup(link, driver)

    images: list[tuple[str, Path]] = []    
    
    for img in page.find_all("img"):
        if "row" not in img.get("id", ""):
            continue
        src = img.get("src", img.get("data-src"))
        if src is None:
            print(f"[IMAGE {img} not retrieved]")
            continue

        images.append(
            (
                src,
                MANGA_DIR / manga_name / chapter_name / f"{len(images)+1:02d}.png"
            )
        )        

    with ThreadPool(4) as pool:
        pool.map(download_image, images)
    pool.join()
    

def main() -> None:
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = Firefox(options)
    manhwas: dict[str, str] = load_manhwas()
    
    for manga_name, manga_link in manhwas.items():
        page: BeautifulSoup = get_soup(manga_link, driver)
        download_cover(manga_name, page)        
        chapters: list[str] = get_chapters(page)
        for i, chapter_link in enumerate(chapters): 
            download_chapter(chapter_link, manga_name, f"Chapter {i+1}", driver)

    driver.close()



if __name__ == "__main__":
    main()