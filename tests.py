import YouTubeScraper
import YTQueue
import time

def test_url(url):
    url = ["https://www.youtube.com/watch?v=f78JPjDY2nE",
           'https://www.youtube.com/watch?v=LQIpForyoJg',
           'https://www.youtube.com/watch?v=LhFOqws128Q',
           'https://www.youtube.com/watch?v=WOEV8lIiJ0I',
           'https://www.youtube.com/watch?v=Fvg5RTrFLfI']

    scrapes = []
    for u in url:
        scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                                 category='Alt-right',
                                 seed_url=url,
                                 max_wait=2)
        video, r = scraper.video_processing(u)
        time.sleep(10)
        scrapes.append([video, r])

def test_queue():
    url = "https://www.youtube.com/watch?v=f78JPjDY2nE"
    scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                                category='Alt-right',
                                seed_url=url,
                                max_wait=2)
    x = 0
    q = YTQueue(url)
    while(x <= 7 & q.isEmpty() == False):
        x = q.dequeue().url

        video, rec= scraper.video_processing(x)
        q.add_end(rec)

        x = x + 1
        print(video.url)

def test_ad():

    url = "https://www.youtube.com/watch?v=sf-qyxEIuHI"
    scraper = scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                                       category='Alt-right',
                                       seed_url=url,
                                       max_wait=2)
    scraper.driver.get(url)
    time.sleep(3)

    while( len(scraper.driver.find_elements_by_css_selector('button[id^=visit-advertiser] > span.ytp-ad-button-text')) == 0 ):
        scraper.driver.quit()

        scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                                 category='Alt-right',
                                 seed_url=url,
                                 max_wait=2)

        scraper.driver.get(url)
        time.sleep(3)

    while (scraper.check_ad() == True):
        scraper.skip_ad()