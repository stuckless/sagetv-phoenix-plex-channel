import sagex as sagex

VIDEO_PREFIX = "/video/sagex/phoenix"

NAME = L('Title')

ART  = 'art-default.jpg'
ICON = 'icon.png'

VERSION="1.0.1-beta"

DEFAULT_MENU = [
    {
        'title':'TV Shows',
        'view':'phoenix.view.default.TV',
        'items': 100
    },
    {
        'title':'Recent Recordings',
        'view':'phoenix.view.util.recentrecordings',
        'items': 50
    },
    {
        'title':'Recent Imports',
        'view':'phoenix.view.util.recentimports',
        'items': 50
    },
    {
        'title':'Upcomming Movies',
        'view':'phoenix.view.default.upcomingmovies',
        'items': 50
    },
    {
        'title':'Home Videos',
        'view':'phoenix.view.default.homevideos',
        'items': 50
    },
    {
        'title':'All Movies',
        'view':'phoenix.view.default.allMovies',
        'items': 50
    },
    {
        'title':'Video Folders',
        'view':'phoenix.view.default.videofolders',
        'items': 50
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
@handler(VIDEO_PREFIX, 'Phoenix', art=ART, thumb=ICON)
def MainMenu():
    dir=ObjectContainer(title1="Phoenix")

    try:
        menus = LoadMenuFromServer()
        for menu in menus:
            item = DirectoryObject(
                key=Callback(GetView,
                             viewName=sagex.jsonval(menu, 'view'),
                             title=sagex.jsonval(menu, 'title'),
                             end=sagex.jsonval(menu, 'items', -1)),
                title=sagex.jsonval(menu, 'title'),
                thumb=R('movies.png')
            )
            dir.add(item)
    except:
        Log('Possible server communication problems')

    #if Client.Product != 'PlexConnect':
    dir.add(SearchDirectoryObject(identifier='com.plexapp.plugins.sagexphoenix', title='Search SageTV', prompt='Search for SageTV Media Files', term='SageTV'))

    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to the SageTV backend", thumb=R("icon-prefs.png")))

    dir.add(DirectoryObject(key=Callback(About), title='About', thumb=R('info.png')));

    return dir


@route(VIDEO_PREFIX + '/about')
def About():
    return MessageContainer(header='About Phoenix', message='Phoenix Plex Plugin Version ' + VERSION)


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

@route(VIDEO_PREFIX + '/vfs/getview/{viewName}/{start}/{end}', allow_sync=True)
def GetView(viewName, title, start=0, end=-1):
    try:
        videos = sagex.PhoenixAPI('phoenix.umb.CreateView', [viewName], start, end)
    except:
        Log("View returned an error: " + viewName);
        videos = None

    if videos is None:
        return ObjectContainer(header='No Files', message='No files for the given view ' + title)

    if 'title' not in videos:
        Log(videos)
        return ObjectContainer(header='No Files', message='No files for the given view ' + title)

    Dict[viewName] = videos

    Log('Processing Videos: viewName=' + viewName + "; title=" + title + "; start: " + str(start) + "; end: " + str(end))

    dir = ProcessChildren(title, viewName, path=Dict[viewName]['title'])

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
        o.title = sagex.jsonval(media,'episodeName')
        o.show = sagex.jsonval(media,'title')
        o.season = sagex.jsonval(media,'season')
        o.index = sagex.jsonval(media,'episode')
        if o.season > 0:
            o.title = ("%s (%sx%s)" % (sagex.jsonval(media, 'episodeName'), str(o.season), str(o.index)))
        o.summary = sagex.jsonval(media,'description')
    else:
        o = VideoClipObject()
        o.title = sagex.jsonval(media, 'title')
        o.summary = sagex.jsonval(media,'description')
        o.year = sagex.jsonval(media, 'year')
        if o.year > 0:
            o.title = "%s (%s)" % (sagex.jsonval(media, 'title'), str(o.year))

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


