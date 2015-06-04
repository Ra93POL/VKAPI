# -*- coding: utf-8 -*-
# Author: Polyakov Konstantin (Ra93POL)
import urllib, urllib2, lxml.html, cookielib

def getAnswer(url_server, api_name, params={}, method="get", headers={}):
    if method == "get":
        req = urllib2.Request(url_server + api_name + "?" + urllib.urlencode(params), headers=headers)
    elif method == "post":
        req = urllib2.Request(url_server + api_name, data=params, headers=headers)
    answer = urllib2.urlopen(req)
    return answer

class VK():
    settings_api = {"lang": "ru", "v": 5.33, "https": 0, "test_mode": 0}
    # https://vk.com/dev/permissions
    acseessPermission = {
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
    }
    app_data = {}
    def __init__(self, client_id, email, password):
        self.client_id = client_id
        self.email = email
        self.password = password
        cookieJar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        urllib2.install_opener(self.opener)

    def get_scope_parametr(self):
        """ Формирование значения параметра scope - списка прав доступа"""
        scope = ""
        for key, value in self.acseessPermission.items():
            if value: scope += key + ","
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

    def do_authorize(self):
        # To open login page...
        params = {"client_id": self.client_id,
                  "redirect_uri": "https://oauth.vk.com/blank.html",
                  "scope": self.get_scope_parametr(),
                  "display": "wap",
                  "response_type": "token"
                  }
        #answer = getAnswer("https://oauth.vk.com/", "authorize", params, "get", headers)
        req = urllib2.Request("https://oauth.vk.com/authorize?" + urllib.urlencode(params))
        answer = self.opener.open(req, urllib.urlencode(params))
        page = answer.read()
        self.save(1, page, answer)
        page = lxml.html.document_fromstring(page)
        form = page.forms[0]
        params2 = {}
        for inpt in form.inputs:
             params2[inpt.name] = inpt.value
        params2["pass"] = self.password
        params2["email"] = self.email
        del params2[None]

        # Logining...
        headers = {"Cookie": answer.headers["Set-Cookie"],
                   "Referer": answer.geturl(),
                   "Connection": "keep-alive",
                   "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0"
                   }
        #answer = getAnswer(form.action, "", urllib.urlencode(params2), "post", headers)
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
        self.app_data = {}
        for kv in fragment:
            k, v = kv.split("=")
            self.app_data[k] = v

    def api(self, method_name, params):
        params = urllib.urlencode(params)
        url = "https://api.vk.com/method/%s?%s&access_token=%s&" + urllib.urlencode(self.settings_api)
        url = url % (method_name, params, self.app_data['access_token'])
        res = self.opener.open(url)
        if not self.acseessPermission['nohttps']: pass
        return res.read()

### Example

vk = VK(1112223, "your email", "password")
vk.do_authorize()

import time

parametrs2 = {
    "owner_id": vk.app_data['user_id'],
    "message": "Hello world!"
    }
print vk.api("wall.post", parametrs2)
#x = 0
#while x<1:
    #print vk.api("wall.post", parametrs)
    #time.sleep(5)
    #x += 1

parametrs = {'q': 'python'}
print vk.api('groups.search', parametrs)
