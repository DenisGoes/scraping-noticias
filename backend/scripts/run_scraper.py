from backend.scrapers.tecnologia.tecnoblog.scraper import run_scraper_tec
from backend.scrapers.tecnologia.bleepingcomputer.scraper import run_scraper_bleeping
from backend.scrapers.tecnologia.the_hacker_news.scraper import (
    run_scraper_the_hacker_news,
)

def main():
    run_scraper_tec()
    run_scraper_bleeping()
    run_scraper_the_hacker_news()


if __name__ == "__main__":
    main()
