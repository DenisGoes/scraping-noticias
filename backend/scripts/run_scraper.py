from backend.scrapers.tecnologia.tecnoblog.scraper import run_scraper_tec
from backend.scrapers.tecnologia.bleepingcomputer.scraper import run_scraper_bleeping
from backend.scrapers.tecnologia.hackernews.scraper import run_scraper_hacker

def main():
    run_scraper_tec()
    run_scraper_bleeping()
    run_scraper_hacker()


if __name__ == "__main__":
    main()