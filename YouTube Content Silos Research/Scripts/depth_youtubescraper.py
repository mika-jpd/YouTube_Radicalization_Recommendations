import json

from selenium_stealth import stealth
import anytree.search
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
from anytree import Node, AnyNode, NodeMixin, RenderTree, AbstractStyle, ContStyle, AsciiStyle
from anytree.exporter import JsonExporter
from collections import deque
import asyncio
import numpy as np
import os
import random
import sys
import uuid
import getpass

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class YouTubeScraper:
    def __init__(self, path_driver, profile_path, max_wait, trial_id, username, password,depth, breadth):
        #driver inputs
        self.path = path_driver
        self.profile_path = profile_path
        self.driver = self.create_chrome_driver()

        #video specific
        self.homepage = []
        self.max_wait = max_wait
        self.trial_id = trial_id
        self.username = username
        self.password = password
        self.depth = depth
        self.breadth = breadth
        self.tree = None

    def create_chrome_driver(self):
        options = webdriver.ChromeOptions()

        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--mute-audio")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-web-security")
        options.add_argument("--lang=en-US")
        options.add_argument('window-size=1920,1080')
        options.add_argument(f"user-data-dir={self.profile_path}")
        options.add_argument(f"profile-directory=Default")

        # comment out in order to see the scraper interacting with webpages
        #options.add_argument('--headless')
        s = Service(self.path)
        try:
            return webdriver.Chrome(service=s, options=options)
        except:
            return webdriver.Chrome(executable_path=self.path, options=options)

    #here just collect video features, add to anynode, add the recommended video to the tasks array
    #once you've colleced n videos, get picture of the homepage
    def video_processing(self, url:str, main_tab:str, parent, number_recommended):
        print(f'    -video processing {url}')
        try:
            self.driver.execute_script("window.open('');")
            new_tab = self.driver.window_handles.pop()
            self.driver.switch_to.window(new_tab)
            self.driver.get(url)
            # wait for the video to be loaded
            time.sleep(1)
            # skip the data protection button if it appears
            try:
                self.driver.find_elements(By.XPATH,
                    '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span')[0].click()
            except:
                # skip the data protection button if it appears
                try:
                    self.driver.find_elements(By.XPATH,
                        '/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[2]/div[2]/div[5]/div[2]/ytd-button-renderer[2]/a/tp-yt-paper-button/yt-formatted-string')[0].click()
                except:
                    pass
                pass
            # skip ad
            time.sleep(2)
            self.start_video()
            ad = None
            while (self.check_ad() == True):
                ad = True
                self.skip_ad()
                time.sleep(2)
            # change to just check whether the video is playing or not (ie. if the big button is discoverable & no ads)
            if (ad == None):
                self.start_video()

            # get the 1st unwatched recommended video
            recommendations = self.get_video_recommendations(current_tab=self.driver.current_window_handle, number_recommended=number_recommended)

            # collect the features
            video = self.collect_data(url=url, ads=ad)
            # watch the video for a little, simulate a person
            try:
                time.sleep(min(video['video_length'], self.max_wait))
            except:
                video['video_length'] = 'Not watched'
            new_node = AnyNode(id=url, parent=parent, video=video, title=video['title'], top_10_recommended=self.top_recommended(10))
            #close the video tab & switch to main tab
            self.driver.close()
            self.driver.switch_to.window(main_tab)
            main_tab = self.driver.current_window_handle
            print(f'        -video: {video["title"]} by {video["content creator"]}, {video["video_length"]}')
        except Exception as e:
            print(e)
            raise Exception
        return new_node, main_tab, recommendations

    def top_recommended(self, n):
        recommendations = self.driver.find_elements(By.XPATH, '//*[@id="items"]//*[@id="thumbnail"]')
        recommendations = [i.get_attribute('href') for i in recommendations]
        return recommendations[0:n]

    #get a snapshot of the homepage
    #returns a list of videos
    def homepage_snapshot(self, main_tab, reload=None):
        print('     -homepage:', end='')
        self.driver.switch_to.window(main_tab)
        #reload YouTube homepage
        if reload == True:
            self.driver.get('https://www.youtube.com/')
        time.sleep(3)
        #will contain list of 20 videos of the homepage
        elements = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents"]/ytd-rich-grid-row//*[@id="contents"]//*[@id="thumbnail"]')))
        videos = [i.get_attribute('href') for i in elements]
        if not(None in videos):
            print(' success')
        else:
            print(' error')
        return videos

    def get_video_recommendations(self, current_tab, number_recommended) -> str:
        self.driver.switch_to.window(current_tab)
        print('         -getting recommendations:', end='')
        recommended_video = []

        path = '//*[@id="items"]//*[@id="thumbnail"]'
        recommendations = self.driver.find_elements(By.XPATH, path)

        for i in recommendations:
            #you are popping the first one in the list, make sure it doesn't represent the true first video
            video_url = i.get_attribute('href')

            #only add the videos not seen before
            if self.tree == None:
                recommended_video.append(video_url)
            elif(anytree.search.find(self.tree, filter_=lambda node: node.id == video_url) == None) and not (video_url == None):
                recommended_video.append(video_url)
                break
            else:
                continue
        if len(recommended_video) > 0:
            print(' success')
        else:
            print('end')
        return recommended_video[0:number_recommended]

    def get_by_xpath(self, xpath):
        try:
            return self.driver.find_elements(By.XPATH, xpath)
        except:
            return 'Error found'

    def start_video(self):
        #print('start video')
        #click on the button to start if the video is not playing (ie. if there were no ads before it)
        try:
            element = self.driver.find_elements(By.XPATH, '//*[@id="movie_player"]/div[5]/button')
            element[0].click()
        except:
            pass

    # checks if there's an ad playing or not
    def check_ad(self) -> bool:
        #print('check ad')
        #ads = self.driver.find_elements_by_css_selector('button[id^=visit-advertiser] > span.ytp-ad-button-text')
        #ads = self.driver.find_element(By.CSS_SELECTOR, 'button[id^=visit-advertiser] > span.ytp-ad-button-text')
        ads = self.driver.find_elements_by_css_selector('button[id^=visit-advertiser] > span.ytp-ad-button-text')
        if (len(ads) == 0):
            return False
        else:
            return True

    def skip_ad(self):
        #print('skip ad')
        time.sleep(5)
        #wait for the end of the advertisement
        try:
            #first make sure it can be skipped by finding the ad text button
            element = self.driver.find_elements(By.XPATH, '//*[contains(@id, "ad-text:")]')
            for i in element:
                #my code works for both french YouTube and anglohpone YouTube
                if(i.text == 'Skip Ads' or i.text == 'Skip Ad' or i.text == "Passer les annonces" or i.text == "Ignorer l'annonce"):
                    self.driver.find_elements(By.XPATH, '//*[@class="ytp-ad-skip-button ytp-button"]')[0].click()
                    break

        except TimeoutException:
            pass

    def login(self, main_tab):
        # ('login')
        try:
            stealth(self.driver,
                    user_agent='DN',
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )

            self.driver.get(
                'https://accounts.google.com/signin/v2/identifier?hl=en&continue=https%3A%2F%2Fwww.google.com%2Fsearch%3Fq%3Dgoogle%2Bsign%2Bin%26rlz%3D1C1CHBF_enCA883CA883%26oq%3Dgoogle%2Bsign%2Bin%26aqs%3Dchrome..69i57j69i64l2j69i60l3.2918j0j1%26sourceid%3Dchrome%26ie%3DUTF-8&gae=cb-none&flowName=GlifWebSignIn&flowEntry=ServiceLogin')
            time.sleep(5)

            print('     -logging in -', end='')

            # Just in case you didn't log in
            if not (self.driver.current_url == "https://www.google.com/search?q=google+sign+in&rlz=1C1CHBF_enCA883CA883&oq=google+sign+in&aqs=chrome..69i57j69i64l2j69i60l3.2918j0j1&sourceid=chrome&ie=UTF-8&pli=1"):
                print('      manually:', end='')
                for i in self.username:
                    WebDriverWait(self.driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="Email"]'))).send_keys(i)
                    time.sleep((np.random.randint(1, 3)) / 10)

                WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="next"]'))).click()

                if self.driver.current_url == 'https://accounts.google.com/signin/rejected?rrk=46&hl=en':
                    print(' error pag', end='')

                    time.sleep(4)
                    self.driver.back()
                    time.sleep(3)
                    WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="next"]')))
                    element = self.driver.find_element(By.XPATH('//*[@id="Email"]'))
                    ActionChains(self.driver).move_to_element(element).perform()
                    time.sleep(2)
                    element = self.driver.find_element(By.XPATH('//*[@id="next"]'))
                    ActionChains(self.driver).move_to_element(element).perform()
                    ActionChains(self.driver).click().perform()

                for i in self.password:
                    WebDriverWait(self.driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]'))).send_keys(i)
                    time.sleep((np.random.randint(1, 3)) / 10)

                WebDriverWait(self.driver, 60).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]'))).click()

            stealth(self.driver,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36',
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
            time.sleep(2)
            # print('opening window')
            self.driver.execute_script("window.open('https://www.youtube.com/')")

            self.driver.switch_to.window(self.driver.window_handles[1])
            # print('looking for notifications')
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="img"]')))

            # print('switch window 0')
            self.driver.switch_to.window(self.driver.window_handles[0])

            # print('okay')

            # print('closing')
            self.driver.close()
            # print('popping')
            main_tab = self.driver.window_handles.pop()
            self.driver.switch_to.window(main_tab)

            print(' login success!')
            return main_tab
        except Exception as e:
            print(', error not fixed')
            return_statement = f'Error logging in: {e}'
            raise ElementNotInteractableException(msg=return_statement)

    def delete_history(self, main_tab):
        print('     -deleting history: ', end='')

        # open window and navigate to the webpage
        self.driver.execute_script(
            "window.open('https://myactivity.google.com/activitycontrols/youtube?hl=en&utm_source=privacy-advisor-youtube')")
        time.sleep(2)
        new_tab = self.driver.window_handles.pop()
        self.driver.switch_to.window(new_tab)
        try:
            time.sleep(10)
            # print('1')
            delete = WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException)).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="gb"]/div[4]/div[2]/div/c-wiz/div/div/nav//div[@class="vwWeec"]')))
            time.sleep(2)
            delete = [i for i in delete if ("Delete" in i.text) & ("activity" in i.text)]
            delete = delete[0]
            delete.click()

            time.sleep(2)
            # print('2')
            delete_all_time = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[8]/div/div[2]/span/div[2]/div/c-wiz/div/div[3]/ul/li[3]')))
            delete_all_time.click()

            # if this doesn't go through then we haven't watched any videos
            try:
                # print('3')
                time.sleep(2)
                confirm_delete = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         '/html/body/div[8]/div/div[2]/span/div[2]/div[1]/c-wiz/div/div[4]/div/div[2]/button')))
                confirm_delete.click()

            except Exception as e:
                print(f' no history to delete,', end='')
        except Exception as e:
            return_statement = f' history delete error: {e}'
            raise ElementNotInteractableException(msg=return_statement)

        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        main_tab = self.driver.window_handles[0]
        print(' success')
        return main_tab


    def collect_data(self, url:str, ads:bool):
        print('         - collect data')
        length = self.get_length()

        self.driver.execute_script('window.scrollTo(0, 540)')

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
            result = [i.get_attribute("aria-label") for i in self.driver.find_elements(By.XPATH, '//yt-formatted-string[@id="text"]') if i.get_attribute("aria-label") != None]

            likes = [i for i in result if ('like' in i) and ('dislike' not in i)]
            dislikes = [i for i in result if ' dislike' in i]

            return likes[0] if (len(likes) != 0) else 'Unavailable', dislikes[0] if (len(dislikes) != 0) else ' Unavailable'
        except:
            return 'Error found'

    def get_title(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="container"]/h1/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_creator(self) -> str:
        try:
            return self.driver.find_elements_by_xpath('//*[@id="text"]/a')[0].text
        except:
            'Error found'

    def get_views(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="count"]/ytd-video-view-count-renderer/span[1]')[0].text
        except:
            return 'Error found'

    def get_description(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="description"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_date(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="info-strings"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_length(self) -> str:
        try:
            return self.driver.execute_script("return document.getElementById('movie_player').getDuration()")
        except:
            return 'Error found'

    def run_scraper(self, url_seed):
        #create a dummy node as tree root, used to keep track of number of videos watched
        
        #login, delete history, pass window handle as input
        main_window = self.driver.window_handles[-1]
        main_window = self.login(main_tab=main_window)
        main_window = self.delete_history(main_tab=main_window)
        self.homepage.append(self.homepage_snapshot(main_window))

        # Returns list of recommended videos
        parent, main_window, recommended = self.video_processing(url=url_seed, parent=None, main_tab=main_window, number_recommended=self.breadth)
        self.tree = parent
        self.homepage.append(self.homepage_snapshot(main_tab=main_window, reload=True))

        for recommended_url in recommended:
            parent = self.tree
            url = recommended_url
            for i in range(0, self.depth):
                self.driver.switch_to.window(main_window)
                main_window = self.driver.current_window_handle
                parent, main_window, recommended = self.video_processing(url=url, parent=parent, main_tab=main_window, number_recommended=1)
                url = recommended[0]
            self.homepage.append(self.homepage_snapshot(main_tab=main_window, reload=True))

        self.driver.quit()
        # ---Save results to a CSV file----
        print('Writing to file')
        path_to_directory = f'{os.getcwd()}/Depth'

        # put homepage in directory
        for i in range(0, len(self.homepage)):
            path_to_file = f'{path_to_directory}/homepage/homepage_{i}_{self.trial_id}.txt'
            with open(path_to_file, 'w+') as outfile:
                for element in self.homepage[i]:
                    if isinstance(element, str):
                        outfile.write(element + '\n')
            outfile.close()

        # put tree into file
        path_to_file = f'{path_to_directory}/tree/tree_{self.trial_id}.txt'
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open(path_to_file, 'w+') as outfile:
            exporter.write(self.tree, outfile)
        outfile.close()
        ##############################################

# Setup
user = getpass.getuser()

with open(f"config_depth_{user}.json") as json_data_file:
    data = json.load(json_data_file)

username = data['username']
password = data['password']
path = data['path']
profile_path = data["profile path"]

max_wait = data['max_wait']
depth = data['depth']
breadth = data['breadth']

seed_file = open(data['Seeds'], 'r')
seeds = seed_file.read()
seeds = seeds.split('\n')

print('Welcome to the YouTube scraper!')
print(f'{user}, you are running the scraper with parameters:')
print(f'     -username: {username}')
print(f'     -password: {password}')
print(f'     -path: {path}')
print(f'     -profile path: {profile_path}')
print(f'     -max wait: {max_wait}')
print(f'     -depth: {depth}')
print(f'     -breadth: {breadth}')
print('Enjoy!')

i = 0
while True:
    i += 1
    try:
        print(f'---Iteration {i}---')
        output = None
        times = 0
        url_seed = np.random.choice(seeds)
        ###############------=CHANGE PATH=------###############
        # change this path to where you saved the Chromedriver
        print('--------------------')
        print(f'Creating the scraper for seed: {url_seed}')
        scraper = YouTubeScraper(path_driver=path, profile_path=profile_path, max_wait=max_wait, username=username, password=password, depth=depth, breadth=breadth, trial_id=f'{user}_trial_{uuid.uuid4()}')
        scraper.run_scraper(url_seed)
        print('\n\nDone!')
    except Exception as e:
        print(f'Error ! {e}')

