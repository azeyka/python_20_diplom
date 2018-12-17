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

  def Get_friends_list(self):
    params = {
      'user_id': self.id,
      'order': 'name',
      'fields': 'domain',
      'access_token': self.token,
      'v': '5.92'
    }
    response = requests.get('https://api.vk.com/method/friends.get',
                            params)

    friends_list = []
    for friend in response.json()['response']['items']:
      if not 'deactivated' in friend:
        friends_list.append(friend)

    return friends_list

  def Get_groups_list(self):
    params = {
      'user_id': self.id,
      'access_token': self.token,
      'v': '5.92'
    }
    try:
      response = requests.get('https://api.vk.com/method/users.getSubscriptions',
                              params)
      if 'error' in response.json():
        assert response.json()['error']['error_code'] != 30, \
          '\r\t- Друг пользователя {} запретил доступ к группам!'.format(self.name)

      groups_list = response.json()['response']['groups']['items']
      if len(groups_list) > 1000:
        groups_list = groups_list[: 999]

    except AssertionError as assertErr:
      groups_list = []
      print(assertErr)
    except:
      try:
        time.sleep(0.33)
        response = requests.get('https://api.vk.com/method/users.getSubscriptions',
                                params)
        groups_list = response.json()['response']['groups']['items']
      except:
        groups_list = []
        print('\rОшибка при считывании информации у пользователя {}!'.format(self.id))

    return groups_list

  def Compare_groups(self):


    def update_progress(i, friends_count, time_left, progress):
      barLength = 20
      block = int(round(barLength * progress))
      text = '\r[{}] ({}%) Выполняется запрос {} из {} (осталось ~{} мин {} сек)'\
              .format("=" * block + " " * (barLength - block), int(progress * 100),\
              i, friends_count, int(time_left//60), int(time_left % 60))
      sys.stdout.write(text)
      sys.stdout.flush()

    print('> Получаем список друзей пользователя...')
    friends_list = self.Get_friends_list()
    print('> Получаем список групп пользователя...')
    user_groups = self.Get_groups_list()
    i = 0
    one_persent = len(friends_list) / 100

    print('> Получаем список групп друзей пользователя...')
    for friend in friends_list:
      start_time = time.time()
      friend_name = friend['first_name'] + ' ' + friend['last_name']
      friend = User(self.token, friend['id'], friend_name)
      friend_groups = friend.Get_groups_list()
      user_groups = list(set(user_groups).difference(set(friend_groups)))
      end_time = time.time()

      i += 1
      time_left = (len(friends_list) - i) * (end_time - start_time)
      progress = i/one_persent/100
      update_progress(i, len(friends_list), time_left, progress)

    return user_groups

def get_unique_groups(inputed_id):


  def find_user_in_vk(inputed_id):
    print('> Ищем пользователя {} на просторах VK...'.format(inputed_id))
    params = {
      'user_ids': inputed_id,
      'access_token': token,
      'v': '5.92'
    }
    response = requests.get('https://api.vk.com/method/users.get',
                            params)
    try:

      return response.json()['response'][0]
    except:
      return 'not found'

  def print_unique_groups(groups):
    print('\nСписок групп, в которых состоит пользователь {} и не состоят его друзья:'\
          .format(inputed_id))
    i = 1
    for group in groups:
      link = 'https://vk.com/' + group['screen_name']
      print('{}) {} ({})'.format(i, group['name'], link))
      i += 1

  def write_result_to_JSON_file(groups):
    print('\n> Записываем результат в файл...')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name_JSON = 'groups.json'
    file_path = os.path.join(current_dir, file_name_JSON)
    with open(file_path, 'w', encoding='UTF-8') as file:
      for group in groups:
        file.write(json.dumps(group, sort_keys = True, indent = 4, ensure_ascii = False))
    print('Результат записан в файл по адресу {}'.format(file_path))

  token = 'ed1271af9e8883f7a7c2cefbfddfcbc61563029666c487b2f71a5227cce0d1b533c4af4c5b888633c06ae'
  response = find_user_in_vk(inputed_id)
  try:
    assert response != 'not found', ('> Данного пользователя не существует!')
    user_name = response['first_name'] + ' ' + response['last_name']
    print('> Найден пользователь по имени {}!'.format(user_name))
    user = User(token, response['id'], user_name)
    unique_groups_list = user.Compare_groups()
    print('\n> Обрабатываем результат...')
    if unique_groups_list:
      group_ids_str = ','.join([str(id) for id in unique_groups_list])
      params = {
          'group_ids': group_ids_str,
          'access_token': token,
          'v': '5.92'
      }
      response = requests.get('https://api.vk.com/method/groups.getById',
                                    params)
      print_unique_groups(response.json()['response'])
      write_result_to_JSON_file(response.json()['response'])
    else:
      print('\n\nНет ни одной группы в которой бы состоял только {}!'.format(inputed_id))
  except AssertionError as assertErr:
    print(assertErr)


if __name__ == '__main__':
  get_unique_groups('7459752')
