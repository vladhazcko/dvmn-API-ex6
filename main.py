import requests
from pathlib import Path
import os
from dotenv import load_dotenv

FILES_DIRECTORY = 'files/'


def main():
    load_dotenv()
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')

    comic = get_random_comic()
    comic_img_url = comic['img']
    comic_img_path = comic_img_url.split('/')[-1]
    comic_img_alt = comic['alt']
    file_path = download_file(comic_img_url, comic_img_path)
    try:
        uploaded_server = send_request_vk('photos.getWallUploadServer', vk_access_token)
        url = uploaded_server['response']['upload_url']
        with open(file_path, 'rb') as file:
            uploaded_photo_params = upload_photo_vk(file, url)

        uploaded_photo = send_request_vk('photos.saveWallPhoto', vk_access_token,
                                         params=uploaded_photo_params,
                                         http_method='post')['response']

        attachments = f'photo{uploaded_photo[0]["owner_id"]}_{uploaded_photo[0]["id"]}'
        send_request_vk('wall.post', vk_access_token, http_method='post', params={
            'owner_id': '-' + vk_group_id,
            'from_group': 1,
            'message': comic_img_alt,
            'attachments': attachments
        })
    finally:
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


def send_request_vk(method_name, access_token,
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
    return check_response_status_vk(response)


def upload_photo_vk(file, url):
    files = {
        'photo': file
    }
    response = requests.post(url, files=files)
    return check_response_status_vk(response)


def check_response_status_vk(response: requests.models.Response):
    response.raise_for_status()
    response_data = response.json()
    if 'error' in response_data:
        raise requests.exceptions.HTTPError(response_data['error'])
    return response_data


if __name__ == '__main__':
    main()
