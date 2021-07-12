import anytree.search
import treelib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time
import Video
from requests_html import HTMLSession
from bs4 import BeautifulSoup as bs
#from treelib import Node, Tree
from anytree import Node, AnyNode, NodeMixin,RenderTree, AbstractStyle, ContStyle
from anytree.exporter import JsonExporter
from YTQueue import YTQueue, Node
from collections import deque
import asyncio

class YouTubeScraper:
    def __init__(self, path_driver, category, seed_url, max_wait, trial_id, num_recommendations,history=False):
        self.path = path_driver
        self.driver = self.create_chrome_driver()
        self.driverconst = self.driver.title
        self.category = category
        self.seed_url = seed_url
        self.history = history
        self.max_wait = max_wait
        self.trial_id = trial_id
        self.num_recommendations=num_recommendations

    def create_chrome_driver(self):
        options = webdriver.ChromeOptions()
        #options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--mute-audio")
        options.add_argument('--headless')

        return webdriver.Chrome(executable_path=self.path, options=options)

    def update_tabs(self):
        pass

    def control(self):
        pass


###### Video Processing #################
    def video_processing(self, url, main_tab, current_tab) -> object:

        self.driver.switch_to.window(current_tab)
        self.driver.get(url)

        #wait for the video to be loaded
        time.sleep(1)

        #skip the data protection button
        try:
            self.driver.find_elements_by_xpath('//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span')[0].click()
        except:
            try:
                self.driver.find_elements_by_xpath('/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[2]/div[2]/div[5]/div[2]/ytd-button-renderer[2]/a/tp-yt-paper-button/yt-formatted-string')[0].click()
            except:
                pass
            pass

        #skip ad
        time.sleep(2)
        ad = None
        while(self.check_ad() == True):
            ad = True
            self.skip_ad()
            time.sleep(2)

        #change to just check whether the video is playing or not (ie. if the big button is discoverable & no ads)
        if (ad == None):
            self.start_video()

        # extract the video length with the JavaScript code
        # use JavaScript since the element isn't always visible
        length = self.get_length()

        #watch the video for a little, simulate a person
        self.wait_seconds(length)

        #collect the features
        video = self.collect_data(url=url, length=length, ads=ad)

        #get the recommended videos
        recommended = self.get_video_recommendations()

        self.driver.switch_to.window(current_tab)
        self.driver.close()
        self.driver.switch_to.window(main_tab)

        return video, recommended

    def start_video(self):
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
            return True

    def skip_ad(self):
        time.sleep(5)
        #wait for the end of the advertisement
        try:
            #first make sure it can be skipped by finding the ad text button
            element = self.driver.find_elements_by_xpath('//*[contains(@id, "ad-text:")]')
            for i in element:
                if(i.text == 'Skip Ads' or i.text == 'Skip Ad'):
                    self.driver.find_elements_by_xpath('//*[@class="ytp-ad-skip-button ytp-button"]')[0].click()
                    break

        except TimeoutException:
            pass

    # wait minutes to simulate watching a video, length is the video's length
    def wait_seconds(self, length):
        if (length < self.max_wait):
            #WebDriverWait(driver=self.driver, timeout=length)
            time.sleep(length)
        else:
            #WebDriverWait(driver=self.driver, timeout=self.max_wait)
            time.sleep(self.max_wait)

    def get_length(self):
        return self.driver.execute_script("return document.getElementById('movie_player').getDuration()")

    def collect_data(self, url, length, ads):
        #time.sleep(1)
        self.driver.execute_script('window.scrollTo(0, 540)')
        #time.sleep(2)

        start = time.perf_counter()
        #prepare beautiful soup for webpage extraction
        session = HTMLSession()
        response = session.get(url)
        # execute Javascript
        response.html.render(timeout=30)
        # create beautiful soup object to parse HTML
        soup = bs(response.html.html, "html.parser")
        end =  time.perf_counter()
        print(f'Time Beuatiful Soup: {end - start:0.4f} second')

        #need to process all of these in video object
        title = self.get_title()
        creator = self.get_creator(soup=soup)
        description = self.get_description(soup=soup)
        dates = self.get_date(soup=soup)
        views = self.get_views(soup=soup)

        number_comments = self.get_num_comments()

        url = url
        id = self.video_url_to_id(url)

        likes, dislikes = self.get_likes_dislikes(soup=soup)

        tags = self.get_tags(soup=soup)

        length = length
        ads = ads

        '''
        vid = Video.video(title=title, content_creator=creator,
                          description=description, date=dates,
                          views=views, comments=number_comments,
                          likes=likes, dislikes=dislikes,
                          transcript='the transcript', tags=tags,
                          video_length=length, url=url,
                          ad=ads, id=id)
        '''

        vid = {
            'title':title,
            'content creator':creator,
            'description':description,
            'date':dates,
            'views':views,
            'comments':number_comments,
            'likes':likes,
            'dislikes':dislikes,
            'tags':tags,
            'video_length':length,
            'url':url,
            'ad':ads,
            'id':id
        }

        response.close()
        session.close()
        #find a way to cycle through comments

        return vid

    def get_num_comments(self):
        try:
            #return self.get_by_xpath('//*[@id="count"]/yt-formatted-string/span[1]').text
            return self.driver.find_elements_by_xpath('//*[@id="count"]/yt-formatted-string/span[1]')[0].text
        except:
            return 'Error found'

    def video_url_to_id(self, url):
        s = url.split('=')
        return s[1]

    def get_tags(self, soup):
        # open("index.html", "w").write(response.html.html)
        # initialize the result
        try:
            tags = ', '.join([ meta.attrs.get("content") for meta in soup.find_all("meta", {"property": "og:video:tag"}) ])
            return tags
        except:
            return 'Error found'


    def get_likes_dislikes(self, soup):
        try:
            result = [i.get_attribute("aria-label") for i in self.driver.find_elements_by_xpath('//yt-formatted-string[@id="text"]') if i.get_attribute("aria-label") != None]

            likes = [i for i in result if ('like' in i) and ('dislike' not in i)]
            dislikes = [i for i in result if ' dislike' in i]

            return likes[0] if (len(likes) != 0) else 'Unavailable', dislikes[0] if (len(dislikes) != 0) else ' Unavailable'
        except:
            return 'Error found'

    def get_title(self):
        try:
            return self.driver.find_elements_by_xpath('//*[@id="container"]/h1/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_creator(self, soup):
        try:
            return self.driver.find_elements_by_xpath('//*[@id="text"]/a')[1].text
        except:
            'Error found'

    def get_views(self, soup):
        try:
            return self.driver.find_elements_by_xpath('//*[@id="count"]/ytd-video-view-count-renderer/span[1]')[0].text
        except:
            return 'Error found'

    def get_description(self, soup):
        try:
            #self.driver.find_elements_by_xpath('//*[@id="description"]/yt-formatted-string/span[1]')[0].text
            return self.driver.find_elements_by_xpath('//*[@id="description"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_date(self, soup):
        try:
            return self.driver.find_elements_by_xpath('//*[@id="info-strings"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_duration(self, soup):
        try:
            soup.find("span", {"class": "ytp-time-duration"}).text
        except:
            return 'Error found'

    def get_video_recommendations(self):
        recommended_videos = []

        #here the 1 is an index that you can use to cycle through recommended videos
        i = 1
        while(i <= self.num_recommendations):
            path = '//*[@id="items"]/ytd-compact-video-renderer[{0}]//*[@id="thumbnail"]'.format(i)
            recommended = self.driver.find_element_by_xpath(path).get_attribute('href')
            recommended_videos.append(recommended)
            i += 1

        return recommended_videos

    def get_by_xpath(self, xpath):
        try:
            return self.driver.find_element_by_xpath(xpath=xpath)
        except:
            return 'Error found'


    def test_scraper(self, url_seed):
        queue = deque([url_seed])
        root = AnyNode(id=url_seed, parent=None, video=None, title=None)

        main_window = self.driver.window_handles[-1]
        max_depth = False
        for n in range(0, 60):
            #returns a url
            x = queue.popleft()

            handles_before = self.driver.window_handles
            self.driver.execute_script("window.open('');")

            #returns the last tab that was opened
            new_tab = self.driver.window_handles.pop()

            video, recommendations = self.video_processing(x, main_window, new_tab)
            node = None

            #find the node with the url since it is stored in the tree before it is watched
            if(root.video==None):
                root.video = video
                root.title = video['title']
                node = root
            else:
                for n in anytree.LevelOrderIter(root):
                    if(len(n.children) != 0):
                        continue
                    else:
                        if(n.id == video['url']):
                            node = n
                            node.title = video['title']
                            node.video = video
                        else:
                            continue

            # add all the recommended videos to the tree in url form
            # add videos that have already been watched to tree BUT not to the queue since you don't want loops in the recommended videos
            # you still want to watch seven videos however

            for i in recommendations:
                queue.append(i)
                AnyNode(id=i, parent=node, video=None, title=None)
        #print(RenderTree(root, style=ContStyle()))
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open('Scraper_Json.txt', 'w') as outfile:
            exporter.write(root, outfile)


def main():
    url_seed = "https://www.youtube.com/watch?v=sf-qyxEIuHI"
    scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                   category='News',
                   seed_url=url_seed,
                   max_wait=0,
                   trial_id=1,
                   num_recommendations=3)
    scraper.test_scraper(url_seed)
    scraper.driver.quit()

if __name__ == '__main__':
    main()


# moving forward: clicking on videos and tab management!
# put all the feature extracting in some form of try catch thing to avoid the huge number of errors that can pop up
# updating the code so to incorporate asynchronous features