# -*- coding: utf-8 -*-
# Author: Polyakov Konstantin (Ra93POL)
# Date: 01.06.2015 - 05.06.2015
import urllib, urllib2, lxml.html, cookielib, md5, json

oauth_data = {
    'vk.com': {
        'scope_separator': ',',
        'url_toopendialog': 'https://oauth.vk.com/authorize?',
        'url_api': 'https://api.vk.com',
        'query': '/method/%s?%saccess_token=%s&', # method_name, parametrs, setting_app
        'uri_redirect': 'https://oauth.vk.com/blank.html'
        },
    'ok.ru': {
        'scope_separator': ';',
        'url_toopendialog': 'http://www.odnoklassniki.ru/oauth/authorize?',
        'url_api': '',
        'uri_redirect': 'http://api.ok.ru/blank.html'
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
        }
}

class VK():
    settings_api = {"lang": "ru", "v": 5.33, "https": 0, "test_mode": 0}
    user_data = {}
    app_data = {}
    # https://vk.com/dev/permissions
    app_data = {}
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
        f = open(name+".html", "w")
        f.write(str(page))
        f.close()

        f = open(name+".txt", "w")
        f.write(answer.geturl())
        f.write("\n\n")
        f.write(str(answer.code) + " " + answer.msg)
        f.write("\n")
        f.write(str(answer.info()))
        f.close()

    def do_authorize(self, site):
        # To open login page...
        params = {"client_id": self.user_data[site][0],
                  "redirect_uri": oauth_data[site]['uri_redirect'],
                  "scope": self.get_scope_parametr(site),
                  "response_type": "token",
                  'state': ''
                  }
        if site == 'vk.com':
            params['display'] = 'wap'
        elif site == 'ok.ru':
            params['layout'] = 'a'
        req = urllib2.Request(oauth_data[site]['url_toopendialog'] + urllib.urlencode(params))
        answer = self.opener.open(req, urllib.urlencode(params))
        page = answer.read()
        self.save(1, page, answer)
        page = lxml.html.document_fromstring(page)
        form = page.forms[0]
        params2 = {}
        for inpt in form.inputs:
             params2[inpt.name] = inpt.value
        params2["pass"] = self.user_data[site][2]
        params2["email"] = self.user_data[site][1]
        del params2[None]

        # Logining...
        headers = {"Cookie": answer.headers["Set-Cookie"],
                   "Referer": answer.geturl(),
                   "Connection": "keep-alive",
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0"
                   }
        req = urllib2.Request(form.action, urllib.urlencode(params2))
        answer = self.opener.open(req, urllib.urlencode(params2))
        page = answer.read()
        self.save(2, page, answer)
        page = lxml.html.document_fromstring(page)
        form = page.forms[0]
        params2 = {}
        for inpt in form.inputs:
            params2[inpt.name] = inpt.value
        del params2[None]
        params2 = urllib2.urlparse.urlparse(form.action).query +"&"+ urllib.urlencode(params2)

        # Giving access...
        headers = {#"Cookie": answer.headers["Set-Cookie"],
                   #"Referer": answer.geturl(),
                   #"Host": "login.vk.com"
                   }
        req = urllib2.Request(form.action, params2)#, headers=headers)
        answer = self.opener.open(req, params2)
        page = answer.read()
        self.save(3, page, answer)
        fragment = urllib2.urlparse.urlparse(answer.geturl()).fragment.split("&")
        self.app_data[site] = {}
        for kv in fragment:
            k, v = kv.split("=")
            self.app_data[site][k] = v

    def api(self, method_name, GET={}, POST={}, site='vk.com'):
        GET = urllib.urlencode(GET)
        POST = urllib.urlencode(POST)
        url = oauth_data[site]['url_api']
        query = oauth_data[site]['query'] + urllib.urlencode(self.settings_api)
        if GET != '': GET += '&'
        if POST != '': _POST = '&'+POST
        else: _POST = ''
        query = query % (method_name, GET, self.app_data[site]['access_token'])
        if site=='vk.com':
            if acceessPermission[site]['nohttps']:
                sig = '&sig='+md5.new(query+_POST+self.app_data[sit]['secret']).hexdigest()
            else: sig = ''
        res = self.opener.open(url+query+sig, POST)
        res =  json.loads(res.read())
        if res.has_key('response'): return res['response']
        if res.has_key('error'):
            res = res['error']
            print res['error_code'], res['error_msg']

### Example

user_data = {
    'vk.com': [1112223, "email", "password"]
    }
vk = VK(user_data)
vk.do_authorize('vk.com')

parametrs2 = {
    "owner_id": vk.app_data['vk.com']['user_id'],
    "message": "Test message (wall.post method)"
    }
print vk.api("wall.post", parametrs2)
