VIDEO_PREFIX = "/videos/sagex/phoenix"

NAME = L('Title')

ART  = 'art-default.jpg'
ICON = 'icon.png'

####################################################################################################

def Start():
    Log("Starting Phoenix Plex Plugin")
    Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
    Plugin.AddViewGroup('PanelStream', viewMode='PanelStream', mediaType='items')

    ObjectContainer.title1 = 'Phoenix'
    ObjectContainer.view_group = 'List'

    Dict.Reset()

# see:
#  http://dev.plexapp.com/docs/Functions.html#ValidatePrefs
def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    ## do some checks and return a
    ## message container
    if( u and p ):
        return MessageContainer(
            "Success",
            "User and password provided ok"
        )
    else:
        return MessageContainer(
            "Error",
            "You need to provide both a user and password"
        )




# This main function will setup the displayed items.
@handler(VIDEO_PREFIX,'Phoenix', art=ART, thumb=ICON)
def MainMenu():
    dir=ObjectContainer()
    dir.add(DirectoryObject(key=Callback(GetView, viewName='phoenix.view.util.instantstatus.recentrecordings', title="Recent Recordings"), title='Recent Recordings'))
    dir.add(DirectoryObject(key=Callback(GetView, viewName='phoenix.view.default.TV.unwatched', title="Unwatched TV"), title='Unwatched TV'))
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to the SageTV backend", thumb=R("icon-prefs.png")))
    return dir

def LoadMenuFromServer(menuname):
    #http://192.168.1.10:8080/sagex/api?c=GetFileAsString&1=userdata/Phoenix/Menus/plexmenu.json&encoder=json
    return None

@route(VIDEO_PREFIX + '/vfs/getview', allow_sync=True)
def GetView(viewName, title):
#    dir.content = ContainerContent.Episodes

    # http://192.168.1.10:8080/sagex/phoenix?c=phoenix.umb.CreateView&1=phoenix.view.default.TV.unwatched
    json_url = 'http://'+Prefs['server']+':'+Prefs['port']+'/sagex/phoenix?c=phoenix.umb.CreateView&1=' + viewName

    # This is the API used to parse data from JSON
    videos = JSON.ObjectFromURL(json_url)

    Dict[viewName] = videos['reply']

    Log('Processing Videos')

    dir = ProcessChildren(title, viewName, Dict[viewName]['title'])

    if len(dir) < 1:
        Log ('still no value for objects: ' + json_url)
        return ObjectContainer(header='No Data for View', message='Unable to load the view')


    return dir

@route(VIDEO_PREFIX + '/vfs/getview/children', allow_sync=True)
def ProcessChildren(title, viewName, path):
    Log('Processing View: ' + viewName + " with path " + path)
    #note need to use a callback and a key on the Directory object... it does not like nesting
    json = GetPath(Dict[viewName], path)

    if (json == None):
        Log('Nothing for ' + path + " in ")
        Log(Dict[viewName])

    dir = ObjectContainer(title2=title, view_group='InfoList')

    if 'children' in json:
        for video in json['children']:
            if 'children' in video:
                Log('Adding Children')
                sageid = FindSageID(video)
                # Log(video)
                dir.add(
                    DirectoryObject(key=Callback(ProcessChildren, title=title, viewName=viewName, path=AppendPath(path, video['title'])),
                    title=video['title'],
                    thumb=GetPosterUrlForId(sageid),
                    art=GetBackgroundUrlForId(sageid))
                )
            else:
                Log('Adding Child: ' + V(video, 'title'))
                dir.add(PhoenixMediaObject(video))

    dir.art=GetBackgroundUrlForId(FindSageID(json))
    return dir

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
        if not sid == None:
            return sid

    return None

def AppendPath(path, part):
    if path == '':
        return part
    else:
        return path + "^^" + part

def GetPath(json, path):
    Log("GetPath: " + path)
    if path == '' or path == V(json, 'title'):
        return json

    for s in path.split('^^'):
        Log("PATH PART: " + s)
        if s == '':
            continue

        Log("Looking for " + s)
        for video in json['children']:
            if s == V(video,'title'):
                Log("Getting: " + V(video, 'title'))
                json = video
                continue

    return json


def PhoenixMediaObject(media):
    if 'isTV' in media:
        isTV = media['isTV']
    else:
        isTV = False

    if isTV:
        o = EpisodeObject()
        o.title = media['episodeName']
        o.show = media['title']
        o.season = media['season']
        o.index = media['episode']
        o.summary = V(media,'description')
    else:
        o = VideoClipObject()
        o.title = V(media, 'title')
#        o.description = V(media,'description')

    if o.title == None:
        Log(media)

    o.url = GetStreamUrl(media)
    o.thumb = GetPosterUrl(media)
    return o

def GetPosterUrl(media):
    return GetPosterUrlForId(media['id'])

def GetPosterUrlForId(mediaid):
    return 'http://'+Prefs['server']+':'+Prefs['port']+'/sagex/media/poster?scalex=300&tag=plexphoenix&mediafile=' + mediaid

def GetBackgroundUrlForId(mediaid):
    return 'http://'+Prefs['server']+':'+Prefs['port']+'/sagex/media/background?tag=plexphoenix&mediafile=' + mediaid


def GetStreamUrl(media):
    return "stvphoenix://mediafile/" + media['id']

def V(o,k):
    if k in o:
        return o[k]
    else:
        return None

# {
#     "reply": {
#         "title": "TV Shows (Unwatched)",
#         "id": "TV Shows (Unwatched)",
#         "path": "/TV Shows (Unwatched)",
#         "view": "phoenix.view.default.TV.unwatched",
#         "level": 0,
#         "children.size": 16,
#         "children": [
#             {
#                 "title": "Hawaii Five-0",
#                 "id": "Hawaii Five-0",
#                 "path": "/TV Shows (Unwatched)/Hawaii Five-0",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Hawaii Five-0",
#                         "id": "10814720",
#                         "path": "/TV Shows (Unwatched)/Hawaii Five-0/Hawaii Five-0",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 13,
#                         "episodeName": "Hana Lokomaika'i",
#                         "airingTime": 1390010400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10734631,
#                         "description": "Chin is questioned about his father's murder and how his relationship with Malia and her family could have adversely affected the investigation.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Bones",
#                 "id": "Bones",
#                 "path": "/TV Shows (Unwatched)/Bones",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Bones",
#                         "id": "10814719",
#                         "path": "/TV Shows (Unwatched)/Bones/Bones",
#                         "isTV": true,
#                         "season": 9,
#                         "episode": 13,
#                         "episodeName": "Big in the Philippines",
#                         "airingTime": 1390006800000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10734450,
#                         "description": "The team investigates the death of a country music singer whose remains were found in a shallow grave; Brennan takes a look at Wendall's injuries after he breaks his arm during a hockey game.",
#                         "isVIDEO": true,
#                         "runtime": 2700000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3394976"
#                     }
#                 ]
#             },
#             {
#                 "title": "White Collar",
#                 "id": "White Collar",
#                 "path": "/TV Shows (Unwatched)/White Collar",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "White Collar",
#                         "id": "10808039",
#                         "path": "/TV Shows (Unwatched)/White Collar/White Collar",
#                         "isTV": true,
#                         "season": 5,
#                         "episode": 11,
#                         "episodeName": "Shot Through the Heart",
#                         "airingTime": 1389947311200,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "When Neal and Peter go after an assassin, the stakes are raised even higher when they realize this may be the same person who has been pulling Neal?s strings.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3238754"
#                     }
#                 ]
#             },
#             {
#                 "title": "Psych",
#                 "id": "Psych",
#                 "path": "/TV Shows (Unwatched)/Psych",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Psych",
#                         "id": "10800773",
#                         "path": "/TV Shows (Unwatched)/Psych/Psych",
#                         "isTV": true,
#                         "season": 8,
#                         "episode": 2,
#                         "episodeName": "SEIZE the Day",
#                         "airingTime": 1389875803610,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Modern Family",
#                 "id": "Modern Family",
#                 "path": "/TV Shows (Unwatched)/Modern Family",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Modern Family",
#                         "id": "10800772",
#                         "path": "/TV Shows (Unwatched)/Modern Family/Modern Family",
#                         "isTV": true,
#                         "season": 5,
#                         "episode": 12,
#                         "episodeName": "Under Pressure",
#                         "airingTime": 1389837600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10723350,
#                         "description": "Gloria has an encounter with a mean mom (Jane Krakowski) during the high school open house; Mitchell meets a judgmental neighbor (Jesse Eisenberg); Alex goes to a therapist.",
#                         "isVIDEO": true,
#                         "runtime": 1800000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3328416"
#                     }
#                 ]
#             },
#             {
#                 "title": "Revolution",
#                 "id": "Revolution",
#                 "path": "/TV Shows (Unwatched)/Revolution",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 10,
#                 "children": [
#                     {
#                         "title": "Revolution",
#                         "id": "10800731",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 11,
#                         "episodeName": "Mis Dos Padres",
#                         "airingTime": 1389834000000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10723361,
#                         "description": "Monroe must make a decision about his son; Gene leads Charlie to a discovery.",
#                         "isVIDEO": true,
#                         "runtime": 2700000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10751821",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 10,
#                         "episodeName": "Three Amigos",
#                         "airingTime": 1389229200000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10676538,
#                         "description": "Miles takes Rachel and Monroe south of the border, where they are met with more than they bargained for; Gene and Charlie keep searching for Aaron.",
#                         "isVIDEO": true,
#                         "runtime": 2700000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10420520",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 9,
#                         "episodeName": "Everyone Says I Love You",
#                         "airingTime": 1384995600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10341116,
#                         "description": "Charlie demonstrates to Rachel how much she has matured; Neville issues Jason a proclamation.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10365821",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 8,
#                         "episodeName": "Come Blow Your Horn",
#                         "airingTime": 1384390800000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10294763,
#                         "description": "Miles and the gang work to escape their situation; Rachel and Gene's difficult relationship affects Charlie; Neville makes a move.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3228418"
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10326789",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 7,
#                         "episodeName": "The Patriot Act",
#                         "airingTime": 1383782400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10251604,
#                         "description": "Rachel is faced with unsettling truths; Miles tries to overcome obstacles; Charlie and her mother share a moment.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3195612"
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10279548",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 6,
#                         "episodeName": "Dead Man Walking",
#                         "airingTime": 1383177600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10273324,
#                         "description": "Monroe's true allegiance is questioned as Miles considers the consequences of his former friend's actions; Aaron's visions continue to lead to questions.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3172464"
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10230724",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 5,
#                         "episodeName": "One Riot, One Ranger",
#                         "airingTime": 1382583600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10156272,
#                         "description": "Aaron and Rachel consider the effects of nanotechnology; a man from Miles' past reappears and offers an opportunity to take the Patriots down.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10184503",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 4,
#                         "episodeName": "Patriot Games",
#                         "airingTime": 1381968000000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10104752,
#                         "description": "Monroe and Charlie's relationship changes; Rachel's curiosity and increased awareness threatens to be her undoing; Neville manipulates patriot power brokers.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10137333",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 3,
#                         "episodeName": "Love Story",
#                         "airingTime": 1381363200000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10061694,
#                         "description": "Rachel tries to rescue Miles and to escape with a sick tribesman's wife; violent refugees assault Neville and Jason; Charlie and Adam can't agree on what to do with Monroe; tribesmen threaten Willoughby.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Revolution",
#                         "id": "10089866",
#                         "path": "/TV Shows (Unwatched)/Revolution/Revolution",
#                         "isTV": true,
#                         "season": 2,
#                         "episode": 2,
#                         "episodeName": "There Will Be Blood",
#                         "airingTime": 1380758400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10008618,
#                         "description": "Miles finds himself in danger when he ends up in the clutches of Titus Andover; Charlie searches for Monroe; Rachel and Dr. Porter desperately try to revive Aaron; Neville devises a plan.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Marvel's Agents of S.H.I.E.L.D.",
#                 "id": "Marvel's Agents of S.H.I.E.L.D.",
#                 "path": "/TV Shows (Unwatched)/Marvel's Agents of S.H.I.E.L.D.",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Marvel's Agents of S.H.I.E.L.D.",
#                         "id": "10794068",
#                         "path": "/TV Shows (Unwatched)/Marvel's Agents of S.H.I.E.L.D./Marvel's Agents of S.H.I.E.L.D.",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 12,
#                         "episodeName": "Seeds",
#                         "airingTime": 1389758400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10798324,
#                         "description": "May and Coulson uncover shocking information about Skye; a team encounters a crisis at the S.H.I.E.L.D. academy.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "New Girl",
#                 "id": "New Girl",
#                 "path": "/TV Shows (Unwatched)/New Girl",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 2,
#                 "children": [
#                     {
#                         "title": "New Girl",
#                         "id": "10794066",
#                         "path": "/TV Shows (Unwatched)/New Girl/New Girl",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 12,
#                         "episodeName": "Basketball",
#                         "airingTime": 1389751200000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10716576,
#                         "description": "Jess makes an effort to cement her friendship with Coach; Schmidt must mentor an older employee; Winston finds a new career path.",
#                         "isVIDEO": true,
#                         "runtime": 1800000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "New Girl",
#                         "id": "10745256",
#                         "path": "/TV Shows (Unwatched)/New Girl/New Girl",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 11,
#                         "episodeName": "Clavado En Un Bar",
#                         "airingTime": 1389146400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10670202,
#                         "description": "When Jess has to make a quick decision about her career, her friends all recall how they ended up at their jobs.",
#                         "isVIDEO": true,
#                         "runtime": 1800000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Brooklyn Nine-Nine",
#                 "id": "Brooklyn Nine-Nine",
#                 "path": "/TV Shows (Unwatched)/Brooklyn Nine-Nine",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 2,
#                 "children": [
#                     {
#                         "title": "Brooklyn Nine-Nine",
#                         "id": "10794064",
#                         "path": "/TV Shows (Unwatched)/Brooklyn Nine-Nine/Brooklyn Nine-Nine",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 13,
#                         "episodeName": "The Bet",
#                         "airingTime": 1389749400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10716578,
#                         "description": "Jake and Amy settle their ongoing bet about who can make more arrests; Charles reveals what he really thinks about his colleagues while under the influence of pain medication.",
#                         "isVIDEO": true,
#                         "runtime": 1800000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "Brooklyn Nine-Nine",
#                         "id": "10745235",
#                         "path": "/TV Shows (Unwatched)/Brooklyn Nine-Nine/Brooklyn Nine-Nine",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 12,
#                         "episodeName": "Pontiac Bandit",
#                         "airingTime": 1389144600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10670204,
#                         "description": "One of Rosa's perps has information on a car thief Jake has been after for years; the station struggles to accommodate Charles' needs; Holt tries to find two puppies a home.",
#                         "isVIDEO": true,
#                         "runtime": 1800000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Person of Interest",
#                 "id": "Person of Interest",
#                 "path": "/TV Shows (Unwatched)/Person of Interest",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Person of Interest",
#                         "id": "10794062",
#                         "path": "/TV Shows (Unwatched)/Person of Interest/Person of Interest",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 13,
#                         "episodeName": "4C",
#                         "airingTime": 1389744000000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10716404,
#                         "description": "Reese gets on an international flight -- intending to leave the team and the past behind -- but realizes his travel plans were manipulated.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3364202"
#                     }
#                 ]
#             },
#             {
#                 "title": "The Blacklist",
#                 "id": "The Blacklist",
#                 "path": "/TV Shows (Unwatched)/The Blacklist",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 6,
#                 "children": [
#                     {
#                         "title": "The Blacklist",
#                         "id": "10782565",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 11,
#                         "episodeName": "The Good Samaritan Killer",
#                         "airingTime": 1389668400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10707330,
#                         "description": "Internal affairs tries to find the mole on the team; Red takes off on a mission to find who betrayed him; a serial killer from Liz's past strikes again.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3276454"
#                     },
#                     {
#                         "title": "The Blacklist",
#                         "id": "10497632",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 10,
#                         "episodeName": "Anslo Garrick - Part 2",
#                         "airingTime": 1386039660000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10423064,
#                         "description": "Liz manages to disarm the signal jammers and call in backup, but hits a snag along the way; Ressler's fate hangs in the balance; Tom worries about Liz's situation.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3276452"
#                     },
#                     {
#                         "title": "The Blacklist",
#                         "id": "10450960",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 9,
#                         "episodeName": "Anslo Garrick",
#                         "airingTime": 1385434860000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10366642,
#                         "description": "Anslo Garrick (Ritchie Coster), the newest person on the blacklist, tries to capture Red; Liz is caught in an elevator.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3276450"
#                     },
#                     {
#                         "title": "The Blacklist",
#                         "id": "10354261",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 8,
#                         "episodeName": "General Ludd",
#                         "airingTime": 1384225260000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10280077,
#                         "description": "When Red reveals a new name, Liz learns of a plot to destroy the country's financial system; Tom helps Liz when a loved one falls ill.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "The Blacklist",
#                         "id": "10308823",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 7,
#                         "episodeName": "Frederick Barnes",
#                         "airingTime": 1383620460000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10233049,
#                         "description": "The FBI searches for the man responsible for a chemical attack on a subway; Liz wants to avoid Red after he implicated Tom.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3277226"
#                     },
#                     {
#                         "title": "The Blacklist",
#                         "id": "10261479",
#                         "path": "/TV Shows (Unwatched)/The Blacklist/The Blacklist",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 6,
#                         "episodeName": "Gina Zanetakos",
#                         "airingTime": 1383012000000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10247764,
#                         "description": "Tom claims he is innocent and wants to turn the box into the FBI; Red's next target is a beautiful and deadly corporate terrorist (Margarita Levieva).",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Sleepy Hollow",
#                 "id": "Sleepy Hollow",
#                 "path": "/TV Shows (Unwatched)/Sleepy Hollow",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Sleepy Hollow",
#                         "id": "10782562",
#                         "path": "/TV Shows (Unwatched)/Sleepy Hollow/Sleepy Hollow",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 11,
#                         "episodeName": "The Vessel",
#                         "airingTime": 1389664800000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10707332,
#                         "description": "Capt. Irving turns to Crane and Mills for help when evil forces target his daughter; a frightening chapter of Jenny's past is exposed.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3387360"
#                     }
#                 ]
#             },
#             {
#                 "title": "Almost Human",
#                 "id": "Almost Human",
#                 "path": "/TV Shows (Unwatched)/Almost Human",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "Almost Human",
#                         "id": "10782559",
#                         "path": "/TV Shows (Unwatched)/Almost Human/Almost Human",
#                         "isTV": true,
#                         "season": 1,
#                         "episode": 8,
#                         "episodeName": "You Are Here",
#                         "airingTime": 1389661200000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10707331,
#                         "description": "Kennex and Dorian investigate a crime involving a self-guided bullet; Maldonado revisits the ambush that nearly killed Kennex.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "The Following",
#                 "id": "The Following",
#                 "path": "/TV Shows (Unwatched)/The Following",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 1,
#                 "children": [
#                     {
#                         "title": "The Following",
#                         "id": "10726102",
#                         "path": "/TV Shows (Unwatched)/The Following/The Following",
#                         "isTV": true,
#                         "season": 0,
#                         "episode": 0,
#                         "episodeName": "The Following Revisited",
#                         "airingTime": 1388889000000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10652453,
#                         "description": "Recap of season one; interviews with creator Kevin Williamson and actors Kevin Bacon and Shawn Ashmore.",
#                         "isVIDEO": true,
#                         "runtime": 0,
#                         "year": 0,
#                         "mediatype": "",
#                         "imdbid": ""
#                     }
#                 ]
#             },
#             {
#                 "title": "Once Upon a Time",
#                 "id": "Once Upon a Time",
#                 "path": "/TV Shows (Unwatched)/Once Upon a Time",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 3,
#                 "children": [
#                     {
#                         "title": "Once Upon a Time",
#                         "id": "10591022",
#                         "path": "/TV Shows (Unwatched)/Once Upon a Time/Once Upon a Time",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 11,
#                         "episodeName": "Going Home",
#                         "airingTime": 1387148400000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10504892,
#                         "description": "",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3282766"
#                     },
#                     {
#                         "title": "Once Upon a Time",
#                         "id": "10543947",
#                         "path": "/TV Shows (Unwatched)/Once Upon a Time/Once Upon a Time",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 10,
#                         "episodeName": "The New Neverland",
#                         "airingTime": 1386543600000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10458475,
#                         "description": "The residents of Storybrooke are overjoyed upon the return of Henry and our heroes from Neverland. But unbeknownst to them, a plan is secretly being put into place by a well-hidden Pan that will shake up the very lives of the townspeople. Meanwhile, in the Fairy Tale Land that was, Snow White and Prince Charming?s honeymoon turns out to be anything but romantic when they go in search of a mythical being that could stop Regina cold in her tracks.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3282768"
#                     },
#                     {
#                         "title": "Once Upon a Time",
#                         "id": "10497442",
#                         "path": "/TV Shows (Unwatched)/Once Upon a Time/Once Upon a Time",
#                         "isTV": true,
#                         "season": 3,
#                         "episode": 9,
#                         "episodeName": "Save Henry",
#                         "airingTime": 1385938800000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "isRecording": true,
#                         "airingid": 10409321,
#                         "description": "The race to stop Pan is on as Henry's life hangs in the balance; with Mr. Gold's help, Regina decides to adopt a baby.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt3280694"
#                     }
#                 ]
#             },
#             {
#                 "title": "The Walking Dead",
#                 "id": "The Walking Dead",
#                 "path": "/TV Shows (Unwatched)/The Walking Dead",
#                 "view": "phoenix.view.default.TV.unwatched",
#                 "level": 1,
#                 "children.size": 8,
#                 "children": [
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10497618",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 8,
#                         "episodeName": "Too Far Gone",
#                         "airingTime": 1385973217370,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "After things begin to calm down at the prison, Rick and his group now face imminent danger and destruction. This time, they might not win.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2948638"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10497458",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 7,
#                         "episodeName": "Dead Weight",
#                         "airingTime": 1385393439410,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "Something new unfolds at a camp outside the prison. The addition of new members may threaten peace.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2948634"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10497454",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 6,
#                         "episodeName": "Live Bait",
#                         "airingTime": 1384785365130,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "Group members struggle to find their humanity while being constantly threatened.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2948630"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10354039",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 5,
#                         "episodeName": "Internment",
#                         "airingTime": 1384158312650,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "Assorted enemies pressure Rick and the group; the survivors and the prison may reach a breaking point.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2948636"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10308771",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 4,
#                         "episodeName": "Indifference",
#                         "airingTime": 1383557336410,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "The supply mission faces hurdles; the situation at the prison worsens.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2948628"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10261219",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 3,
#                         "episodeName": "Isolation",
#                         "airingTime": 1382941611000,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "A group leaves the prison to search for supplies; the remaining members of the group deal with recent losses.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": ""
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10211989",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 2,
#                         "episodeName": "Infected",
#                         "airingTime": 1382363224130,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "As the group faces a brand new enemy, Rick and the others must fight to protect the livelihood they worked so hard to create at the prison.",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2931446"
#                     },
#                     {
#                         "title": "The Walking Dead",
#                         "id": "10167392",
#                         "path": "/TV Shows (Unwatched)/The Walking Dead/The Walking Dead",
#                         "isTV": true,
#                         "season": 4,
#                         "episode": 1,
#                         "episodeName": "30 Days Without an Accident",
#                         "airingTime": 1381719975940,
#                         "isDontLike": false,
#                         "watched": false,
#                         "description": "Rick and the group are as close to an ideal life as possible at the prison. Will they be able to hold on to humanity in the face of a new evil?",
#                         "isVIDEO": true,
#                         "runtime": 3600000,
#                         "year": 0,
#                         "mediatype": "TV",
#                         "imdbid": "tt2795750"
#                     }
#                 ]
#             }
#         ]
#     }
# }

