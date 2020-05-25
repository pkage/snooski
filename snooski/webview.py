import urwid
import webbrowser
import requests
from mdformat import urwidify_content
from postlist import SelectableButton
from newspaper import Article
from pygments import highlight
from pygments.lexers import HtmlLexer
from pygments.formatters import TerminalFormatter

class OpenLinkDialog(urwid.WidgetWrap):
    signals = ['close', 'extract', 'raw', 'open']
    def __init__(self):
        extract_btn = urwid.Button('extract article')
        raw_btn = urwid.Button('raw html')
        open_btn = urwid.Button('open in browser')
        close_btn = urwid.Button('close menu')

        # quick n dirty signal setup
        urwid.connect_signal(close_btn, 'click',
            lambda button:self._emit("close"))
        urwid.connect_signal(extract_btn, 'click',
            lambda button:self._emit("extract"))
        urwid.connect_signal(raw_btn, 'click',
            lambda button:self._emit("raw"))
        urwid.connect_signal(open_btn, 'click',
            lambda button:self._emit("open"))

        pile = urwid.Pile([
            close_btn,
            extract_btn,
            raw_btn,
            open_btn
        ])

        fill = urwid.Filler(pile)
        super().__init__(urwid.AttrWrap(fill, 'popbg'))

class LinkDisplayOpts(urwid.PopUpLauncher):
    signals = ['open_extract', 'open_raw']
    def __init__(self, url):
        self.url = url
        openbtn = SelectableButton(self.url)
        super().__init__(urwid.AttrMap(openbtn, None, focus_map='selected'))

        # popup setup
        urwid.connect_signal(openbtn, 'click',
            lambda button: self.open_pop_up())

    def create_pop_up(self):
        pop_up = OpenLinkDialog()
        # signal setup
        urwid.connect_signal(pop_up, 'close',
            lambda button: self.close_pop_up())
        urwid.connect_signal(pop_up, 'extract',
            lambda button: self.open_extract())
        urwid.connect_signal(pop_up, 'raw',
            lambda button: self.open_raw())
        urwid.connect_signal(pop_up, 'open',
            lambda button: self.open_browser())
        return pop_up

    def open_extract(self):
        urwid.emit_signal(self, 'open_extract')
        self.close_pop_up()

    def open_raw(self):
        urwid.emit_signal(self, 'open_raw')
        self.close_pop_up()

    def open_browser(self):
        webbrowser.open(self.url)
        self.close_pop_up()

    def get_pop_up_parameters(self):
        return {'left':0, 'top':1, 'overlay_width': 19, 'overlay_height': 4}

class LinkDisplay(urwid.WidgetWrap):
    def __init__(self, post):
        self.post = post

        self.renderarea = urwid.WidgetPlaceholder(
            urwid.Filler(
                urwid.Text('content not\nauto-loaded', align='center')
            )
        )

        self.viewopts = LinkDisplayOpts(post.url)
        urwid.connect_signal(self.viewopts, 'open_extract', self.open_extract)
        urwid.connect_signal(self.viewopts, 'open_raw', self.open_raw)

        # check the header for content-types, load it if it's probably an article
        r = requests.head(self.post.url)
        if 'content-type' in r.headers and r.headers['content-type'].split(';')[0] == 'text/html':
            try:
                self.open_extract()
            except:
                status, reason = self.get_http_error()
                self.renderarea = urwid.WidgetPlaceholder(
                    urwid.Filler(
                        urwid.Text('error loading selected\ncontent ({} {})'.format(status, reason), align='center')
                    )
                )
            
        self.frame = urwid.Frame(
            urwid.LineBox(
                self.renderarea
            ),
            header=self.viewopts
        )
        self.frame.focus_position = 'header'

        super().__init__(self.frame)

    def open_extract(self):
        article = Article(self.post.url)
        article.download()
        article.parse()

        adsp = urwid.ListBox(
            [urwid.Pile([
                urwid.Text(('title', article.title)),
                urwid.Text(('author', ', '.join(article.authors))),
                urwid.Divider()
            ])] + urwidify_content(article.text)
        )

        self.renderarea.original_widget = urwid.Filler(
            adsp,
            height=('relative', 100),
            valign='top'
        )

    def get_http_error(self):
        r = requests.get(self.post.url)
        return r.status_code, r.reason

    def open_raw(self):
        r = requests.get(self.post.url)

        allowed_headers = [
            'text/html',
            'text/plain',
            'application/json'
        ]
        if not r.headers['content-type'].split(';')[0] in allowed_headers:
            self.renderarea.original_widget = urwid.Filler(
                urwid.Text((
                    'inactive',
                    'could not load\ncontent-type {}'.format(r.headers['content-type'])),
                    align='center')
            )
            return
        content = highlight(r.text, HtmlLexer(), TerminalFormatter())
        content = urwidify_content(content)

        adsp = urwid.ListBox(content)
        self.renderarea.original_widget = urwid.Filler(
            adsp,
            height=('relative', 100),
            valign='top'
        )

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key is not None:
            if self.frame.focus_position == 'body':
                if key == 'up':
                    self.frame.focus_position = 'header'
            elif self.frame.focus_position == 'header':
                if key == 'down':
                    self.frame.focus_position = 'body'
        return key


def render_web(post):
    return urwid.Filler(
        LinkDisplay(post),
        valign='top',
        height=('relative', 100)
    )
