# -*- coding: utf-8 -*-
# Author: Polyakov Konstantin (Ra93POL)
# Date: 01.06.2015 - 06.06.2015
import urllib, urllib2, lxml.html, cookielib, md5, json, urlparse
import dataMngt

oauth_data = {
    'vk.com': {
        'scope_separator': ',',
        'url_toopendialog': 'https://oauth.vk.com/authorize',
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
        'url_toopendialog': 'http://www.odnoklassniki.ru/oauth/authorize',
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
        'url_toopendialog': 'https://oauth.yandex.ru/authorize',
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
        'VALUABLE_ACCESS': 1,
        'GROUP_CONTENT': 1,
        'VIDEO_CONTENT': 1,
        'APP_INVITE': 1,
        'MESSAGING': 1
        },
    'disk.yandex.ru': {} # указываются только на сайте Яндекса
}        

def save_log(name, page, answer):
    name = str(name)
    f = open('oauth/logs/%s.html' % name, 'w')
    f.write(str(page))
    f.close()

    f = open('oauth/logs/%s.txt' % name, 'w')
    f.write(answer.geturl())
    f.write('\n\n')
    f.write(str(answer.code) + ' ' + answer.msg)
    f.write('\n')
    f.write(str(answer.info()))
    f.close()

def open_url(url, name, opener, POST=None, GET=None):
    if 'dict' in str(type(POST)): POST = urllib.urlencode(POST)
    if 'dict' in str(type(GET)): GET = urllib.urlencode(GET)

    if GET == None and POST == None: res = opener.open(url)
    elif GET != None and POST != None: res = opener.open(url +'?'+ GET, POST)
    elif GET == None: res = opener.open(url, POST)
    elif POST == None: res = opener.open(url +'?'+ GET)
    str_page = res.read()
    save_log(name, str_page, res)
    return str_page, res

def get_from_form(str_page, response, opener=None):
    page = lxml.html.document_fromstring(str_page)
    if len(page.forms) == 1: form = page.forms[0]
    else: form = page.forms[1] # для Яндекса на этапе полтверждения прав:(
    # Собираем параметры
    key_value = {}
    for inpt in form.inputs:
        value = inpt.value
        name = inpt.name
        if None not in [name, value]: key_value[name] = value.encode('utf-8')
    #if key_value.has_key(None): del key_value[None] # У кнопки обычно нет имени.
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

    # проверяем наличие капчи (for vk.com only)
    if key_value.has_key('captcha_key'):
        img = form.cssselect('img.captcha_img')[0]
        captcha_url = img.attrib['src']
        captcha_img = opener.open(captcha_url).read()
        dataMngt.write('oauth/logs/captcha.jpg', captcha_img, 'wb')
        captcha_key = raw_input('Input the captcha number:')
        key_value['captcha_key'] = captcha_key
    return key_value, action_url

class VK():
    settings_api = {"lang": "ru", "v": 5.33, "https": 0, "test_mode": 0}
    user_data = {}
    app_data = {}
    openers = {}
    print_log = True
    def __init__(self, user_data):
        self.user_data = user_data

    def _get_scope_parametr(self, site):
        """ Формирование значения параметра scope - списка прав доступа"""
        scope = ""
        for key, value in acceessPermission[site].items():
            if value: scope += key + oauth_data[site]['scope_separator']
        if len(scope) > 1: scope = scope[:-1]
        return scope

    def _extract_app_data(self, response):
        fragment = urlparse.urlparse(response.geturl()).fragment
        app_data = urlparse.parse_qs(fragment)
        for k in app_data: app_data[k] = app_data[k][0]
        return app_data

    def _is_there_token(self, response):
        fragment = urlparse.urlparse(response.geturl()).fragment
        app_data = urlparse.parse_qs(fragment)
        if app_data.has_key('access_token'): return True
        else: return False

    def _is_frozen(self, str_page):
        str_page = str_page.replace('text_panel login_blocked_panel', 'text_panel_login_blocked_panel')
        page = lxml.html.document_fromstring(str_page)
        div = page.cssselect('div.text_panel_login_blocked_panel')
        if len(div) == 1:
            print div[0].text
            return True
        else: return False

    def do_authorize(self, site):
        cookieJar = cookielib.CookieJar()
        self.openers[site] = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        #urllib2.install_opener(self.openers[site])

        params = {"client_id": self.user_data[site][0],
                  "redirect_uri": oauth_data[site]['uri_redirect'],
                  "scope": self._get_scope_parametr(site),
                  "response_type": "token",
                  'state': ''
                  }
        #if site == 'disk.yandex.ru':
        #    del params['redirect_uri'], params['scope']
        if site == 'vk.com': params['display'] = 'wap'
        elif site == 'ok.ru': params['layout'] = 'a'
        elif site == 'disk.yandex.ru': params['display'] = 'popup'

        print site+u': Открываем страницу для логининга...'
        str_page, res = open_url(oauth_data[site]['url_toopendialog'], 1, self.openers[site], GET=params)
        params2, action_url = get_from_form(str_page, res)
        params2[oauth_data[site]['name_for_email']] = self.user_data[site][1]
        params2[oauth_data[site]['name_for_password']] = self.user_data[site][2]

        print site+u': Логинимся...'
        str_page, res = open_url(action_url, 2, self.openers[site], POST=params2)
        # Если вместо страницы логининга была страница подтверждения прав
        # (т. е. мы уже были залогинены), то вынимаем токен.
        if not self._is_there_token(res):
            if self._is_frozen(str_page): return 'frozen'
            params2, action_url = get_from_form(str_page, res, self.openers[site])
            # если мы вводили капчу
            if params.has_key(oauth_data[site]['name_for_password']):
                params2[oauth_data[site]['name_for_email']] = self.user_data[site][1]
                params2[oauth_data[site]['name_for_password']] = self.user_data[site][2]
            params2 = urlparse.urlparse(action_url).query +"&"+ urllib.urlencode(params2)

            print site+u': Подтверждаем права доступа...'
            str_page, res = open_url(action_url, 3, self.openers[site], POST=params2)
        else: print site+u': Пользователь был залогинен ранее.'

        print site+u': Сохраняем токен доступа.\n'
        self.app_data[site] = self._extract_app_data(res)

    def _process_response(self, res, site):
        res = json.loads(res.read())
        if self.print_log: print '\nResponse from '+site+':\n  ', res
        if site == 'vk.com':
            if res.has_key('response'): return 'success', res['response']
            elif res.has_key('error'):
                res = res['error']
                return 'error', {'code': res['error_code'], 'msg': res['error_msg']}
        elif site == 'ok.ru':
            if res in [True, False]: return 'success', res
            elif res.has_key('error_data'):
                return 'error', {'code': res['error_code'], 'msg': res['error_msg']}

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
            res = self.openers[site].open(url+query+sig, POST) 
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
            res = self.openers[site].open(url + oauth_data[site]['query'] + urllib.urlencode(GET))
        elif site == 'disk.yandex.ru': pass
        
        return self._process_response(res, site)
