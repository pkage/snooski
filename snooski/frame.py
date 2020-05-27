
import urwid
import praw
from .postlist import PostListDisplay
import json
from .data import convert_submission_to_obj
from .content import render_link, render_comments
from . import mdformat

palette = [
    ('title', 'bold', ''),
    ('author', 'dark gray', ''),
    ('sticky_title', 'dark green,bold', ''),
    ('selected', 'standout', ''),
    ('selected_post', 'light blue', ''),
    ('selected_title', 'light blue,bold', ''),
    ('comment_header', 'light blue', ''),
    ('comment_header_active', 'light blue,bold', ''),
    ('titlebar', 'standout', ''),
    ('titlebar_active', 'white', 'black'),
    ('active', 'light green', ''),
    ('inactive', 'light red', ''),
    ('popbg', 'white', 'dark blue')
]

class Snooski(urwid.WidgetWrap):
    def __init__(self, credfile):
        with open(credfile, 'r') as cfile:
            creds = json.load(cfile)

        self.r = praw.Reddit(client_id=creds['client_id'],
                     client_secret=creds['client_secret'],
                     username=creds['username'],
                     password=creds['password'],
                     user_agent='term:UNFrngLesKyhjw:0.0a /u/quadnix')

        self.create_layout()
        super().__init__(self.frame)

    def create_layout(self):
        self.postlist = PostListDisplay()
        urwid.connect_signal(self.postlist.walker, 'open_link', self.update_content)
        urwid.connect_signal(self.postlist.walker, 'open_comments', self.update_content)

        # command prompt
        self.prompt = urwid.Edit('> ')

        # menu bar
        self.menubar = urwid.Pile([
            urwid.AttrMap(
                urwid.Columns([
                    ('pack', urwid.AttrMap(urwid.SelectableIcon(' file '), None, focus_map='titlebar_active')),
                    ('pack', urwid.AttrMap(urwid.SelectableIcon(' options '), None, focus_map='titlebar_active'))
                ]),
                'titlebar'
            ),
            urwid.Divider()
        ])

        # content display
        self.display_content = urwid.WidgetPlaceholder(
            urwid.LineBox(
                urwid.Filler(
                    urwid.Text(('inactive', '[no content selected]'), align='center'))))

        # frame
        self.frame = urwid.Frame(
            urwid.Columns([
                urwid.Filler(
                    self.postlist,
                    height=('relative', 100)
                ),
                self.display_content
            ]),
            header=self.menubar,
            footer=urwid.AttrMap(self.prompt, None, focus_map='active')
        )

    def keypress(self, size, key):
        key = super().keypress(size, key)

        if key is not None:
            #print('key: ' + repr(key))
            if key == '.' or key == ':':
                self.frame.focus_position = 'footer'

            if key == 'esc':
                self.prompt.set_edit_text('')
                if self.frame.focus_position == 'body':
                    self.frame.focus_position = 'header'
                else:
                    self.frame.focus_position = 'body'

            if key == 'enter':
                self.process_cmd(self.prompt.get_edit_text())
                self.prompt.set_edit_text('')
                self.frame.focus_position = 'body'

            if key == 'tab':
                if self.frame.body.focus_position == 0:
                    self.frame.body.focus_position = 1
                else:
                    self.frame.body.focus_position = 0

    def update_content(self, data):
        if data[1] == 'link':
            self.display_content.original_widget = render_link(data[0])
            self.frame.body.focus_position = 1
        else:
            self.display_content.original_widget = render_comments(data[0])

    def process_cmd(self, cmd):
        if cmd == 'Q' or cmd == 'q':
            raise urwid.ExitMainLoop()
        elif cmd[:2] == 'r/':
            cmd = cmd[2:]
            if '/' in cmd:
                cmd, sort = cmd.split('/')
            else:
                sort = 'hot'
            self.postlist.load(getattr(self.r.subreddit(cmd), sort)())



