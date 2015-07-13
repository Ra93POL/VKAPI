# -* coding: utf-8 -*-
import VKAPI, dataMngt, time

vk = None
one_account = {'vk.com': True, 'ok.ru': True, 'disk.yandex.ru': True}
number_account = dataMngt.get_number_account()

def check_app_data(one_account, res_auth, site):
    if res_auth == 'frozen':
        print 'Account of "'+vk.user_data[site][1]+'" is frozen'
        if one_account[site] == False: reauthorize(site, account='next')
    elif not vk.app_data[site].has_key('access_token'):
        print 'Access token for "'+vk.user_data[site][1]+'" wasn\'t given!'
        if one_account[site] == False: reauthorize(site, account='next')

def reauthorize(site, account='next'):
    global vk, number_account
    time.sleep(10)
    if account == 'same': number_account[site] -= 1
    dataMngt.reload_user_data(vk.user_data, number_account, site)
    res_auth = vk.do_authorize(site)
    check_app_data(one_account, res_auth, site)

def authorize(*sites):
    global vk, one_account, number_account
    user_data = dataMngt.load_user_data(one_account, number_account)
    vk = VKAPI.VK(user_data)
    for site in sites:
        res_auth = vk.do_authorize(site)
        check_app_data(one_account, res_auth, site) 
    return vk

################# ------ OK.RU ----- ################

def ok_usersSetStatus(status):
    return vk.api('ok.ru', 'users.setStatus', {'status': status})[1]

def ok_usersGetInfo(uid, fields, emptyPictures='false'):
    params = {
        'uid': uid,
        'fields': fields,
        'emptyPictures': emptyPictures}
    return vk.api('ok.ru', 'users.getInfo', params)[1]

def ok_photosEditPhoto(photo_id, description):
    params = {
    'photo_id': photo_id,
    'description': description}
    return vk.api('ok.ru', 'photos.editPhoto', params)[1]

def ok_photosGetPhotos(uid, fid='', aid=''):
    params = {
        'uid': uid,
        'fid': fid,
        'aid': aid}
    return vk.api('ok.ru', 'photos.getPhotos', params)[1]

################# ------ VK.COM ----- ################

def proccessing_error(cond, res):
    global one_account
    if cond == 'success': return res
    elif cond == 'error':
        code = res['code']
        msg = res['msg']
        oa = one_account['vk.com']
        print code, msg
        if code == 5:
            reauthorize('vk.com', 'next')
            print '\n  Connected to', vk.user_data['vk.com'][1], '\n'
            return 'reauthed'
        elif code == 15: pass
        elif code == 220: # защита от спама
            if oa == False:
                reauthorize('vk.com', 'next')
                print '\n  Connected to', vk.user_data['vk.com'][1], '\n'
                return 'reauthed'

def vk_usersGet(user_ids, fields, name_case='nom'):
    params = {
        'user_ids': user_ids,
        'fields': fields,
        'name_case': name_case}
    cond, res =  vk.api('vk.com', 'users.get', params)
    return proccessing_error(cond, res)

def vk_wallPost(owner_id, message, attachments='', from_group=0):
    params = {
        'owner_id': owner_id,
        'message': message,
        'attachments': attachments,
        'from_group': from_group}
    cond, res =  vk.api('vk.com', 'wall.post', params)
    return proccessing_error(cond, res)

def vk_newsfeedSearch(q, count, start_from='', end_time='', extended=0):
    params = {
        'q': q,
        'count': count,
        'start_from': start_from,
        'end_time': end_time,
        'extended': extended}
    cond, res =  vk.api('vk.com', 'newsfeed.search', params)
    return proccessing_error(cond, res)

def vk_groupsSearch(q, count, offset=0, city_id=''):
    parametrs = {
        'q': q, 'offset': offset, 'count': count,
        'sort': 2, 'city_id': city_id}
    cond, res = vk.api('vk.com', 'groups.search', parametrs)
    return proccessing_error(cond, res)

def vk_groupsGetById(group_id, fields=''):
    parametrs = {'group_id': group_id, 'fields': fields}
    cond, res = vk.api('vk.com', 'groups.getById', parametrs)
    return proccessing_error(cond, res)

def vk_groupsGetMembers(group_id, count, offset=0, fields=''):
    parametrs = {
        'group_id': group_id,
        'fields': fields,
        'offset': offset,
        'count': count}
    cond, res = vk.api('vk.com', 'groups.getMembers', parametrs)
    return proccessing_error(cond, res)
