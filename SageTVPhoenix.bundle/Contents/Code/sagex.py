import base64
import urllib


def SAGEX_URL():
    return "http://%s:%s/sagex" % (Prefs['server'], Prefs['port'])

# given 'object.child' it will traverse the object hierarchy for the item
def jsonval(o, expr, defval=None):
    if (o == None):
        Log('Passed Null Object for ' + expr);
        return defval

    parts = expr.split(".")
    for s in parts:
        if (s in o):
            o = o[s]
        else:
            Log("val(): Object doesn't have " + expr + "; (failed on " + s + ")")
            o = defval
            break

    return o


def GetThumb(mediafile):
    return GetFanart(mediafile, 'poster', '300')

def GetBackground(mediafile):
    return GetFanart(mediafile, 'background')

def GetFanart(mediafile, artifact, scalex=None):
    if isinstance(mediafile, dict):
        fid = mediafile['id']
    else:
        fid = mediafile

    values = {}
    values['tag'] = 'plexphoenix'
    values['mediafile'] = fid

    if not scalex == None:
        values['scalex'] = scalex

    url = SAGEX_URL() + "/media/"+artifact+"?" + urllib.urlencode(values)
    return url

def GetFanartFor(mediafile, mediatype, artifact, title=None, season=None, scalex=None):
    values = {}
    if isinstance(mediafile, dict):
        if title is None and 'title' in mediafile:
            title = mediafile['title']

        if season is None and 'season' in mediafile:
            season = mediafile['season']

        if not 'isEPG' in mediafile:
            values['mediafile'] = mediafile['id']
    else:
        if mediafile is not None:
            values['mediafile'] = mediafile

    values['tag'] = 'plexphoenix'
    values['usedefault'] = 'true'
    values['title'] = title
    values['defaulttitle'] = title
    values['artifact'] = artifact
    values['mediatype'] = mediatype

    if not scalex == None:
        values['scalex'] = scalex

    url = SAGEX_URL() + "/media/fanart?" + urllib.urlencode(values)

    Log("FANART URL: " + url)

    return url


def SageAPI(cmd, args):
    # add in command args
    values = {}
    values['c'] = cmd
    values['encoder'] = 'json'
    if not args == None:
        i = 1
        for arg in args:
            values[str(i)] = arg
            i += 1

    # Request the URL with authentication
    headers = {}
    headers["Authorization"] = "Basic " + (base64.encodestring(Prefs['username'] + ":" + Prefs['password']))

    url = SAGEX_URL() + "/api?" + urllib.urlencode(values)
    reply = JSON.ObjectFromURL(url=url, headers=headers)
    if 'Result' in reply:
        return reply['Result']
    else:
        return reply


def PhoenixAPI(cmd, args):
    # add in command args
    values = {}
    values['c'] = cmd
    if not args == None:
        i = 1
        for arg in args:
            values[str(i)] = arg
            i += 1

    # Request the URL with authentication
    headers = {}
    headers["Authorization"] = "Basic " + (base64.encodestring(Prefs['username'] + ":" + Prefs['password']))

    url = SAGEX_URL() + "/phoenix?" + urllib.urlencode(values)
    reply = JSON.ObjectFromURL(url=url, headers=headers)
    if 'reply' in reply:
        return reply['reply']
    else:
        return reply


## VFS Specific APIS
def FindSageID(json):
    if 'children' in json:
        return FindSageIDInChildren(json['children'])
    else:
        if 'id' in json:
            return json['id']
        else:
            return None

def FindSageIDInChildren(children):
    for child in children:
        sid = FindSageID(child)
        if not sid is None:
            return sid

    return None


def FindFirstChild(json):
    if isinstance(json, dict):
        if 'children' in json:
            return FindFirstChild(json['children'])
        else:
            return json
    elif isinstance(json, list):
        return FindFirstChild(json[0])
    else:
        return json


    return None


def IsAirings(json):
    try:
        return FindFirstChild(json)['isEPG']
    except:
        return False


def AppendPath(path, part):
    if path == '':
        return part
    else:
        return path + "^^" + part


def GetPath(json, path):
    Log("GetPath: " + path)
    if path == '' or path == jsonval(json, 'title'):
        return json

    for s in path.split('^^'):
        Log("PATH PART: " + s)
        if s == '':
            continue

        Log("Looking for " + s)
        for video in json['children']:
            if s == jsonval(video,'title'):
                Log("Getting: " + jsonval(video, 'title'))
                json = video
                continue

    return json


# Misc Util Sages Methods
def GetStreamUrl(media):
    return "stvphoenix://mediafile/" + media['id']


def GetAiringUrl(media):
    return "stvphoenix://airing/" + media['id']

