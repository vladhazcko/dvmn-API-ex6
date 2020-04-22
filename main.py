import requests
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
FILES_DIRECTORY = 'files/'
VK_ACCESS_KEY = os.getenv('VK_ACCESS_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')


def main():
    comic = get_random_comic()
    comic_img_url = comic['img']
    comic_img_path = comic_img_url.split('/')[-1]
    comic_img_alt = comic['alt']
    file_path = download_file(comic_img_url, comic_img_path)

    uploaded_server = send_request_vk('photos.getWallUploadServer')
    url = uploaded_server['response']['upload_url']
    with open(file_path, 'rb') as file:
        uploaded_photo_params = upload_photo_vk(file, url)

    uploaded_photo = send_request_vk('photos.saveWallPhoto',
                                     params=uploaded_photo_params,
                                     http_method='post')['response']

    attachments = f'photo{uploaded_photo[0]["owner_id"]}_{uploaded_photo[0]["id"]}'
    send_request_vk('wall.post', http_method='post', params={
                                           'owner_id': '-' + VK_GROUP_ID,
                                           'from_group': 1,
                                           'message': comic_img_alt,
                                           'attachments': attachments
                                       })
    os.remove(file_path)


def download_file(url, path, prefix_name='', directory=FILES_DIRECTORY):
    response = requests.get(url)
    response.raise_for_status()

    Path(directory).mkdir(parents=True, exist_ok=True)
    file_path = directory + path
    with open(file_path, 'wb') as file:
        file.write(response.content)

    return file_path


def get_random_comic():
    base_url = 'https://c.xkcd.com/random/comic/'
    response_comic_url = requests.get(base_url)
    response_comic_url.raise_for_status()
    comic_url_data = response_comic_url.url + 'info.0.json'

    response_data = requests.get(comic_url_data)
    response_data.raise_for_status()
    return response_data.json()


def send_request_vk(method_name, access_token=VK_ACCESS_KEY,
                    params=None, http_method='get'):
    if params is None:
        params = {}

    api_version = 5.103
    host = 'https://api.vk.com/method/'
    params['access_token'] = access_token
    params['v'] = api_version
    request_url = host + method_name

    if http_method == 'get':
        response = requests.get(request_url, params)
    else:
        response = requests.post(request_url, params)
    response.raise_for_status()
    return response.json()


def upload_photo_vk(file, url):
    files = {
        'photo': file
    }
    response = requests.post(url, files=files)
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    main()
