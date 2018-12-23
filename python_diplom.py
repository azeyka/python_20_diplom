import requests
import time
import sys
import os
import json

class User():

  def __init__(self, token, id, name):
    self.token = token
    self.id = id
    self.name = name

  def get_friends_list(self):
    params = {
      'user_id': self.id,
      'order': 'name',
      'fields': 'domain',
    }

    response = do_api_call('friends.get', params, self.token)
    friends_list = []
    for friend in response.json()['response']['items']:
      if 'deactivated' not in friend:
        friends_list.append(friend)

    return friends_list

  def get_groups_list(self):
    params = {
      'user_id': self.id,
    }

    response = do_api_call('users.getSubscriptions', params, self.token)
    if type(response) is str:
      print(response)
      return []
    else:
      return response.json()['response']['groups']['items']

  def compare_groups(self):
    print('> Получаем список друзей пользователя...')
    friends_list = self.get_friends_list()
    print('> Получаем список групп пользователя...')
    user_groups = self.get_groups_list()
    i = 0
    one_persent = len(friends_list) / 100

    print('> Получаем список групп друзей пользователя...')
    for friend in friends_list:
      start_time = time.time()
      friend_name = friend['first_name'] + ' ' + friend['last_name']
      friend = User(self.token, friend['id'], friend_name)
      friend_groups = friend.get_groups_list()
      user_groups = set(user_groups).difference(set(friend_groups))
      end_time = time.time()

      i += 1
      time_left = (len(friends_list) - i) * (end_time - start_time)
      progress = i / one_persent / 100
      self.update_progress_bar(i, len(friends_list), time_left, progress)

    return user_groups

  def update_progress_bar(self, i, friends_count, time_left, progress):
    bar_length = 20
    block = int(round(bar_length * progress))
    bar = '=' * block + ' ' * (bar_length - block)
    text = '\r[{}] ({}%) Выполняется запрос {} из {} (осталось ~{} мин {} сек)'\
            .format(bar, int(progress * 100),  i, friends_count,\
            int(time_left//60), int(time_left % 60))
    sys.stdout.write(text)
    sys.stdout.flush()

def do_api_call(method, params, token):
  method_link = 'https://api.vk.com/method/' + method
  params['v'] = '5.92'
  params['access_token'] = token

  while True:
    response = requests.get(method_link, params)
    if 'error' in response.json():
      error_code = response.json()['error']['error_code']
      if error_code == 6 or error_code == 10:
        time.sleep(0.33)
        continue
      elif error_code == 113:
        return '> Данного пользователя не существует!'
      elif error_code == 5:
        return '> Указан не подходящий token в конфигурации!'
      elif error_code == 30:
        return '\r\t- Один из друзей пользователя запретил доступ к группам!'
      else:
        return '> Произошла неизвестная ошибка.'
    else:
      return response

def get_unique_groups():
  config_file_name = find_config()
  if config_file_name == 'no config file':
    print('> Нет файла конфигурации!')
  else:
    config_path = os.path.join(current_dir, config_file_name)
    with open(config_path, 'r') as config_JSON:
      config = json.load(config_JSON)
      if 'token' not in config and 'id' not in config:
        print('> Ошибка в файле конфигурации!')

      else:
        token = config['token']
        user_id = config['id']
        response = find_user_in_vk(user_id, token)
        if type(response) is str:
          print(response)
        else:
          parsed_response = response.json()['response'][0]
          user_name = parsed_response['first_name'] + ' ' + parsed_response['last_name']
          print('> Найден пользователь по имени {}!'.format(user_name))

          user = User(token, parsed_response['id'], user_name)

          unique_groups = user.compare_groups()
          print('\n> Обрабатываем результат...')
          if unique_groups:
            group_ids_str = ','.join([str(id) for id in unique_groups])
            params = {
                'group_ids': group_ids_str,
            }
            response = do_api_call('groups.getById', params, token)
            if type(response) is str:
              print(response)
            else:
              print_unique_groups(response.json()['response'])
              write_result_to_JSON_file(response.json()['response'])
          else:
            print('\n\nНет ни одной группы в которой бы состоял только {}!'.format(user.name))

def find_config():
  files_list = os.listdir(current_dir)
  if '.gitignore' in files_list:
    return '.gitignore'
  elif 'config.json' in files_list:
    return 'config.json'
  else:
    return 'no config file'

def find_user_in_vk(user_id, token):
  print('> Ищем пользователя {} на просторах VK...'.format(user_id))
  params = {
    'user_ids': user_id
  }
  return do_api_call('users.get', params, token)

def print_unique_groups(groups):
  print('\nСписок групп, в которых состоит пользователь и не состоят его друзья:')
  i = 1
  for group in groups:
    link = 'https://vk.com/' + group['screen_name']
    print('{}) {} ({})'.format(i, group['name'], link))
    i += 1

def write_result_to_JSON_file(groups):
  print('\n> Записываем результат в файл...')
  file_name_JSON = 'groups.json'
  file_path = os.path.join(current_dir, file_name_JSON)
  json.dump(groups, open(file_path, 'w', encoding='UTF-8'), sort_keys=True, indent=4, ensure_ascii=False)
  print('Результат записан в файл по адресу {}'.format(file_path))

if __name__ == '__main__':
  current_dir = os.path.dirname(os.path.abspath(__file__))
  get_unique_groups()
