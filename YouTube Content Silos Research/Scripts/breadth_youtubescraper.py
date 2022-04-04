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


class YouTubeScraper:
    def __init__(self, path_driver, profile_path, history=False):
        self.path = path_driver
        self.profile_path = profile_path
        self.driver = self.create_chrome_driver()

        self.homepage = []
        self.depth = 0
        self.seed_url = None
        self.history = history
        self.max_wait = None
        self.trial_id = None
        self.num_recommendations = None
        self.username = None
        self.password = None
        self.tree = None

    def create_chrome_driver(self):
        options = webdriver.ChromeOptions()
        # print('Creating options')
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
        options.add_argument('--headless')
        s = Service(self.path)
        try:
            return webdriver.Chrome(service=s, options=options)
        except:
            return webdriver.Chrome(executable_path=self.path, options=options)

    ###### Video Processing #################
    async def videos_handling(self, url_list: list, main_tab: str, results: list):
        # print('videos_handling')
        tasks = []
        for url, i in zip(url_list, list(range(0, len(url_list)))):
            # open new tab and pass it for new video to watch
            self.driver.execute_script("window.open('');")
            new_tab = self.driver.window_handles.pop()

            tasks.append(self.video_processing(url=url, main_tab=main_tab, current_tab=new_tab, res=results, index=i))
        await asyncio.gather(*tasks)

    # here you watch a single video at a time
    async def video_processing(self, url: str, main_tab: str, current_tab: str, res: list, index: int):
        print('video processing')
        try:
            self.driver.switch_to.window(current_tab)
            self.driver.get(url)
            # wait for the video to be loaded
            time.sleep(1)
            # skip the data protection button if it appears
            try:
                self.driver.find_elements(by=By.XPATH, value='//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[4]/form/div[1]/div/button/span')[0].click()
            except:
                # skip the data protection button if it appears
                try:
                    self.driver.find_elements(by=By.XPATH, value= '/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[2]/div[2]/div[5]/div[2]/ytd-button-renderer[2]/a/tp-yt-paper-button/yt-formatted-string')[0].click()
                except:
                    pass
                pass
            # skip ad
            time.sleep(2)
            ad = None
            while (self.check_ad() == True):
                ad = True
                self.skip_ad()
                time.sleep(2)
            # change to just check whether the video is playing or not (ie. if the big button is discoverable & no ads)
            if (ad == None):
                self.start_video()

            # collect the features
            video = self.collect_data(url=url, ads=ad)
            # watch the video for a little, simulate a person
            try:
                await asyncio.sleep(min(video['video_length'], self.max_wait))
            except:
                video['video_length'] = None

            # get the recommended videos
            recommended = self.get_video_recommendations(parent_url=url, main_tab=main_tab, current_tab = current_tab)

            self.driver.switch_to.window(current_tab)
            self.driver.close()
            self.driver.switch_to.window(main_tab)

            res[index] = (video, recommended)
        except:
            res[index] = ('Error found', 'Error found')

        print(f'     -video processing: {video["title"]} by {video["content creator"]}, {video["video_length"]}')

    def start_video(self):
        # click on the button to start if the video is not playing (ie. if there were no ads before it)
        try:
            element = self.driver.find_element(by= By.XPATH, value= "//button[@class='ytp-large-play-button ytp-button']")
            element.click()
        except ElementNotInteractableException:
            pass

    # checks if there's an ad playing or not
    def check_ad(self) -> bool:
        ads = self.driver.find_elements(by= By.CSS_SELECTOR, value= 'button[id^=visit-advertiser] > span.ytp-ad-button-text')
        if (len(ads) == 0):
            return False
        else:
            return True

    def skip_ad(self):
        time.sleep(5)
        # wait for the end of the advertisement
        try:
            # first make sure it can be skipped by finding the ad text button
            element = self.driver.find_elements(by= By.XPATH, value= '//*[contains(@id, "ad-text:")]')
            for i in element:
                # my code works for both french YouTube and anglohpone YouTube
                if (i.text == 'Skip Ads' or i.text == 'Skip Ad' or i.text == "Passer les annonces" or i.text == "Ignorer l'annonce"):
                    self.driver.find_elements(by= By.XPATH, value= '//*[@class="ytp-ad-skip-button ytp-button"]')[0].click()
                    break
        except TimeoutException:
            pass

    def get_length(self):
        try:
            return self.driver.execute_script("return document.getElementById('movie_player').getDuration()")
        except:
            return "Error found"
    def login(self, main_tab, username, password):
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

            self.driver.get('https://accounts.google.com/signin/v2/identifier?hl=en&continue=https%3A%2F%2Fwww.google.com%2Fsearch%3Fq%3Dgoogle%2Bsign%2Bin%26rlz%3D1C1CHBF_enCA883CA883%26oq%3Dgoogle%2Bsign%2Bin%26aqs%3Dchrome..69i57j69i64l2j69i60l3.2918j0j1%26sourceid%3Dchrome%26ie%3DUTF-8&gae=cb-none&flowName=GlifWebSignIn&flowEntry=ServiceLogin')
            time.sleep(5)

            print('     -logging in -', end='')

            # Just in case you didn't log in
            if not (self.driver.current_url == "https://www.google.com/search?q=google+sign+in&rlz=1C1CHBF_enCA883CA883&oq=google+sign+in&aqs=chrome..69i57j69i64l2j69i60l3.2918j0j1&sourceid=chrome&ie=UTF-8&pli=1"):
                print('     - manually:', end='')
                for i in username:
                    WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Email"]'))).send_keys(i)
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

                for i in password:
                    WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]'))).send_keys(i)
                    time.sleep((np.random.randint(1, 3)) / 10)

                WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit"]'))).click()

            stealth(self.driver,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36',
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
            time.sleep(2)
            #print('opening window')
            self.driver.execute_script("window.open('https://www.youtube.com/')")

            self.driver.switch_to.window(self.driver.window_handles[1])
            #print('looking for notifications')
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="img"]')))
            #print('switch handle1')

            #print('okay')

            #print('switch window 0')
            self.driver.switch_to.window(self.driver.window_handles[0])

            #print('okay')

            #print('closing')
            self.driver.close()
            #print('popping')
            main_tab = self.driver.window_handles.pop()
            self.driver.switch_to.window(main_tab)

            print(' login success!')
            return main_tab
        except Exception as e:
            print(', error not fixed')
            return_statement = f'Error logging in: {e}'
            raise ElementNotInteractableException(msg=return_statement)

    def delete_history(self, main_tab):
        print('     -deleting history:', end='')

        # open window and navigate to the webpage
        self.driver.execute_script("window.open('https://myactivity.google.com/activitycontrols/youtube?hl=en&utm_source=privacy-advisor-youtube')")
        time.sleep(2)
        new_tab = self.driver.window_handles.pop()
        self.driver.switch_to.window(new_tab)
        try:
            time.sleep(2)
            #print('1')
            delete = WebDriverWait(self.driver, 10, ignored_exceptions=(StaleElementReferenceException)).until(EC.presence_of_element_located((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[2]/div/div[2]/div[2]/span/div[2]/c-wiz[1]/div/div/div/div/div[4]/div/div[1]/div/button/span')))
            time.sleep(2)
            delete.click()

            time.sleep(2)
            #print('2')
            delete_all_time = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[2]/div/div[2]/div[2]/span/div[2]/c-wiz[1]/div/div/div/div/div[4]/div/div[2]/div/ul/li[3]/span[2]')))
            delete_all_time.click()

            # if this doesn't go through then we haven't watched any videos
            try:
                #print('3')
                time.sleep(2)
                confirm_delete = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="yDmH0d"]/div[8]/div/div[2]/span/div[2]/div/c-wiz/div/div[4]/div/div[2]/button/span')))
                confirm_delete.click()
                delete_confirmation = self.driver.find_elements(by=By.XPATH, value='//*[@id="yDmH0d"]/div[8]/div/div[2]/span/div[2]/div/c-wiz/div/div[4]/div/div/button/span')
                if len(delete_confirmation) > 0:
                    print('success')
            except Exception as e:
                print(f' no history to delete')
        except Exception as e:
            return_statement = f' history delete error: {e}'
            raise ElementNotInteractableException(msg=return_statement)

        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        main_tab = self.driver.window_handles[0]
        return main_tab

    def collect_data(self, url: str, ads: bool):

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

        # tags = self.get_tags(soup=soup)

        ads = ads

        video = {
            'title': title,
            'content creator': creator,
            'description': description,
            'date': dates,
            'views': views,
            'comments': number_comments,
            'likes': likes,
            'dislikes': dislikes,
            # 'tags':tags,
            'video_length': length,
            'url': url,
            'ad': ads,
            'id': id
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
            tags = ', '.join([meta.attrs.get("content") for meta in soup.find_all(
                "meta", {"property": "og:video:tag"})])
            return tags
        except:
            return 'Error found'

    def get_likes_dislikes(self) -> str:
        try:
            result = [i.get_attribute("aria-label") for i in self.driver.find_elements(by= By.XPATH, value= '//yt-formatted-string[@id="text"]') if i.get_attribute("aria-label") != None]

            likes = [i for i in result if (
                    'like' in i) and ('dislike' not in i)]
            dislikes = [i for i in result if ' dislike' in i]

            return likes[0] if (len(likes) != 0) else 'Unavailable', dislikes[0] if (
                        len(dislikes) != 0) else ' Unavailable'
        except:
            return 'Error found'

    def get_title(self) -> str:
        try:
            return self.driver.find_elements(by= By.XPATH, value= '//*[@id="container"]/h1/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_creator(self) -> str:
        try:
            return self.driver.find_elements(by= By.XPATH, value= '//*[@id="text"]/a')[0].text
        except:
            return 'Error found'

    def get_views(self) -> str:
        try:
            return self.driver.find_elements(by= By.XPATH, value= '//*[@id="count"]/ytd-video-view-count-renderer/span[1]')[0].text
        except:
            return 'Error found'

    def get_description(self) -> str:
        try:
            return self.driver.find_elements(by= By.XPATH, value= '//*[@id="description"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_date(self) -> str:
        try:
            return self.driver.find_elements(by= By.XPATH, value= '//*[@id="info-strings"]/yt-formatted-string')[0].text
        except:
            return 'Error found'

    def get_video_recommendations(self, parent_url: str, main_tab, current_tab) -> list:
        self.driver.switch_to.window(current_tab)
        #print('     -recommended', end='')
        recommended_videos = []
        x = 0
        # find the video in the tree
        node = anytree.search.find(self.tree,
                                   filter_=lambda node: node.id == parent_url)
        path = '//*[@id="related"]/ytd-watch-next-secondary-results-renderer//*[@id="thumbnail"]'
        recommendations = self.driver.find_elements(by= By.XPATH, value= path)
        for i in recommendations:
            video_url = i.get_attribute('href')

            # only add the videos not seen before
            if (anytree.search.find(self.tree, filter_=lambda node: node.id == video_url) == None) and not (
                    video_url in recommended_videos) and not (video_url == None):
                recommended_videos.append(video_url)

                # add recommended videos as children
                AnyNode(id=video_url, parent=node, video=None, title=None)
                x += 1
            else:
                continue
            if (x == self.num_recommendations):
                break

        # figure out depth of the new node for the homepage_snapshot
        node = self.tree
        depth = 0
        while len(node.children) != 0:
            node = node.children[len(node.children) - 1]
            depth += 1

        # since we fill the tree
        if depth > self.depth:
            videos = self.homepage_snapshot(main_tab)
            self.homepage.append(videos)
            self.depth += 1

        return recommended_videos

    def get_by_xpath(self, xpath):
        try:
            return self.driver.find_element(by= By.XPATH, value= xpath)
        except:
            return 'Error found'

    def homepage_snapshot(self, main_tab):
        print('     -homepage')
        self.driver.switch_to.window(main_tab)
        time.sleep(2)
        # reload YouTube homepage
        self.driver.get('https://www.youtube.com/')
        time.sleep(3)
        # will contain list of 20 ish videos of the homepage
        elements = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contents"]/ytd-rich-grid-row//*[@id="contents"]//*[@id="thumbnail"]')))
        videos = [i.get_attribute('href') for i in elements]

        print('         -success')
        return videos

    def geometric_series_calc(self, num_reco: int, depth: int) -> int:
        x = 0
        for i in range(0, depth):
            x = x + num_reco ** i
        return x

    # breadth-first run of the scraper: goes level by level and gets the recommended videos like a tree
    def run_scraper(self, url_seed: str, max_wait: int, username: str, password: str, num_reco: int, depth: int,
                    videos_parallele: int, trial_id: str):
        print('     -running scraper')
        queue = deque([url_seed])
        root = AnyNode(id=url_seed, parent=None, video=None, title=None)
        self.tree = root
        self.max_wait = max_wait
        self.username = username
        self.password = password
        self.num_recommendations = num_reco

        main_window = self.driver.window_handles[-1]

        main_window = self.login(main_tab=main_window,
                                 username=self.username,
                                 password=self.password)
        main_window = self.delete_history(main_tab=main_window)

        # will have reloaded right before this call
        self.homepage.append(self.homepage_snapshot(main_tab=main_window))

        num_limit = self.geometric_series_calc(num_reco=num_reco, depth=depth)
        videos_watched = []

        iteration = 0
        while ((num_limit - len(videos_watched)) != 0):
            self.driver.quit()

            # restart driver and login to speed up the process
            self.driver = self.create_chrome_driver()
            main_window = self.driver.window_handles[-1]
            main_window = self.login(main_tab=main_window,
                                     username=self.username,
                                     password=self.password)

            print(f'----Iteration {iteration}----')
            iteration = iteration + 1

            # array of video urls to watch
            tasks = []
            # determines how many videos will be watched at the same time
            to_watch = min(videos_parallele, len(queue),
                           num_limit - len(videos_watched))

            for i in range(0, to_watch):
                x = queue.popleft()
                tasks.append(x)
                videos_watched.append(x)

            # this array will receive the results of the scraping
            results = [None for i in tasks]
            asyncio.run(self.videos_handling(url_list=tasks,
                                             main_tab=main_window, results=results), debug=True)

            for r in results:
                if r[0] != 'Error found':
                    node = None
                    # find the node with the url since it is stored in the tree before it is watched
                    if (root.video == None):
                        root.video = r[0]
                        root.title = r[0]['title']
                        node = root
                    else:
                        for n in anytree.LevelOrderIter(root):
                            if (n.id == r[0]['url']):
                                node = n
                                node.title = r[0]['title']
                                node.video = r[0]
                            else:
                                continue
                    for i in r[1]:
                        queue.append(i)
            print('')
        # check whether you need to refresh here or not
        self.homepage.append(self.homepage_snapshot(main_tab=main_window))

        print(RenderTree(self.tree, style=ContStyle()))
        # ---Save results to a CSV file----
        print('     -writing to file')
        path_to_directory = f'{os.getcwd()}/Breadth'

        # put homepage in directory
        for i in range(0, len(self.homepage)):
            path_to_file = f'{path_to_directory}/homepage/homepage_{i}_{trial_id}.txt'
            with open(path_to_file, 'w+') as outfile:
                for element in self.homepage[i]:
                    if isinstance(element, str):
                        outfile.write(element + '\n')
            outfile.close()

        # put tree into file
        path_to_file = f'{path_to_directory}/tree/tree_{trial_id}.txt'
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open(path_to_file, 'w+') as outfile:
            exporter.write(root, outfile)
        outfile.close()



# Setup
user = getpass.getuser()

with open(f"config_{user}.json") as json_data_file:
    data = json.load(json_data_file)

username = data['username']
password = data['password']
path = data['path']
profile_path = data["profile path"]

max_wait = data['max_wait']
num_reco = data['num_reco']
depth = data['depth']
videos_parallele = data['videos_parallele']


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
print(f'     -num reco: {num_reco}')
print(f'     -depth: {depth}')
print(f'     -videos parallele: {videos_parallele}')
print('Enjoy!')

for url_seed in range(0, len(seeds)):
    output = None
    times = 0
    while output != 1:
        try:
            ###############------=CHANGE PATH=------###############
            # change this path to where you saved the Chromedriver
            print('##################################\n##################################\n')
            print(f'Creating the scraper for seed: {seeds[url_seed]}')
            scraper = YouTubeScraper(path_driver=path, profile_path=profile_path)
            scraper.run_scraper(url_seed=seeds[url_seed],
                                max_wait=max_wait,
                                # change username and password
                                username=username,
                                password=password,
                                num_reco=num_reco,
                                depth=depth,
                                videos_parallele=videos_parallele,

                                # make your own trial_id
                                trial_id=f'{user}_trial_{uuid.uuid4()}')
            scraper.driver.quit()
            print('\n\nDone!')

            output = 1
            times += 1
        except Exception as e:
            print('\n\nStarting again !')
            scraper.driver.quit()
            if times > 5:
                raise Exception(f'Multiple attempts to run the scraper failed. \nLast error was : {sys.exc_info()[2]}')
            print(f'error: {e}\n{sys.exc_info()[2]}')

