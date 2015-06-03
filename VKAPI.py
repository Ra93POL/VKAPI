# -*- coding: utf-8 -*-
import urllib, urllib2, lxml.html, cookielib

cookieJar = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
urllib2.install_opener(opener)

# https://vk.com/dev/permissions
acseessPermission_dict = {
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
client_id = 11223344
email = "lala@server.moc"
password = "qwerty"

settings_api = {"lang": "ru", "v": 5.33, "https": 0, "test_mode": 0}

def getScopeParametr():
    """ Формирование значения параметра scope - списка прав доступа"""
    scope = ""
    for key, value in acseessPermission_dict.items():
        if value: scope += key + ","
    if len(scope) > 1: scope = scope[:-1]
    return scope

def getAnswer(url_server, api_name, params={}, method="get", headers={}):
    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()), urllib2.HTTPRedirectHandler())
    if method == "get":
        req = urllib2.Request(url_server + api_name + "?" + urllib.urlencode(params), headers=headers)
    elif method == "post":
        req = urllib2.Request(url_server + api_name, data=params, headers=headers)
    #print req.get_full_url() + "\n"
    #print dir(req)
    answer = urllib2.urlopen(req)
    #answer = opener.open(url_server + api_name + "?" + urllib.urlencode(params))
    return answer

def save(name, page, answer):
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

def doAuthorize():
    # To open login page...
    params = {"client_id": client_id,
              "redirect_uri": "https://oauth.vk.com/blank.html",
              "scope": getScopeParametr(),
              "display": "wap",
              "response_type": "token"
              }
    #answer = getAnswer("https://oauth.vk.com/", "authorize", params, "get", headers)
    req = urllib2.Request("https://oauth.vk.com/authorize?" + urllib.urlencode(params))
    answer = opener.open(req, urllib.urlencode(params))
    page = answer.read()
    save(1, page, answer)
    page = lxml.html.document_fromstring(page)
    form = page.forms[0]
    params2 = {}
    for inpt in form.inputs:
        params2[inpt.name] = inpt.value
    params2["pass"] = password
    params2["email"] = email
    del params2[None]

    # Logining...
    headers = {"Cookie": answer.headers["Set-Cookie"],
               "Referer": answer.geturl(),
               "Connection": "keep-alive",
               "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0"
               }
    #answer = getAnswer(form.action, "", urllib.urlencode(params2), "post", headers)
    req = urllib2.Request(form.action, urllib.urlencode(params2))
    answer = opener.open(req, urllib.urlencode(params2))
    page = answer.read()
    save(2, page, answer)
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
    answer = opener.open(req, params2)
    page = answer.read()
    save(3, page, answer)
    fragment = urllib2.urlparse.urlparse(answer.geturl()).fragment.split("&")
    app_data = {}
    for kv in fragment:
        k, v = kv.split("=")
        app_data[k] = v
    return app_data

def vk_api(method_name, params, access_token):
    params = urllib.urlencode(params)
    url = "https://api.vk.com/method/%s?%s&access_token=%s&" + urllib.urlencode(settings_api)
    url = url % (method_name, params, access_token)
    res = opener.open(url)
    return res.read()

### Example

app_data = doAuthorize()
#print app_data
access_token = app_data["access_token"]
user_id = app_data["user_id"]
#secret = app_data["secret"]
expires_in = app_data["expires_in"]

import time

parametrs = {
    "owner_id": -95491425,
    "message": "Hello world!"
    }
x = 0
while x<5:
    print vk_api("wall.post", parametrs, access_token)
    time.sleep(5)
    x += 1
