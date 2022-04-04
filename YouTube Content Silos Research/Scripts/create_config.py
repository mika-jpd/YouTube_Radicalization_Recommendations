import json
import os
import getpass


def breadth():
    for i in range(51, 71):
        if i <= 55:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscraper{i - 50}@yandex.com',
                'password': f'396ytscraper{i-50}!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 180,
                'num_reco': 5,
                'depth': 3,
                'videos_parallele': 14
            }
        else:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscrapercsuser{i - 50}@yandex.com',
                'password': f'396ytscraper{i - 50}!!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 180,
                'num_reco': 5,
                'depth': 3,
                'videos_parallele': 14
            }
        with open(f"{os.getcwd()}\\Configuration Files\\Configuration Breadth\\config_csuser{i}.json", "w") as outfile:
            json.dump(data, outfile)

def depth():
    for i in range(51, 71):
        if i <= 55:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscraper{i - 50}@yandex.com',
                'password': f'396ytscraper{i-50}!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 30,
                'depth': 5,
                'profile path': None
            }
        else:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscrapercsuser{i - 50}@yandex.com',
                'password': f'396ytscraper{i - 50}!!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 30,
                'depth': 5,
                'profile path': None
            }
        with open(f"{os.getcwd()}\\Configuration Files\\Configuration Depth\\config_depth_csuser{i}.json", "w") as outfile:
            json.dump(data, outfile)

def survey():
    for i in range(51, 71):
        if i <= 55:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscraper{i - 50}@yandex.com',
                'password': f'396ytscraper{i-50}!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 30,
                'depth': 3,
                'breadth':6,
                'path csv': 'channel_review.csv',
                'profile path': None
            }
        else:
            data = {
                'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
                'username': f'ytscrapercsuser{i - 50}@yandex.com',
                'password': f'396ytscraper{i - 50}!!',
                'Seeds': f'seedscsuser{i}',
                'max_wait': 30,
                'depth': 3,
                'breadth':6,
                'path csv': 'channel_review.csv',
                'profile path': None
            }
        #add bias later
        if i <=57:
            data['bias'] = 'Left'
            data['political bias array'] = ["SocialJustice", 'Socialist', 'PartisanLeft']
            data['opposing array'] = ['AntiSJW', 'Conspiracy', 'PartisanRight', 'ReligiousConservative', 'WhiteIdentitarian', 'Libertarian', 'MRA']
        else:
            data['bias'] = 'Right'
            data['opposing array'] = ["SocialJustice", 'Socialist', 'PartisanLeft']
            data['political bias array'] = ['AntiSJW', 'Conspiracy', 'PartisanRight', 'ReligiousConservative',
                                      'WhiteIdentitarian', 'Libertarian', 'MRA']
        with open(f"{os.getcwd()}\\Configuration Files\\Configuration Survey\\config_survey_csuser{i}.json", "w") as outfile:
            json.dump(data, outfile)

def info():
    for i in range(51, 71):
        data = {
            'path': f'/home/socs/csuser{i}/.wdm/drivers/chromedriver/linux64/97.0.4692.71/chromedriver',
            'Seeds': f'videos_to_visit_csuser{i}.txt'
        }
        with open(f"{os.getcwd()}\\Configuration Files\\Configuration Info\\config_info_csuser{i}.json", "w") as outfile:
            json.dump(data, outfile)

info()
print('Done')