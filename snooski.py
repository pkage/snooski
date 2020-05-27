import urwid
from snooski.frame import Snooski, palette
from snooski import mdformat

snooski = Snooski('./creds.json')
urwid.MainLoop(snooski, palette + mdformat.get_palette(), pop_ups=True).run()
