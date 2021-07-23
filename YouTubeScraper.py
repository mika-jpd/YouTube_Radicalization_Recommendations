import anytree.search
import treelib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
import time
from requests_html import HTMLSession
from requests_html import AsyncHTMLSession
from bs4 import BeautifulSoup as bs
from anytree import Node, AnyNode, NodeMixin,RenderTree, AbstractStyle, ContStyle
from anytree.exporter import JsonExporter
from collections import deque
import asyncio
import numpy as np

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
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-web-security")
        options.add_argument('--user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"')
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--lang=en-US")
        options.add_argument('--headless')

        return webdriver.Chrome(executable_path=self.path, options=options)

    def update_tabs(self):
        pass

    def control(self):
        pass

###### Video Processing #################
    async def videos_handling(self, url_list:list, main_tab:str, results:list):
        print('videos_handling')
        tasks = []
        for url, i in zip(url_list, list(range(0, len(url_list)))):
            #open new tab and pass it for new video to watch
            self.driver.execute_script("window.open('');")
            new_tab = self.driver.window_handles.pop()

            tasks.append(self.video_processing(url=url, main_tab=main_tab, current_tab=new_tab, res=results, index=i))
        await asyncio.gather(*tasks)

    #here you watch a single video at a time
    async def video_processing(self, url:str, main_tab:str, current_tab:str, res:list, index:int):
        print('video_processing')
        try:
            #self.driver.switch_to_window(current_tab)
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

            # get the recommended videos
            recommended = self.get_video_recommendations()

            # collect the features
            video = self.collect_data(url=url, ads=ad)
            # watch the video for a little, simulate a person
            try:
                await asyncio.sleep(min(video['video_length'], self.max_wait))
            except:
                video['video_length'] = 'Not watched'

            self.driver.switch_to.window(current_tab)
            self.driver.close()
            self.driver.switch_to.window(main_tab)

            res[index] = (video, recommended)
        except:
            res[index] = ('Error found', 'Error found')

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
                if(i.text == 'Skip Ads' or i.text == 'Skip Ad' or i.text == "Passer les annonces" or i.text == "Ignorer l'annonce"):
                    self.driver.find_elements_by_xpath('//*[@class="ytp-ad-skip-button ytp-button"]')[0].click()
                    break

        except TimeoutException:
            pass

    def get_length(self):
        return self.driver.execute_script("return document.getElementById('movie_player').getDuration()")

#LOGIN the YouTube account with hotmail accounts
    def login(self, main_tab, username, password):
        print('login')
        self.driver.get('https://www.youtube.com/')
        time.sleep(2)
        # skip the data protection button
        try:
            self.driver.find_elements_by_xpath(
                '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span')[0].click()
        except:
            try:
                self.driver.find_elements_by_xpath(
                    '/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[2]/div[2]/div[5]/div[2]/ytd-button-renderer[2]/a/tp-yt-paper-button/yt-formatted-string')[
                    0].click()
            except:
                pass
            pass

        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="buttons"]/ytd-button-renderer/a'))).click()
        time.sleep(1)

        for i in username:
            WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]'))).send_keys(i)
            time.sleep((np.random.randint(3, 7))/10)

        WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="identifierNext"]/div/button/span'))).click()

        #click to avoid error
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))).click()
        for i in password:
            #//*[@id="passwordNext"]/div/button
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input'))).send_keys(i)
            time.sleep((np.random.randint(3, 7)) / 10)
        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="passwordNext"]/div/button'))).click()
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@aria-label="Notifications"]')))
        except TimeoutException as e:
            e.msg = 'Login mistake'
            raise
        time.sleep(2)
    def collect_data(self, url:str, ads:bool):
        print('collecting data')
        #time.sleep(1)
        #here add a proper wait (wait for something to show up)
        #time.sleep(2)

        #start = time.perf_counter()
        #prepare beautiful soup for webpage extraction
        #session = HTMLSession()
        #session = AsyncHTMLSession()
        #response = session.get(url)
        #response = await session.get(url)
        # execute Javascript
        #response.html.render(timeout=30)
        # await response.html.arender()
        #response.html.arender()

        # create beautiful soup object to parse HTML
        #soup = bs(response.html.html, "html.parser")
        #end =  time.perf_counter()
        #print(f'Time Beuatiful Soup: {end - start:0.4f} second')
        length = self.get_duration_test()

        self.driver.execute_script('window.scrollTo(0, 540)')
        #need to process all of these in video object
        title = self.get_title()
        creator = self.get_creator()
        description = self.get_description()
        dates = self.get_date()
        views = self.get_views()

        number_comments = self.get_num_comments()

        url = url
        id = self.video_url_to_id(url)

        likes, dislikes = self.get_likes_dislikes()

        #tags = self.get_tags(soup=soup)

        ads = ads

        video = {
            'title':title,
            'content creator':creator,
            'description':description,
            'date':dates,
            'views':views,
            'comments':number_comments,
            'likes':likes,
            'dislikes':dislikes,
            #'tags':tags,
            'video_length':length,
            'url':url,
            'ad':ads,
            'id':id
        }

        #response.close()
        #await session.close()
        #session.close()

        return video

    def get_num_comments(self) -> str:
        try:
            element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="count"]/yt-formatted-string/span[1]')))
            element = element.text
            return element
        except:
            return 'Error found'

    def video_url_to_id(self, url) -> str:
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

    def get_likes_dislikes(self) -> str:
        try:
            result = [i.get_attribute("aria-label") for i in self.driver.find_elements_by_xpath('//yt-formatted-string[@id="text"]') if i.get_attribute("aria-label") != None]

            likes = [i for i in result if ('like' in i) and ('dislike' not in i)]
            dislikes = [i for i in result if ' dislike' in i]

            return likes[0] if (len(likes) != 0) else 'Unavailable', dislikes[0] if (len(dislikes) != 0) else ' Unavailable'
        except:
            return 'Error found'

    def get_title(self) -> str:
        try:
            return self.driver.find_elements_by_xpath('//*[@id="container"]/h1/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_creator(self) -> str:
        try:
            return self.driver.find_elements_by_xpath('//*[@id="text"]/a')[1].text
        except:
            'Error found'

    def get_views(self) -> str:
        try:
            return self.driver.find_elements_by_xpath('//*[@id="count"]/ytd-video-view-count-renderer/span[1]')[0].text
        except:
            return 'Error found'

    def get_description(self) -> str:
        try:
            #self.driver.find_elements_by_xpath('//*[@id="description"]/yt-formatted-string/span[1]')[0].text
            return self.driver.find_elements_by_xpath('//*[@id="description"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_date(self) -> str:
        try:
            return self.driver.find_elements_by_xpath('//*[@id="info-strings"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_duration(self, soup) -> str:
        try:
            soup.find("span", {"class": "ytp-time-duration"}).text
        except:
            return 'Error found'

    def get_duration_test(self) -> str:
        try:
            #pause video so that
            self.driver.find_elements_by_xpath('//*[@class="video-stream html5-main-video"]')[0].click()

            time_element = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 'ytp-time-duration')))

            duration = time_element.text
            self.driver.find_elements_by_xpath('//*[@class="video-stream html5-main-video"]')[0].click()

            #go from string to seconds
            split = duration.split(':')
            seconds = 0
            for i, x in zip(list(range(0, len(split))),  list(range(len(split) -1, -1, -1))):
                seconds = seconds + (int(split[x])) * (60 ** i)

            return seconds
        except:
            return 'Error found'


    def get_video_recommendations(self) -> list:
        recommended_videos = []

        #here the 1 is an index that you can use to cycle through recommended videos
        x = 0

        path = '//*[@id="related"]/ytd-watch-next-secondary-results-renderer//*[@id="thumbnail"]'
        recommendations = self.driver.find_elements_by_xpath(path)
        for i in recommendations:
            recommended_videos.append(i.get_attribute('href'))
            x += 1
            if (x == self.num_recommendations):
                break

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
        self.login(main_tab=main_window, username='mika.desblancs@hotmail.com', password='Mika180600!')
        max_depth = False
        videos_watched = []
        for n in range(0, 10):
            print(f'----Iteration {n}----')
            #returns list of urls
            tasks = []
            for i in range(0, min(12, len(queue))):
                tasks.append(queue.popleft())
            results = [None for i in tasks]
            asyncio.run(self.videos_handling(url_list=tasks, main_tab=main_window, results=results), debug=True)
            #video, recommendations = self.video_processing(x, main_window, new_tab)
            for r in results:
                if r[0] != 'Error found':
                    videos_watched.append(r[0]['title'])
                    node = None
                    #find the node with the url since it is stored in the tree before it is watched
                    if(root.video==None):
                        root.video = r[0]
                        root.title = r[0]['title']
                        node = root
                    else:
                        for n in anytree.LevelOrderIter(root):
                            if(len(n.children) != 0):
                                continue
                            else:
                                if(n.id == r[0]['url']):
                                    node = n
                                    node.title = r[0]['title']
                                    node.video = r[0]
                                else:
                                    continue

                    # add all the recommended videos to the tree in url form
                    # add videos that have already been watched to tree BUT not to the queue since you don't want loops in the recommended videos
                    # you still want to watch seven videos however
                    for i in r[1]:
                        queue.append(i)
                        AnyNode(id=i, parent=node, video=None, title=None)
        print('writing to file')
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open('Scraper_Json.txt', 'w') as outfile:
            exporter.write(root, outfile)

#here create the object and call the central unit which launches the first video + parallele videos
url_seed = "https://www.youtube.com/watch?v=sf-qyxEIuHI"
scraper = YouTubeScraper(path_driver="C:\Program Files (x86)\chromedriver.exe",
                category='News',
                seed_url=url_seed,
                max_wait=10,
                trial_id=1,
                num_recommendations=3)
scraper.test_scraper(url_seed)
scraper.driver.quit()

# moving forward: clicking on videos and tab management!
# put all the feature extracting in some form of try catch thing to avoid the huge number of errors that can pop up
# updating the code so to incorporate asynchronous features