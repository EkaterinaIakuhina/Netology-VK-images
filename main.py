import requests
import json
import logging
from random import randrange

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    filemode="w",
    format='%(asctime)s %(levelname)s %(message)s')


class VKuser:

    VK_API_URL = 'https://api.vk.com/method'

    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = owner_id

    def __get_common_params(self):
        return {
            'access_token': self.token,
            'v': '5.199',
            'owner_id': self.owner_id
        }

    def get_owner_albums(self):
        '''return list of all ids owners albums'''

        api_method = 'photos.getAlbums'
        params = self.__get_common_params()

        response = requests.get(
            f'{self.VK_API_URL}/{api_method}', params=params)

        if 'error' not in response.json():
            all_albums_ids = []
            for album in response.json()['response']['items']:
                all_albums_ids.append(album['id'])

            logging.info('Successfuly getting albums')
            return all_albums_ids
        else:
            logging.error('Token is not correct', exc_info=True)

    def get_photos_from_album(self, number_photos, album_id='wall'):
        '''return list of photos

        get information from owner concrete album, album_id can be missed then taking from 'wall'

        '''
        api_method = 'photos.get'
        params = self.__get_common_params()
        params.update({
            'album_id': album_id,
            'extended': 1,
            'photo_sizes': 1,
            'count': number_photos
        })

        response = requests.get(
            f'{self.VK_API_URL}/{api_method}', params=params)

        if 'error' not in response.json():
            logging.info(f'Successfuly getting photos from {album_id}')
            return response.json()['response']['items']
        else:
            logging.error('Token is not correct or album_id is not valid')

    def get_photo_with_max_size(self, photo):
        '''return size and url of photo

        find the largest possible size for photo

        '''
        photos_diff_sizes = photo['sizes']
        largest = max(
            photos_diff_sizes,
            key=lambda x: x['width'] *
            x['height'])
        return largest['type'], largest['url']

    def get_likes_of_photo(self, photo):
        '''return count of likes'''

        photos_likes = photo['likes']
        return photos_likes['count']

    def get_id_of_photo(self, photo):
        '''return photos_id'''

        return photo['id']

    def make_name_of_photo(self, photo):
        '''return name of file '''

        # in order to have unique name using id
        return f'{self.get_likes_of_photo(photo)}_{self.get_id_of_photo(photo)}.jpg'

    def save_to_json_from_album(
            self, list_of_photos_info, name_of_json_file=None):
        '''return json file

        need firstly to get photos info from concrete album
        if name_of_json_file is None then create one file and append info to it
        '''

        photos = []
        if list_of_photos_info:
            for photo in list_of_photos_info:
                file_name = owner.make_name_of_photo(photo)
                file_size = self.get_photo_with_max_size(
                    photo)[0]  # return only size
                photos_info = {'file_name': file_name, 'size': file_size}
                photos.append(photos_info)

            with open(f'vk_photos_album_{name_of_json_file}.json', 'a') as file:
                json.dump(photos, file, indent=2)
        else:
            logging.error('Cannot save to json: photos is empty')

    def getting_content_of_photo(self, photo):
        '''return photo binary'''

        photo_url = owner.get_photo_with_max_size(
            photo)[1]  # getting url of photo
        response = requests.get(photo_url)
        photo = response.content

        return photo


class YDUser:

    YD_URL = 'https://cloud-api.yandex.net'

    def __init__(self, YDtoken):
        self.YDtoken = YDtoken
        self.headers = {'Authorization': f'OAuth {YDtoken}'}

    def create_new_folder(self, name):
        '''return name of folder

        creat new folder in YD and return name of it if it is completed
        '''
        params = {'path': name}
        create_url = f'{self.YD_URL}/v1/disk/resources'
        headers = self.headers
        response = requests.put(create_url, params=params, headers=headers)

        if response.status_code == 409:
            logging.error(
                f'The folder {name} is already exists: change the name')
        elif response.status_code != 200 and response.status_code != 201:
            logging.error(f'Error: {response.status_code}')
        else:
            logging.info(f'Folder {name} is created')
            return name

    def add_photos_to_YD(self, name_of_folder, name_of_file, file):
        '''add neccessary file to concrete folder'''

        params = {'path': f'{name_of_folder}/{name_of_file}'}
        add_url = f'{self.YD_URL}/v1/disk/resources/upload'
        headers = self.headers

        response = requests.get(add_url, params=params, headers=headers)
        url_for_load = response.json()['href']

        response = requests.put(url_for_load, files={'file': file})


if __name__ == '__main__':

    vk_access_token = ''
    yandex_token = ''
    user_id = '-143792183'  # vk_group for example with many albums

    # creating vk owner from whom will load photos
    owner = VKuser(token=vk_access_token, owner_id=user_id)
    YDclient = YDUser(yandex_token)  # creating the user of YD

    '''choose two random albums with photos and getting 5 photos from each of them
    name the json file by album_id
    save them to YD disk to new folder named by album_id
    '''
    all_albums = owner.get_owner_albums()
    for i in range(2):
        if all_albums: 
            number = randrange(0, len(all_albums))
            album_id = all_albums[number]

            photos = owner.get_photos_from_album(5, album_id)
            owner.save_to_json_from_album(photos, album_id)

            name_of_folder = YDclient.create_new_folder(album_id)

            for photo in photos:
                photo_name = owner.make_name_of_photo(photo)
                photo = owner.getting_content_of_photo(photo)

                YDclient.add_photos_to_YD(
                    name_of_folder,
                    photo_name,
                    photo)  # saving photo fo YD