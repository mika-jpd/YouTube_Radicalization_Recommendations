from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
import time
import Video
from requests_html import HTMLSession
from bs4 import BeautifulSoup as bs

import asyncio

class YouTubeScraper:
    def __init__(self, path_driver, category, seed_url, max_wait,history=False):
        self.path = path_driver
        self.driver = self.create_chrome_driver()
        self.driverconst = self.driver.title
        self.category = category
        self.seed_url = seed_url
        self.history = history
        self.max_wait = max_wait

    def create_chrome_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")

        return webdriver.Chrome(executable_path=self.path, options=options)

    def update_tabs(self):
        pass

    def control(self):
        pass


###### Video Processing #################
    def video_processing(self, url):

        self.driver.get(url)

        #skip ad
        ad = self.check_ad()
        if (ad == False):
            self.start_video()

        # extract the video length with the JavaScript code
        # use JavaScript since the element isn't always visible
        length = self.driver.execute_script("return document.getElementById('movie_player').getDuration()")

        #watch the video for a little, simulate a person
        self.wait_seconds(length)

        #collect the features
        video = self.collect_data(url=url, length=length)

        recommended = self.get_video_recommendations()

        self.driver.quit()
        return video, recommended

    def start_video(self):
        time.sleep(3)

        #click on the button to start if
        try:
            element = self.driver.find_element_by_xpath("//button[@class='ytp-large-play-button ytp-button']")
            element.click()
        except ElementNotInteractableException:
            pass



    # checks if there's an ad playing or not
    def check_ad(self) -> bool:
        ads = self.driver.find_elements_by_css_selector('button[id^=visit-advertiser] > span.ytp-ad-button-text')
        if (len(ads) == 0):
            return False
        else:
            #wait for the end of the advertisement
            try:
                #there can be two ads of 5 seconds in a row
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, '//*[@id*="ad-text"]'))
                )
            except TimeoutException:
                pass
        return True


    # wait minutes to simulate watching a video, length is the video's length
    def wait_seconds(self, length):
        if (length < self.max_wait):
            WebDriverWait(driver=self.driver, timeout=length)
        else:
            WebDriverWait(driver=self.driver, timeout=self.max_wait)

    def collect_data(self, url, length):
        self.driver.execute_script('window.scroll(0, 590)')
        time.sleep(2)

        #need to process all of these in video object
        title = self.driver.find_elements_by_xpath('//*[@id="container"]/h1/yt-formatted-string')[0].text
        creator = self.driver.find_elements_by_xpath('//*[@id="text"]/a')[1].text
        description = self.driver.find_elements_by_xpath('/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[7]/div[2]/ytd-video-secondary-info-renderer/div/ytd-expander/div/div/yt-formatted-string')[0].text
        dates = self.driver.find_element_by_xpath('//*[@id="info-strings"]/yt-formatted-string').text
        views = self.driver.find_element_by_xpath('//*[@id="count"]/ytd-video-view-count-renderer/span[1]').text

        number_comments = self.driver.find_element_by_xpath('//*[@id="count"]/yt-formatted-string/span[1]').text
        likes = self.driver.find_elements_by_xpath('/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[6]/div[2]/ytd-video-primary-info-renderer/div/div/div[3]/div/ytd-menu-renderer/div[2]/ytd-toggle-button-renderer[1]/a/yt-formatted-string')[0].text
        dislike = self.driver.find_elements_by_xpath('/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[6]/div[2]/ytd-video-primary-info-renderer/div/div/div[3]/div/ytd-menu-renderer/div[2]/ytd-toggle-button-renderer[2]/a/yt-formatted-string')[0].text
        url = url
        id = self.video_url_to_id(url)
        tags = self.get_tags(url)
        length = length
        ads = self.check_ad()

        vid = Video.video(title=title, content_creator=creator,
                          description=description, date=dates,
                          views=views, comments=number_comments,
                          likes=likes, dislikes=dislike,
                          transcript='the transcript', tags=tags,
                          video_length=length, url=url,
                          ad=ads, id=id)


        #find a way to cycle through comments

        return vid

    def video_url_to_id(self, url):
        s = url.split('=')
        return s[1]

    def get_tags(self, url):
        session = HTMLSession()
        response = session.get(url)
        # execute Javascript
        response.html.render(sleep=1)
        # create beautiful soup object to parse HTML
        soup = bs(response.html.html, "html.parser")
        # open("index.html", "w").write(response.html.html)
        # initialize the result
        tags = ', '.join([ meta.attrs.get("content") for meta in soup.find_all("meta", {"property": "og:video:tag"}) ])

        return tags


    def get_video_recommendations(self):
        time.sleep(2)
        recommended_videos = []
        #here the 1 is an index that you can use to cycle through recommended videos
        i = 1
        while(i <= 7):
            path = '//*[@id="items"]/ytd-compact-video-renderer[{0}]//*[@id="thumbnail"]'.format(i)
            recommended = self.driver.find_element_by_xpath(path).get_attribute('href')
            recommended_videos.append(recommended)
            i += 1

        return recommended_videos




def main():
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
        scrapes.append([video, r])

    print('done')
if __name__ == '__main__':
    main()


# moving forward: clicking on videos and tab management!