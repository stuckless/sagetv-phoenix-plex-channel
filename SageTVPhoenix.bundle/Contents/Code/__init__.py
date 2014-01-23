import sagex as sagex

VIDEO_PREFIX = "/video/sagex/phoenix"

NAME = L('Title')

ART  = 'art-default.jpg'
ICON = 'icon.png'

DEFAULT_MENU = [
    {
        'title':'Unwatched TV',
        'view':'phoenix.view.default.TV.unwatched'
    },
    {
        'title':'Recording Schedule (Grouped by Date)',
        'view':'phoenix.view.default.scheduledrecordings'
    },
    {
        'title':'Recording Schedule',
        'view':'phoenix.view.primary.scheduledrecordings'
    },
    {
        'title':'Currently Recording',
        'view':'phoenix.view.default.currentlyrecording'
    }
]



####################################################################################################

FOLDERS_COUNT_IN_TITLE = True

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
    server = Prefs['server']
    port = Prefs['port']

    ## do some checks and return a
    ## message container
    if u and p and server and port:
        return MessageContainer(
            "Success",
            "User and password provided ok"
        )
    else:
        return MessageContainer(
            "Error",
            "You need to provide a user, password, server, and port"
        )




# This main function will setup the displayed items.
@handler(VIDEO_PREFIX,'Phoenix', art=ART, thumb=ICON)
def MainMenu():
    dir=ObjectContainer()

    try:
        menus = LoadMenuFromServer()
        for menu in menus:
            dir.add(DirectoryObject(key=Callback(GetView, viewName=sagex.jsonval(menu, 'view'), title=sagex.jsonval(menu, 'title')), title=sagex.jsonval(menu, 'title')))
    except:
        Log('Possible server communication problems')

    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to the SageTV backend", thumb=R("icon-prefs.png")))
    return dir


def LoadMenuFromServer(menuname='userdata/Phoenix/Menus/plexmenu.json'):
    menusStr = sagex.SageAPI('GetFileAsString', [menuname])
    if menusStr is None or menusStr == '':
        return DEFAULT_MENU
    else:
        try:
            return JSON.ObjectFromString(menusStr)
        except:
            Log('Invalid Menu ' + menusStr + " from " + menuname)
            return DEFAULT_MENU


    return None

@route(VIDEO_PREFIX + '/vfs/getview', allow_sync=True)
def GetView(viewName, title):
    videos = sagex.PhoenixAPI('phoenix.umb.CreateView', [viewName])

    if videos is None:
        return ObjectContainer(header='No Files', message='No files for the given view ' + title)

    if 'title' not in videos:
        Log(videos)
        return ObjectContainer(header='No Files', message='No files for the given view ' + title)

    Dict[viewName] = videos

    Log('Processing Videos: viewName=' + viewName + "; title=" + title)



    dir = ProcessChildren(title, viewName, Dict[viewName]['title'])

    if dir is None or len(dir) < 1:
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + viewName)

    return dir


@route(VIDEO_PREFIX + '/vfs/getview/children', allow_sync=True)
def ProcessChildren(title, viewName, path):
    Log('Processing View: ' + viewName + " with path " + path)

    json = sagex.GetPath(Dict[viewName], path)

    if (json == None):
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + title)

    if sagex.IsAirings(json):
        return ProcessAirings(title, viewName, path, json)
    else:
        return ProcessMediaItems(title, viewName, path, json)


def ProcessMediaItems(title, viewName, path, json):
    dir = ObjectContainer(title2=title, view_group='InfoList')

    if 'children' in json:
        for video in json['children']:
            if 'children' in video:
                sageid = sagex.FindSageID(video)
                if FOLDERS_COUNT_IN_TITLE:
                    folderTitle = video['title'] + " (" + str(len(video['children'])) + " Items)"
                else:
                    folderTitle = video['title']
                dir.add(
                    DirectoryObject(key=Callback(ProcessChildren, title=title, viewName=viewName, path=sagex.AppendPath(path, video['title'])),
                                    title=folderTitle,
                                    thumb=sagex.GetThumb(sageid),
                                    art=sagex.GetBackground(sageid))
                )
            else:
                dir.add(NewPhoenixMediaObject(video))

    dir.art=sagex.GetBackground(sagex.FindSageID(json))

    if len(dir)<1:
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + title)

    return dir


def ProcessAirings(title, viewName, path, json):
    dir = ObjectContainer(title2=title, view_group='InfoList')

    if 'children' in json:
        for video in json['children']:
            if 'children' in video:
                sageid = sagex.FindSageID(video)
                if FOLDERS_COUNT_IN_TITLE:
                    folderTitle = video['title'] + " (" + str(len(video['children'])) + " Airing Items)"
                else:
                    folderTitle = video['title']

                airing = sagex.FindFirstChild(video)
                thumb = sagex.GetFanartFor(mediafile=airing, artifact='poster', mediatype='tv')

                dir.add(
                    DirectoryObject(key=Callback(ProcessChildren, title=title, viewName=viewName, path=sagex.AppendPath(path, video['title'])),
                                    title=folderTitle,
                                    thumb=thumb
                                    )
                )
            else:
                dir.add(PhoenixObject(video))

    dir.art=sagex.GetBackground(sagex.FindSageID(json))

    if len(dir)<1:
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + title)

    return dir


def PhoenixObject(media):
    if sagex.IsAirings(media):
        return NewPhoenixAiringObject(media)
    else:
        return NewPhoenixMediaObject(media)


def NewPhoenixAiringObject(media):
    o = EpisodeObject()
    aired = Datetime.FromTimestamp((sagex.jsonval(media, "airingTime")) / 1000)
    o.title = sagex.jsonval(media, 'title') + " - " + sagex.jsonval(media, 'episodeName') + " - " + aired.strftime("%a %I:%M %p")
    o.show = sagex.jsonval(media, 'title')
    o.season = sagex.jsonval(media, 'season')
    o.index = sagex.jsonval(media, 'episode')
    desc = aired.strftime("%a, %b %d at %I:%M %p\n") + sagex.jsonval(media, 'description')
    o.summary = desc
    o.duration = sagex.jsonval(media, "runtime")
    o.originally_available_at = aired
    o.thumb = sagex.GetFanartFor(mediafile=media, artifact='poster', mediatype='tv')
    o.url = sagex.GetAiringUrl(media)
    return o


def NewPhoenixMediaObject(media):
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
        o.summary = sagex.jsonval(media,'description')
    else:
        o = VideoClipObject()
        o.title = sagex.jsonval(media, 'title')
        o.summary = sagex.jsonval(media,'description')
        o.year = sagex.jsonval(media, 'year')

    if o.title is None:
        Log(media)

    o.url = sagex.GetStreamUrl(media)
    o.thumb = sagex.GetThumb(media)
    o.duration = sagex.jsonval(media, "runtime")

    try:
        o.originally_available_at = Datetime.FromTimestamp((sagex.jsonval(media, "airingTime")) / 1000)
    except:
        pass

    return o


