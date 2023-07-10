import json
import os.path
import requests
import youtube_dl
from config import TOKEN


def download_video(url, post_id, group_name, max_video_duration):
    """Функция загрузки видео из поста"""

    if not os.path.exists(f'{group_name}/videos'):
        os.mkdir(f'{group_name}/videos')

    try:
        ydl_options = {'outtmpl': f'{group_name}/videos/{post_id}'}
        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            video_info = ydl.extract_info(url, download=False)
            video_duration = video_info['duration']
            if video_duration > max_video_duration * 60:
                return '[ОШИБКА] Видео слишком долгое!'
            else:
                ydl.download([url])
                return f'[УСПЕХ] Видео получено!'

    except Exception as _ex:
        print('[ОШИБКА] Не удалось скачать видео!')


def download_image(url, post_id, group_name):
    """Функция загрузки изображения из поста"""

    image_request = requests.get(url)
    print(image_request)

    if not os.path.exists(f'{group_name}/images'):
        os.mkdir(f'{group_name}/images')

    with open(f'{group_name}/images/{post_id}.jpg', 'wb') as file:
        file.write(image_request.content)

    return '[УСПЕХ] Изображение получено!'


def get_wall_posts(group_name, posts_get_count, max_video_duration):
    """Основная функция для парсинга страницы"""

    url = f'https://api.vk.com/method/wall.get?domain={group_name}&count={posts_get_count}&access_token={TOKEN}&v=5.131'
    request_from_wall = requests.get(url).json()

    if not os.path.exists(group_name):
        os.mkdir(group_name)

    with open(f'{group_name}/{group_name}.json', 'w', encoding='utf-8') as file:
        json.dump(request_from_wall, file, indent=4, ensure_ascii=False)

    received_posts_id = []
    all_posts_from_wall = request_from_wall['response']['items']

    for post in all_posts_from_wall:
        received_posts_id.append(post['id'])

    if not os.path.exists(f'{group_name}/exists_posts_{group_name}.txt'):
        print(f'[ИНФОРМАЦИЯ] Файла с ID постов для группы ({group_name}) не существует, создаем файл!')

        with open(f'{group_name}/exists_posts_{group_name}.txt', 'w', encoding='utf-8') as file:
            for post_id in received_posts_id:
                file.write(str(post_id) + '\n')

        current_counter_post = 1

        for post in all_posts_from_wall:
            post_id = post['id']
            print(f'[ПРОГРЕСС] Обработка поста с ID {post_id}')

            try:
                if 'attachments' in post:
                    post = post['attachments']
                    post_type = post[0]['type']

                    if len(post) == 1:
                        if post_type == 'photo':
                            print('[ИНФОРМАЦИЯ] Найден пост с изображением!')
                            photo_url = post[0]['photo']['sizes'][-1]['url']
                            print(download_image(url=photo_url, post_id=post_id, group_name=group_name))

                        elif post_type == 'video':
                            print('[ИНФОРМАЦИЯ] Найден пост с видео!')
                            video_access_key = post[0]['video']['access_key']
                            video_post_id = post[0]['video']['id']
                            video_owner_id = post[0]['video']['owner_id']

                            video_get_url = f'https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&access_token={TOKEN}&v=5.131'
                            video_request = requests.get(video_get_url).json()

                            video_url = video_request['response']['items'][0]['player']
                            print(download_video(url=video_url, post_id=post_id, group_name=group_name, max_video_duration=max_video_duration))

                        else:
                            print('[ИНФОРМАЦИЯ] Пост с аудио, ссылкой или др')

                    else:
                        print('[ИНФОРМАЦИЯ] Найден пост с несколькими объектами!')
                        photo_in_post_count = 1

                        for item_in_post in post:
                            if item_in_post['type'] == 'photo':
                                photo_url = item_in_post['photo']['sizes'][-1]['url']
                                item_id_counter = str(post_id) + f'_{photo_in_post_count}'
                                print(download_image(url=photo_url, post_id=item_id_counter, group_name=group_name))
                                photo_in_post_count += 1

                            elif item_in_post['type'] == 'video':
                                video_access_key = item_in_post['video']['access_key']
                                video_post_id = item_in_post['video']['id']
                                video_owner_id = item_in_post['video']['owner_id']

                                video_get_url = f'https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&access_token={TOKEN}&v=5.131'
                                video_request = requests.get(video_get_url).json()

                                video_url = video_request['response']['items'][0]['player']
                                print(download_video(url=video_url, post_id=post_id, group_name=group_name, max_video_duration=max_video_duration))

                            else:
                                print('[ИНФОРМАЦИЯ] Пост с аудио, ссылкой или др')

            except Exception as _ex:
                print(_ex)

            print(f'[ПРОГРЕСС] Обработан пост {current_counter_post}/{posts_get_count}')
            current_counter_post += 1

    else:
        print(f'Файл с ID постов для группы ({group_name}) найден, начинаем выборку свежих постов')

        with open(f'{group_name}/exists_posts_{group_name}.txt', 'r', encoding='utf-8') as file:
            exists_posts_from_wall = [int(i.strip()) for i in file.readlines()]

        new_posts_from_wall = []

        for post_id in received_posts_id:
            if post_id not in exists_posts_from_wall:
                new_posts_from_wall.append(post_id)

        with open(f'{group_name}/exists_posts_{group_name}.txt', 'w', encoding='utf-8') as file:
            for post_id in new_posts_from_wall:
                file.write(str(post_id) + '\n')

        current_counter_post = 1

        for post in all_posts_from_wall:
            post_id = post['id']
            print(f'[ПРОГРЕСС] Обработка поста с ID {post_id}')

            if post_id in new_posts_from_wall:
                try:
                    if 'attachments' in post:
                        post = post['attachments']
                        post_type = post[0]['type']

                        if len(post) == 1:
                            if post_type == 'photo':
                                print('[ИНФОРМАЦИЯ] Найден пост с изображением!')
                                photo_url = post[0]['photo']['sizes'][-1]['url']
                                print(download_image(url=photo_url, post_id=post_id, group_name=group_name))

                            elif post_type == 'video':
                                print('[ИНФОРМАЦИЯ] Найден пост с видео!')
                                video_access_key = post[0]['video']['access_key']
                                video_post_id = post[0]['video']['id']
                                video_owner_id = post[0]['video']['owner_id']

                                video_get_url = f'https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&access_token={TOKEN}&v=5.131'
                                video_request = requests.get(video_get_url).json()

                                video_url = video_request['response']['items'][0]['player']
                                print(download_video(url=video_url, post_id=post_id, group_name=group_name, max_video_duration=max_video_duration))

                            else:
                                print('[ИНФОРМАЦИЯ] Пост с аудио, ссылкой или др')

                        else:
                            print('[ИНФОРМАЦИЯ] Найден пост с несколькими объектами!')
                            photo_in_post_count = 1

                            for item_in_post in post:
                                if item_in_post['type'] == 'photo':
                                    photo_url = item_in_post['photo']['sizes'][-1]['url']
                                    item_id_counter = str(post_id) + f'_{photo_in_post_count}'
                                    print(download_image(url=photo_url, post_id=item_id_counter, group_name=group_name))
                                    photo_in_post_count += 1

                                elif item_in_post['type'] == 'video':
                                    video_access_key = item_in_post['video']['access_key']
                                    video_post_id = item_in_post['video']['id']
                                    video_owner_id = item_in_post['video']['owner_id']

                                    video_get_url = f'https://api.vk.com/method/video.get?videos={video_owner_id}_{video_post_id}_{video_access_key}&access_token={TOKEN}&v=5.131'
                                    video_request = requests.get(video_get_url).json()

                                    video_url = video_request['response']['items'][0]['player']
                                    print(download_video(url=video_url, post_id=post_id, group_name=group_name, max_video_duration=max_video_duration))

                                else:
                                    print('[ИНФОРМАЦИЯ] Пост с аудио, ссылкой или др')

                except Exception as _ex:
                    print(_ex)

                print(f'[ПРОГРЕСС] Обработан пост {current_counter_post}/{len(new_posts_from_wall)}')
                current_counter_post += 1

    return '[ПРОГРЕСС] Работа программы завершена'


def main():
    group_name = input('Название группы VK: ')
    posts_get_count = input('Какое количество последних постов запарсить: ')
    max_video_duration = int(input('Максимальная длина видео в минутах: '))
    print(get_wall_posts(group_name=group_name, posts_get_count=posts_get_count, max_video_duration=max_video_duration))


if __name__ == '__main__':
    main()
