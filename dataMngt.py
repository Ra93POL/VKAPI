# -*- coding: utf-8 -*-
import pickle, os

def write(name, text, mode):
    f = open(name, mode)
    f.write(text)
    f.close()

def write_list(name, list_text, shell_text='%s', key=None):
    f = open(name, 'a')
    for text in list_text:
        if key != None: text = text[key]
        f.write(shell_text % str(text))
    f.close()

def get_number_account():
    if not os.path.exists('oauth/logs/number_account.txt'):
        number_account = {'vk.com': 0, 'ok.ru': 0, 'disk.yandex.ru': 0}
        f = open('oauth/logs/number_account.txt', 'w')
        pickle.dump(number_account, f)
    else:
        f = open('oauth/logs/number_account.txt', 'r')
        number_account = pickle.load(f)
    f.close()
    return number_account

def reload_user_data(user_data, number_account, site):
    f = open('oauth/data/passwords_'+site+'.txt', 'r')
    raw_file = f.read()
    f.close()
    raw_file = raw_file.split('\n')
    if len(raw_file) == number_account[site]:
        print 'Start the new cycle of passwords and logins...'
        number_account[site] = 0
    login, password = raw_file[number_account[site]].split(':', 1)
    user_data[site][1] = login
    user_data[site][2] = password
    number_account[site] += 1

    f = open('oauth/logs/number_account.txt', 'w')
    pickle.dump(number_account, f)
    f.close()

def load_user_data(one_account, number_account):
    f = open('oauth/data/user_data.txt', 'r')
    raw_user_data = f.read()
    f.close()
    raw_user_data = raw_user_data.split('\n\n')
    user_data = {}
    for raw_user_data_site in raw_user_data:
        raw_user_data_site = raw_user_data_site.split('\n')
        site = raw_user_data_site.pop(0)
        user_data[site] = []
        for data in raw_user_data_site:
            if data[0] == '#': continue
            user_data[site].append(data.split('=', 1)[1].strip())

    for site, value in one_account.items():
        if value == False: reload_user_data(user_data, number_account, site)

    return user_data
