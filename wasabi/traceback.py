# coding: utf8
from __future__ import unicode_literals, print_function

from .util import color, to_string, supports_ansi, locale_escape, NO_UTF8


LINE_EDGE = "└─" if not NO_UTF8 else "|_"
LINE_FORK = "├─" if not NO_UTF8 else "|__"
LINE_PATH = "──" if not NO_UTF8 else "__"


class TracebackPrinter(object):
    def __init__(
        self,
        color_error="red",
        color_tb="blue",
        color_highlight="yellow",
        indent=2,
        tb_base=None,
        tb_exclude=tuple(),
    ):
        """Initialize a traceback printer.

        color_error (unicode / int): Color name or code for errors.
        color_tb (unicode / int): Color name or code for traceback headline.
        color_highlight (unicode / int): Color name or code for highlights.
        indent (int): Indentation in spaces.
        tb_base (unicode): Name of directory to use to show relative paths. For
            example, "thinc" will look for the last occurence of "/thinc/" in
            a path and only show path to the right of it.
        tb_exclude (tuple): List of filenames to exclude from traceback.
        RETURNS (TracebackPrinter): The traceback printer.
        """
        self.color_error = color_error
        self.color_tb = color_tb
        self.color_highlight = color_highlight
        self.indent = " " * indent
        self.tb_base = "/{}/".format(tb_base) if tb_base else None
        self.tb_exclude = tuple(tb_exclude)
        self.supports_ansi = supports_ansi()

    def __call__(self, title, *texts, **settings):
        """Output custom formatted tracebacks and errors.

        title (unicode): The message title.
        *texts (unicode): The texts to print (one per line).
        highlight (unicode): Optional sequence to highlight in the traceback,
            e.g. the bad value that caused the error.
        tb (iterable): The traceback, e.g. generated by traceback.extract_stack().
        RETURNS (unicode): The formatted traceback. Can be printed or raised
            by custom exception.
        """
        highlight = settings.get("highlight", False)
        tb = settings.get("tb", None)
        if self.supports_ansi:  # use first line as title
            title = color(title, fg=self.color_error, bold=True)
        info = "\n" + "\n".join([self.indent + text for text in texts]) if texts else ""
        tb = self._get_traceback(tb, highlight) if tb else ""
        msg = "\n\n{}{}{}{}\n".format(self.indent, title, info, tb)
        return msg
        # return locale_escape(msg, errors="ignore")

    def _get_traceback(self, tb, highlight):
        # Exclude certain file names from traceback
        tb = [record for record in tb if not record[0].endswith(self.tb_exclude)]
        tb_range = tb[-5:-2]
        tb_list = [
            self._format_traceback(path, line, fn, text, i, len(tb_range), highlight)
            for i, (path, line, fn, text) in enumerate(tb_range)
        ]
        tb_data = "\n".join(tb_list).strip()
        title = "Traceback:"
        if self.supports_ansi:
            title = color(title, fg=self.color_tb, bold=True)
        return "\n\n{indent}{title}\n{indent}{tb}".format(
            title=title, tb=tb_data, indent=self.indent
        )

    def _format_traceback(self, path, line, fn, text, i, count, highlight):
        template = "{base_indent}{indent} {fn} [{line}] in {path}{text}"
        indent = (LINE_EDGE if i == count - 1 else LINE_FORK) + LINE_PATH * i
        if self.tb_base and self.tb_base in path:
            path = path.rsplit(self.tb_base, 1)[1]
        text = self._format_user_error(text, i, highlight) if i == count - 1 else ""
        line = to_string(line)
        if self.supports_ansi:
            fn = color(fn, bold=True)
            path = color(path, underline=True)
        return template.format(
            base_indent=self.indent,
            line=line,
            indent=indent,
            text=text,
            fn=fn,
            path=path,
        )

    def _format_user_error(self, text, i, highlight):
        spacing = "  " * i + " >>>"
        if self.supports_ansi:
            spacing = color(spacing, fg=self.color_error)
        if highlight and self.supports_ansi:
            highlight = to_string(highlight)
            formatted_highlight = color(highlight, fg=self.color_highlight)
            text = text.replace(highlight, formatted_highlight)
        return "\n{}  {} {}".format(self.indent, spacing, text)
