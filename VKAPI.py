# -*- coding: utf-8 -*-
# Author: Polyakov Konstantin (Ra93POL)
# Date: 01.06.2015 - 06.06.2015
import urllib, urllib2, lxml.html, cookielib, md5, json, urlparse

oauth_data = {
    'vk.com': {
        'scope_separator': ',',
        'url_toopendialog': 'https://oauth.vk.com/authorize?',
        'url_api': 'https://api.vk.com',
        'query': '/method/',
        'uri_redirect': 'https://oauth.vk.com/blank.html',
        # названия параметров, передаваемые при выполнении логининга
        'name_for_email': 'email',
        'name_for_password': 'pass',
        'other': {} # не общая информация
        },
    'ok.ru': {
        'scope_separator': ';',
        'url_toopendialog': 'http://www.odnoklassniki.ru/oauth/authorize?',
        'url_api': 'http://api.ok.ru',
        'query': '/fb.do?',
        'uri_redirect': 'http://api.ok.ru/blank.html',
        # названия параметров, передаваемые при выполнении логининга
        'name_for_email': 'fr.email',
        'name_for_password': 'fr.password',
        # названия ключей верхнего уровня в словаре-ответе на запрос api
        'other': {} # не общая информация
        },
    'disk.yandex.ru': {
        'scope_separator': None,
        'url_toopendialog': 'https://oauth.yandex.ru/authorize?',
        'url_api': 'https://webdav.yandex.ru',
        'query': None,
        'uri_redirect': 'https://oauth.yandex.ru/verification_code',
        # названия параметров, передаваемые при выполнении логининга
        'name_for_email': 'login',
        'name_for_password': 'passwd',
        'other': {} # не общая информация
        }
    }

acceessPermission = {
    'vk.com': {
        "notify": 1,
        "friends": 1,
        "photos": 1,
        "audio": 1,
        "video": 1,
        "docs": 1,
        "notes": 1,
        "pages": 1,
        "status": 1,
        "offers": 1,
        "questions": 1,
        "wall": 1,
        "groups": 1,
        "messages": 1,
        "email": 1,
        "notifications": 1,
        "stats": 1,
        "ads": 1,
        "offline": 0,
        "nohttps": 0
        },
    'ok.ru': {
        'PHOTO_CONTENT': 1,
        'SET_STATUS': 1,
        'VALUABLE_ACCESS': 0,
        'GROUP_CONTENT': 0,
        'VIDEO_CONTENT': 0,
        'APP_INVITE': 0,
        'MESSAGING': 0
        },
    'disk.yandex.ru': {} # указываются только на сайте Яндекса
}

def load_user_data():
    f = open('data/user_data.txt', 'r')
    raw_user_data = f.read()
    f.close()
    raw_user_data = raw_user_data.split('\n\n')
    user_data = {}
    for raw_user_data_site in raw_user_data:
        raw_user_data_site = raw_user_data_site.split('\n')
        site = raw_user_data_site.pop(0)
        user_data[site] = []
        for data in raw_user_data_site:
            user_data[site].append(data.split('=', 1)[1].strip())
    return user_data

class VK():
    settings_api = {"lang": "ru", "v": 5.33, "https": 0, "test_mode": 0}
    user_data = {}
    app_data = {}
    # https://vk.com/dev/permissions
    def __init__(self, user_data):
        self.user_data = user_data
        cookieJar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        urllib2.install_opener(self.opener)

    def get_scope_parametr(self, site):
        """ Формирование значения параметра scope - списка прав доступа"""
        scope = ""
        for key, value in acceessPermission[site].items():
            if value: scope += key + oauth_data[site]['scope_separator']
        if len(scope) > 1: scope = scope[:-1]
        return scope

    def save(self, name, page, answer):
        name = str(name)
        f = open('logs/%s.html' % name, 'w')
        f.write(str(page))
        f.close()

        f = open('logs/%s.txt' % name, 'w')
        f.write(answer.geturl())
        f.write('\n\n')
        f.write(str(answer.code) + ' ' + answer.msg)
        f.write('\n')
        f.write(str(answer.info()))
        f.close()

    def get_from_form(self, str_page, response):
        page = lxml.html.document_fromstring(str_page)
        if len(page.forms) == 1: form = page.forms[0]
        else: form = page.forms[1] # для Яндекса на этапе полтверждения прав:(
        # Собираем параметры
        key_value = {}
        for inpt in form.inputs:
            key_value[inpt.name] = inpt.value
        if key_value.has_key(None): del key_value[None] # У кнопки обычно нет имени.
        # Извлекаем адрес отправки формы
        action_url = form.action
        if action_url == None: action_url = response.geturl()

        parts = urlparse.urlsplit(action_url)
        # если относительный адрес...
        if parts.scheme == '' and parts.netloc == '':
            # относительно сервера
            if action_url[0] == '/':
                netloc = urlparse.urlsplit(response.geturl()).netloc
                action_url = 'https://' + netloc + action_url
            # относительно адреса текущей страницы
            else: action_url = response.geturl() +'/'+ action_url
            #print 'action url after parse: ', action_url
        return key_value, action_url

    def extract_app_data(self, response):
        fragment = urlparse.urlparse(response.geturl()).fragment
        app_data = urlparse.parse_qs(fragment)
        for k in app_data: app_data[k] = app_data[k][0]
        return app_data

    def is_there_token(self, response):
        fragment = urlparse.urlparse(response.geturl()).fragment
        app_data = urlparse.parse_qs(fragment)
        if app_data.has_key('access_token'): return True
        else: return False

    def do_authorize(self, site):
        params = {"client_id": self.user_data[site][0],
                  "redirect_uri": oauth_data[site]['uri_redirect'],
                  "scope": self.get_scope_parametr(site),
                  "response_type": "token",
                  'state': ''
                  }
        #if site == 'disk.yandex.ru':
        #    del params['redirect_uri'], params['scope']
        if site == 'vk.com': params['display'] = 'wap'
        elif site == 'ok.ru': params['layout'] = 'a'
        elif site == 'disk.yandex.ru': params['display'] = 'popup'

        print site+u': Открываем страницу для логининга...'
        req = urllib2.Request(oauth_data[site]['url_toopendialog'] + urllib.urlencode(params))
        #print 'Req. url:', req.get_full_url(), '\n'
        answer = self.opener.open(req)
        str_page = answer.read()
        self.save(1, str_page, answer)
        params2, action_url = self.get_from_form(str_page, answer)
        params2[oauth_data[site]['name_for_email']] = self.user_data[site][1]
        params2[oauth_data[site]['name_for_password']] = self.user_data[site][2]

        print site+u': Логинимся...'
        req = urllib2.Request(action_url, urllib.urlencode(params2))
        #print req.get_full_url(), '\n'
        answer = self.opener.open(req, urllib.urlencode(params2))
        # Если вместо страницы логининга была страница подтверждения прав
        # (т. е. мы уже были залогинены), то вынимаем токен.
        if not self.is_there_token(answer):
            str_page = answer.read()
            self.save(2, str_page, answer)
            params2, action_url = self.get_from_form(str_page, answer)
            params2 = urllib2.urlparse.urlparse(action_url).query +"&"+ urllib.urlencode(params2)

            print site+u': Подтверждаем права доступа...'
            req = urllib2.Request(action_url, params2)
            answer = self.opener.open(req, params2)
            self.save(3, answer.read(), answer)
        else: print site+u': Пользователь был залогинен ранее.'

        print site+u': Сохраняем токен доступа.\n'
        self.app_data[site] = self.extract_app_data(answer)

    def _process_response(self, res, site):
        res = json.loads(res.read())
        print '\nResponse from '+site+':\n  ', res
        if site == 'vk.com':
            if res.has_key('response'): return res['response']
            if res.has_key('error'):
                res = res['error']
                print 'Error: ', res['error_code'], res['error_msg']
        elif site == 'ok.ru':
            if res in [True, False]: return res
            if res.has_key('error_data'):
                print 'Error:', res['error_code'], res['error_msg']

    def api(self, site, method_name, GET={}, POST={}):
        if site == 'vk.com':
            GET['access_token'] = self.app_data[site]['access_token']
            GET = urllib.urlencode(GET)
            POST = urllib.urlencode(POST)
            url = oauth_data[site]['url_api']
            query = oauth_data[site]['query'] + method_name +'?'+ urllib.urlencode(self.settings_api) +'&'+ GET
            if POST != '': _POST = '&'+POST
            else: _POST = ''
            if acceessPermission[site]['nohttps']:
                sig = '&sig='+md5.new(query+_POST+self.app_data[site]['secret']).hexdigest()
            else: sig = ''
            res = self.opener.open(url+query+sig, POST) 
        elif site == 'ok.ru': 
            GET['application_key'] = self.user_data[site][3]
            GET['method'] = method_name
            keys = GET.keys()
            keys.sort()
            sig = ''
            for key in keys:
                sig += key +'='+ str(GET[key])
            sig = md5.new(sig+self.app_data[site]['session_secret_key']).hexdigest().lower()

            GET['access_token'] = self.app_data[site]['access_token']
            GET['sig'] = sig

            if self.app_data[site].has_key('api_server'): url = self.app_data[site]['api_server']
            else: url = oauth_data[site]['url_api']
            res = self.opener.open(url + oauth_data[site]['query'] + urllib.urlencode(GET))
        elif site == 'disk.yandex.ru': pass
        
        return self._process_response(res, site)

################## Example ##################

user_data = load_user_data()
vk = VK(user_data)

vk.do_authorize('vk.com')
vk.do_authorize('ok.ru')
vk.do_authorize('disk.yandex.ru')
print vk.app_data

#parametrs2 = {}
#vk.api('', parametrs2)

parametrs2 = {
    'owner_id': vk.app_data['vk.com']['user_id'],
    'message': 'Test (wall.post method)'
    }
parametrs3 = {
    'photo_id': 802371866404,
    'description': 'Test (photos.editPhoto method)'
    }
vk.api('vk.com', 'wall.post', parametrs2)
vk.api('ok.ru', 'photos.editPhoto', parametrs3)
