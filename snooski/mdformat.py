import urwid
from copy import deepcopy

def get_palette():
    fg_colors = {
        '39': '',
        '30': 'black',
        '31': 'dark red',
        '32': 'dark green',
        '33': 'brown',
        '34': 'dark blue',
        '35': 'dark magenta',
        '36': 'dark cyan',
        '37': 'light gray',
        '1;31': 'light red',
        '1;32': 'light green',
        '1;33': 'yellow',
        '1;34': 'light blue',
        '1;35': 'light magenta',
        '1;36': 'light cyan',
        '1;37': 'white'
    }

    bg_colors = {
        '': '',
        '49': '',
        '40': 'black',
        '41': 'dark red',
        '42': 'dark green',
        '43': 'brown',
        '44': 'dark blue',
        '45': 'dark magenta',
        '46': 'dark cyan',
        '47': 'light gray'
    }

    text_modes = {
        '': '',
        '00': '',
        '01': 'bold',
        '04': 'underline',
        '07': 'standout'
    }

    palette = []
    for textmode_key in text_modes:
        for bg_key in bg_colors:
            for fg_key in fg_colors:
                ecode = [fg_key]
                if bg_colors[bg_key] != '':
                    ecode.append(bg_key)
                if text_modes[textmode_key] != '':
                    ecode.append(textmode_key)

                ecode = ';'.join(ecode)
                palette.append((
                    'escape_{}'.format(ecode),
                    fg_colors[fg_key] + ((',' + text_modes[textmode_key]) if text_modes[textmode_key] != '' else ''),
                    bg_colors[bg_key]
                ))

    return palette


def process_escapes(text):
    out = []
    text = '\u001b[39;49;00m' + text + '\n'
    text = text.split('\u001b[')
    for chunk in text:
        endofcode = chunk.find('m')
        out.append(('escape_{}'.format(chunk[:endofcode]), chunk[endofcode + 1:]))

    return out

def urwidify_content(text):
    nobr = []
    for chunk in process_escapes(text):
        text = chunk[1].split('\n')
        if len(text) > 1:
            for i in range(len(text)):
                if i == 0:
                    nobr.append((chunk[0], text[i], False))
                else:
                    nobr.append((chunk[0], text[i], True))
        else:
            nobr.append((chunk[0], chunk[1], False))

    lines = []
    line = []
    for tch in nobr:
        if tch[2]:
            lines.append(deepcopy(line))
            line = []
        line.append((tch[0], tch[1]))
    lines.append(deepcopy(line))

    out = []
    for ln in lines:
        out.append(urwid.SelectableIcon(ln, cursor_position=0))
    return out


if __name__ == '__main__':
    from pygments import highlight
    from pygments.lexers import MarkdownLexer
    from pygments.formatters import TerminalFormatter
    import json

    with open('/tmp/testmdraw', 'r') as f:
        text = '\n'.join(f.readlines())

    content = highlight(text, MarkdownLexer(), TerminalFormatter())
    content = urwidify_content(content)

    json.dump(get_palette(), open('/tmp/mdstyles', 'w'), indent=4)


    print(content)
