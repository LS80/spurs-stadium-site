#!/usr/bin/python3.5

from datetime import datetime, time, timedelta
from urllib.parse import urljoin
from time import sleep
import json
from collections import defaultdict
import logging

from imgurpython import ImgurClient
import requests

import config

HEADERS = {
    'Authorization': 'Basic dGhfc3RhZGl1bTp5Vm13elIzZ3Z3V0w=',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
}
JSON_URL_ROOT = 'https://www.siteeyearchive2.co.uk/api/1.0/images/project/319/'
IMAGE_URL_FMT = ('http://new-stadium.tottenhamhotspur.com/wp-content/plugins/live-feed/callback/'
                 'image.php?camera={}&image={}?')

CLIENT_ID = '3f174d92740022d'
CLIENT_SECRET = 'd5b512767da5f09ba344d9e7780b747439d81076'

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

def latest_image_metadata(camera_id):
    today = datetime.today()
    start, end = (dt.strftime('%y%m%d') for dt in [today - timedelta(days=1), today])
    url_images_json = urljoin(
        JSON_URL_ROOT,
        'camera/{}/start/{}/end/{}'.format(camera_id, start, end)
    )
    response = requests.get(url_images_json, headers=HEADERS)
    if response:
        image = response.json()[-1]
        return int(image['id']), image['dateTaken']

def download_image(camera_id, image_id):
    url = IMAGE_URL_FMT.format(camera_id, image_id)
    raw_response = requests.get(url, stream=True).raw
    logging.info('Downloading {}'.format(url))
    return raw_response

def upload(fd, camera, date_taken):
    client = ImgurClient(CLIENT_ID, CLIENT_SECRET)
    config = {
        'title': 'New Spurs Stadium Camera {}'.format(camera),
        'description': 'New Tottenham Hotspur stadium build camera {} at {}'.format(
            camera, date_taken
        )
    }
    return client.upload(fd, config=config)['link']

def default_image():
    return dict(id=0, dateTaken=None, url=None)

def images_metadata():
    try:
        with open(config.IMAGES_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return defaultdict(default_image)

def write_images_metadata(images_data):
    with open(config.IMAGES_FILE, 'w') as f:
        json.dump(images_data, f)

def update():
    metadata = images_metadata()
    for camera_num, camera_id in enumerate(config.CAMERAS, start=1):
        image_metadata = metadata[str(camera_id)]
        latest_image = latest_image_metadata(camera_id)
        if latest_image:
            latest_image_id, latest_image_datetime = latest_image
            logging.debug(
                'Latest image for camera {}: {} {}'.format(
                    camera_num, latest_image_id, latest_image_datetime
                )
            )
            if latest_image_id > image_metadata['id']:
                image_data = download_image(camera_id, latest_image_id)
                url = upload(image_data, camera_num, latest_image_datetime)
                logging.info('Camera {} image uploaded to {}'.format(camera_num, url))
                image_metadata['id'] = latest_image_id
                image_metadata['dateTaken'] = latest_image_datetime
                image_metadata['url'] = url
            else:
                logging.info('Camera {} image up to date'.format(camera_num))
        write_images_metadata(metadata)
        logging.info('Sleeping until next update...')
        sleep(10)

if __name__ == '__main__':
    while datetime.now().time() <= time(hour=22, minute=00):
        update()
