# static service methods for sagex.pys
jsonval = SharedCodeService.sagex.jsonval
PhoenixAPI = SharedCodeService.sagex.PhoenixAPI
SageAPI = SharedCodeService.sagex.SageAPI
GetPath = SharedCodeService.sagex.GetPath
IsAirings = SharedCodeService.sagex.IsAirings
FindSageID = SharedCodeService.sagex.FindSageID
AppendPath = SharedCodeService.sagex.AppendPath
GetThumb = SharedCodeService.sagex.GetThumb
GetBackground = SharedCodeService.sagex.GetBackground
FindFirstChild = SharedCodeService.sagex.FindFirstChild
GetFanartFor = SharedCodeService.sagex.GetFanartFor
GetAiringUrl = SharedCodeService.sagex.GetAiringUrl
GetStreamUrl = SharedCodeService.sagex.GetStreamUrl
PhoenixObject = SharedCodeService.sagex.PhoenixObject
PhoenixMediaObject = SharedCodeService.sagex.PhoenixMediaObject

VIDEO_PREFIX = "/video/sagex/phoenix"

NAME = L('Title')

ART  = 'art-default.jpg'
ICON = 'icon.png'

VERSION="1.0.3-beta"

DEFAULT_MENU = [
    {
        'title':'TV Shows',
        'view':'phoenix.view.default.allTV',
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
    Log("Starting Phoenix Plex Plugin: " + VERSION)
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
                             viewName=jsonval(menu, 'view'),
                             title=jsonval(menu, 'title'),
                             end=jsonval(menu, 'items', -1)),
                title=jsonval(menu, 'title'),
                thumb=R('movies.png')
            )
            dir.add(item)
    except:
        Log('Possible server communication problems')

    dir.add(SearchDirectoryObject(identifier='com.plexapp.plugins.sagexphoenix', title='Search SageTV', prompt='Search for SageTV Media Files', term='SageTV'))
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to the SageTV backend", thumb=R("icon-prefs.png")))
    dir.add(DirectoryObject(key=Callback(About), title='About', thumb=R('info.png')));

    return dir


@route(VIDEO_PREFIX + '/about')
def About():
    return ObjectContainer(header='About Phoenix', message='Phoenix Plex Plugin Version ' + VERSION)


def LoadMenuFromServer(menuname='userdata/Phoenix/Menus/plexmenu.json'):
    if Prefs['enable_custom_menu'] is False:
        return DEFAULT_MENU

    menusStr = SageAPI('GetFileAsString', [menuname])
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
def GetView(viewName, title, start=0, end=-1):
    try:
        videos = PhoenixAPI('phoenix.umb.CreateView', [viewName], start, end)
    except:
        Log("View returned an error: " + viewName)
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
        return ObjectContainer(header='No Media', message='Empty View ' + viewName)

    return dir


@route(VIDEO_PREFIX + '/vfs/getview/children', allow_sync=True)
def ProcessChildren(title, viewName, path):
    Log('Processing View: ' + viewName + " with path " + path)

    json = GetPath(Dict[viewName], path)

    if json is None:
        Log('VIEW: ' + viewName + " was empty");
        return ObjectContainer(header='No Data for View', message='The view, ' + title + ', was empty')

    if IsAirings(json):
        return ProcessAirings(title, viewName, path, json)
    else:
        return ProcessMediaItems(title, viewName, path, json)


def ProcessMediaItems(title, viewName, path, json):
    dir = ObjectContainer(title2=title, view_group='InfoList')

    if 'children' in json:
        if 'title' in json:
            dir.title1 = json['title']

        for video in json['children']:
            if 'children' in video:
                sageid = FindSageID(video)
                if FOLDERS_COUNT_IN_TITLE:
                    folderTitle = video['title'] + " (" + str(len(video['children'])) + " Items)"
                else:
                    folderTitle = video['title']
                dir.add(
                    DirectoryObject(key=Callback(ProcessChildren, title=title, viewName=viewName, path=AppendPath(path, video['title'])),
                                    title=folderTitle,
                                    thumb=GetThumb(sageid),
                                    art=GetBackground(sageid))
                )
            else:
                dir.add(PhoenixMediaObject(video))

    dir.art=GetBackground(FindSageID(json))

    if len(dir)<1:
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + title)

    return dir


def ProcessAirings(title, viewName, path, json):
    dir = ObjectContainer(title2=title, view_group='InfoList')

    if 'children' in json:
        if 'title' in json:
            dir.title1 = json['title']

        for video in json['children']:
            if 'children' in video:
                sageid = FindSageID(video)
                if FOLDERS_COUNT_IN_TITLE:
                    folderTitle = video['title'] + " (" + str(len(video['children'])) + " Airing Items)"
                else:
                    folderTitle = video['title']

                airing = FindFirstChild(video)
                thumb = GetFanartFor(mediafile=airing, artifact='poster', mediatype='tv')

                dir.add(
                    DirectoryObject(key=Callback(ProcessChildren, title=title, viewName=viewName, path=AppendPath(path, video['title'])),
                                    title=folderTitle,
                                    thumb=thumb
                                    )
                )
            else:
                dir.add(PhoenixObject(video))

    dir.art=GetBackground(FindSageID(json))

    if len(dir)<1:
        return ObjectContainer(header='No Data for View', message='Unable to load the view ' + title)

    return dir




