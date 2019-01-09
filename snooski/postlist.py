#! /usr/bin/env python

import urwid
import json
import arrow

class SelectableButton(urwid.SelectableIcon):
    signals = ['click']
    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == 'enter':
            urwid.emit_signal(self, 'click', self)
        else:
            return key

class OpenPostDialog(urwid.WidgetWrap):
    signals = ['close', 'link', 'comments']
    def __init__(self, is_self):
        open_link_btn = urwid.Button('self text' if is_self else 'link')
        open_comments_btn = urwid.Button('comments')
        clost_btn = urwid.Button('close menu')

        # quick n dirty signal setup
        urwid.connect_signal(clost_btn, 'click',
            lambda button:self._emit("close"))
        urwid.connect_signal(open_link_btn, 'click',
            lambda button:self._emit("link"))
        urwid.connect_signal(open_comments_btn, 'click',
            lambda button:self._emit("comments"))

        pile = urwid.Pile([
            clost_btn,
            open_link_btn,
            open_comments_btn
        ])

        fill = urwid.Filler(pile)
        super().__init__(urwid.AttrWrap(fill, 'popbg'))

class PostDisplay(urwid.PopUpLauncher):
    signals = ['open_link', 'open_comments']
    def __init__(self, postdata, index):
        self.postdata = postdata
        self.index = index

        openbtn = SelectableButton('#[{}] {}'.format(
            self.index + 1,
            self.postdata.title
        ), cursor_position=0)

        pile = urwid.Pile([
            urwid.AttrMap(
                openbtn,
                ('sticky_title' if self.postdata.stickied else 'title'),
                focus_map=('sticky_title' if self.postdata.stickied else 'selected_title')),
            urwid.Text('{} | {} | {} | /r/{} | /u/{} | {} comments'.format(
                postdata.score,
                arrow.get(postdata.created_utc).to('local').humanize(),
                '(self)' if postdata.is_self else postdata.domain,
                postdata.subreddit,
                postdata.author if postdata.author is not None else '[deleted]',
                postdata.num_comments)),
            urwid.Text('')
        ])
        super().__init__(urwid.AttrMap(pile, None, focus_map='selected_post'))

        # popup setup
        urwid.connect_signal(openbtn, 'click',
            lambda button: self.open_pop_up())

    def create_pop_up(self):
        pop_up = OpenPostDialog(self.postdata.is_self)
        # signal setup
        urwid.connect_signal(pop_up, 'close',
            lambda button: self.close_pop_up())
        urwid.connect_signal(pop_up, 'link',
            lambda button: self.open_link())
        urwid.connect_signal(pop_up, 'comments',
            lambda button: self.open_comments())
        return pop_up

    def open_link(self):
        urwid.emit_signal(self, 'open_link', self.postdata)
        self.close_pop_up()

    def open_comments(self):
        urwid.emit_signal(self, 'open_comments', self.postdata)
        self.close_pop_up()

    def get_pop_up_parameters(self):
        return {'left':0, 'top':2, 'overlay_width': 15, 'overlay_height':3}

def new_random_post(length):
    return {
        'title': 'random post (len {})'.format(length),
        'author': 'test',
        'subreddit': 'testsub',
        'score': 1,
        'comments': 0
    }

class PostListWalker(urwid.ListWalker):
    signals = ['open_link', 'open_comments']
    def __init__(self, source):
        # initialize the superclass
        super().__init__()

        if source is not None:
            self.reset(source)
        else:
            self.posts=[self.display_header('no data source')]
            self.position = 0

    def reset(self, source):
        # create the default post list
        self.source = source

        self.posts = []
        for i in range(0, 25):
            self.posts.append(self.display_post(next(self.source), i))

        #self.posts += [self.display_post(post) for post in json.load(open('../test.json', 'r'))['posts']]

        self.create_load_more()

        # default selection position
        self.position = 0

    def create_load_more(self):
        loadmore = urwid.Button('Load more posts...')
        urwid.connect_signal(loadmore, 'click', self.load_more_posts)
        self.posts.append(urwid.AttrMap(loadmore, None, focus_map='selected'))

    def load_more_posts(self, button):
        additional = []
        for i in range(0, 25):
            additional.append(self.display_post(next(self.source), len(self.posts) - 1 + i))

        self.posts = self.posts[:-1] + additional
        self.create_load_more()
        self._modified()

    def get_focus(self):
        if self.position < 0 or self.position >= len(self.posts):
            return (None, None)
        return (self.posts[self.position], self.position)

    def set_focus(self, pos):
        if pos < 0 or pos >= len(self.posts):
            raise IndexError()
        self.position = pos
        # notify the walker that things have been modified
        self._modified()

    def get_next(self, pos):
        if pos + 1 >= len(self.posts):
            return (None, None)
        return (self.posts[pos + 1], pos + 1)

    def get_prev(self, pos):
        if pos - 1 < 0:
            return (None, None)
        return (self.posts[pos - 1], pos - 1)

    def display_post(self, postdata, index):
        #postdata = convert_submission_to_obj(postdata)
        post = PostDisplay(postdata, index)
        urwid.connect_signal(post, 'open_comments', self.open_comments)
        urwid.connect_signal(post, 'open_link', self.open_link)
        return urwid.AttrMap(post, None, focus_map='title')

    def display_header(self, title):
        return urwid.Text(('title', '{}\n'.format(title)))

    def open_comments(self, post):
        urwid.emit_signal(self, 'open_comments', (post, 'comments'))

    def open_link(self, post):
        urwid.emit_signal(self, 'open_link', (post, 'link'))

class PostListDisplay(urwid.WidgetWrap):
    def __init__(self):
        self.walker = PostListWalker(None)
        # urwid.connect_signal(self.walker, 'post_clicked', post_clicked)

        self.postlist = urwid.Padding(
            urwid.ListBox(self.walker),
            left=2,
            right=2
        )

        super().__init__(self.postlist)


    def load(self, source):
        self.walker.reset(source)

#urwid.MainLoop(PostListDisplay(), palette, pop_ups=True).run()
