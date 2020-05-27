import urwid
from pygments import highlight
from pygments.lexers import MarkdownLexer
from pygments.formatters import TerminalFormatter
from .mdformat import urwidify_content
from .comments import CommentDisplay
from .webview import render_web


def render_link(post):
    if post.is_self:
        content = highlight(post.selftext, MarkdownLexer(), TerminalFormatter())
        content = urwidify_content(content)
        return urwid.Filler(
            urwid.ListBox(content),
            valign='top',
            height=('relative', 100)
        )
    else:
        return render_web(post)

def render_comments(post):
    cdp = CommentDisplay(post)
    return urwid.Filler(
        cdp,
        valign='top',
        height=('relative', 100)
    )

