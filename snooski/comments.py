import urwid
import praw
from pygments import highlight
from pygments.lexers import MarkdownLexer
from pygments.formatters import TerminalFormatter
from mdformat import urwidify_content
from postlist import SelectableButton
import arrow

class CommentDisplay(urwid.WidgetWrap):
    mardown_lexer = MarkdownLexer()
    terminal_formatter = TerminalFormatter()

    def __init__(self, post):
        self.collapsed = set()
        self.root = urwid.WidgetPlaceholder(urwid.ListBox([urwid.Text('loading')]))
        super().__init__(self.root)
        self.create_comment_list(post)

    def render_comments(self, index=0):
        cmts = []
        skipdepth = 9999
        for i in range(len(self.comments)):
            if self.comments[i].depth > skipdepth:
                continue
            else:
                skipdepth = 9999
            if self.comments[i].id in self.collapsed:
                if self.comments[i].depth < skipdepth:
                    skipdepth = self.comments[i].depth
            cmts.append(self.render_comment(self.comments[i], i))

        cmts.append(urwid.Text(''))
        self.root.original_widget = urwid.ListBox(cmts)
        self.root.original_widget.focus_position = index

    def render_comment(self, comment, index):
        if type(comment) is praw.models.Comment:
            content = highlight(comment.body, self.mardown_lexer, self.terminal_formatter)
            content = urwidify_content(content)
            header = SelectableButton('[{}] {} | {} | /u/{}{}'.format(
                '+' if comment.id in self.collapsed else '-',
                '*' if comment.score_hidden else comment.score,
                arrow.get(comment.created_utc).to('local').humanize(),
                comment.author.name if comment.author is not None else '[deleted]',
                ' (op)' if comment.is_submitter else ''
            ))
            urwid.connect_signal(header, 'click', self.toggle_collapse, (comment.id, index))
            lb = urwid.Pile([urwid.AttrMap(
                header,
                'comment_header',
                focus_map='comment_header_active'
            )] + ([] if comment.id in self.collapsed else content))
        else:
            loadmore = urwid.Button('load more comments')
            urwid.connect_signal(loadmore, 'click', self.expand_at, index)
            lb = urwid.AttrMap(loadmore, None, focus_map='selected')


        return urwid.Padding(lb, left=comment.depth*2)

    def toggle_collapse(self, button, data):
        if data[0] in self.collapsed:
            self.collapsed.remove(data[0])
        else:
            self.collapsed.add(data[0])
        self.render_comments(self.root.original_widget.focus_position)

    def create_comment_list(self, post):
        self.comments = []
        flats = [self.flatten_comments(c) for c in list(post.comments)]
        for flat in flats:
            self.comments += flat
        self.render_comments()

    def expand_at(self, button, index):
        if type(self.comments[index]) is praw.models.MoreComments:
            olddepth = self.comments[index].depth
            fst = self.comments[:index]
            lst = self.comments[index + 1:]

            cmts = self.comments[index].comments(update=False)

            cs = [self.flatten_comments(c, depth=olddepth) for c in cmts]
            mid = []
            for c in cs:
                mid += c

            self.comments = fst + mid + lst
            self.render_comments(self.root.original_widget.focus_position)
            #self.root.original_widget = urwid.ListBox([urwid.Text(repr(mid))])


    def flatten_comments(self, cobj, depth=0):
        cobj.depth = depth
        out = [cobj]

        if type(cobj) is praw.models.Comment:
            for reply in cobj.replies:
                out += self.flatten_comments(reply, depth + 1)
        return out
