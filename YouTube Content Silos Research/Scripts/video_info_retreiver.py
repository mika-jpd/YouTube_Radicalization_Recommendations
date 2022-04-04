import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import asyncio
import getpass
import uuid

class VideoInfoRetreiver:
    def __init__(self, path_to_driver, video_urls, id):
        self.path_to_driver = path_to_driver
        self.video_urls = [i for i in video_urls]
        self.id = id
        self.video_information = {}
        self.driver = None

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

        # comment out in order to see the scraper interacting with webpages
        options.add_argument('--headless')
        s = Service(self.path_to_driver)
        try:
            return webdriver.Chrome(service=s, options=options)
        except:
            return webdriver.Chrome(executable_path=self.path_to_driver, options=options)

    async def process_videos(self):
        # while it's not empty
        batch = 0
        while len(self.video_urls) > 0:
            self.driver = self.create_chrome_driver()
            main_tab = self.driver.current_window_handle
            # pop the first 14
            tasks = []
            to_watch = min(12, len(self.video_urls))
            for i in range(0, to_watch):
                url = self.video_urls.pop(0)
                self.driver.execute_script(f"window.open('{url}')")
                current_tab = self.driver.window_handles[-1]
                tasks.append(self.collect_data(url, current_tab))

            print(f'--Batch {batch}--', flush=True)
            await asyncio.gather(*tasks)
            self.driver.quit()
            time.sleep(5)
            batch += 1
        # Now you have to write to a file

        with open(f'video_info_dictionairies_{self.id}_{uuid.uuid4()}.json', 'w+') as outfile:
            json.dump(self.video_information, outfile)
        print('Done')


    async def collect_data(self, url: str, current_tab):
        await asyncio.sleep(5)
        attempts = 0
        video = {
            'content creator': 'Error',
            'title': 'Error',
            'views': 'Error'
        }
        try:
            start = time.time()
            while ('Error' in video['content creator'] or 'Error' in video['title'] or 'Error' in video['views']) and attempts < 3:
                attempts += 1
                self.driver.switch_to.window(current_tab)

                length = self.get_length()

                self.driver.execute_script('window.scrollTo(0, 540)')

                title = self.get_title()
                creator = self.get_creator()
                description = self.get_description()
                dates = self.get_date()
                views = self.get_views()
                number_comments = self.get_num_comments()

                likes, dislikes = None, None
                try:
                    likes, dislikes = self.get_likes_dislikes()
                except:
                    pass

                video = {
                    'title': title,
                    'content creator': creator,
                    'description': description,
                    'date': dates,
                    'views': views,
                    'comments': number_comments,
                    'likes': likes,
                    'dislikes': dislikes,
                    'video_length': length,
                    'url': url,
                }

            self.video_information[url] = video
            print(self.video_information[url]['content creator'], url)
            self.driver.close()
            end = time.time()
            print('     -collected video:')
            print(f'         content creator{video["content creator"]}')
            print(f'         time: {end-start}')
            print(f'         attempt: {attempts}', flush=True)
        except Exception as e:
            print(f'     - There was an error {e}', flush=True)

    def get_num_comments(self) -> str:
        try:
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="count"]/yt-formatted-string/span[1]')))
            element = element.text
            return element
        except Exception as e:
            return f'Error found: {e}'

    def get_tags(self, soup):
        # open("index.html", "w").write(response.html.html)
        # initialize the result
        try:
            tags = ', '.join([meta.attrs.get("content") for meta in soup.find_all(
                "meta", {"property": "og:video:tag"})])
            return tags
        except Exception as e:
            return f'Error found: {e}'


    def get_likes_dislikes(self) -> str:
        try:
            result = [i.get_attribute("aria-label") for i in
                      self.driver.find_elements(By.XPATH, '//yt-formatted-string[@id="text"]') if
                      i.get_attribute("aria-label") != None]

            likes = [i for i in result if (
                    'like' in i) and ('dislike' not in i)]
            dislikes = [i for i in result if ' dislike' in i]

            return likes[0] if (len(likes) != 0) else 'Unavailable', dislikes[0] if (len(dislikes) != 0) else ' Unavailable'
        except Exception as e:
            return f'Error found: {e}'


    def get_title(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="container"]/h1/yt-formatted-string')[0].text
        except Exception as e:
            return f'Error found: {e}'


    def get_creator(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="text"]/a')[0].text
        except Exception as e:
            return f'Error found: {e}'


    def get_views(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="count"]/ytd-video-view-count-renderer/span[1]')[0].text
        except Exception as e:
            return f'Error found: {e}'


    def get_description(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="description"]/yt-formatted-string')[0].text
        except Exception as e:
            return f'Error found: {e}'


    def get_date(self) -> str:
        try:
            return self.driver.find_elements(By.XPATH, '//*[@id="info-strings"]/yt-formatted-string')[0].text
        except Exception as e:
            return f'Error found: {e}'

    def get_length(self):
        try:
            return self.driver.execute_script("return document.getElementById('movie_player').getDuration()")
        except Exception as e:
            return f'Error found: {e}'

user = getpass.getuser()
with open(f"Configuration Files\\Configuration mikad\\config_info_{user}.json") as json_data_file:
    data = json.load(json_data_file)

seed_file = open(data['Seeds'], 'r')
seeds = seed_file.read()
seeds = seeds.split('\n')

path = data['path']

print('Welcome to the YouTube scraper!')
print(f'{user}, you are running the scraper with parameters:')
print(f'     -path: {path}')
print(f'     - Seeds name: {data["Seeds"]}')
print(f'     -: Seeds {len(seeds)}')
print('Enjoy!', flush=True)

video_retreiver = VideoInfoRetreiver(path_to_driver=path, video_urls=seeds, id=user)
asyncio.run(video_retreiver.process_videos())
print('Done')