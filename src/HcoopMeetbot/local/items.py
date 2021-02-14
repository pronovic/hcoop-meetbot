# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
# pylint: disable=invalid-name,unused-argument,protected-access,attribute-defined-outside-init,multiple-statements,redefined-outer-name,import-outside-toplevel,too-many-arguments,too-many-lines,too-many-locals,too-many-branches,too-many-public-methods,too-many-instance-attributes,too-many-statements,unused-variable,line-too-long:

# This code was originally taken from the ircmeeting package in Meetbot.  It
# was converted to Python 3, adjusted to fix PyCharm and pylint warnings, and
# reformatted to match my coding standard with black and isort.  In a lot of
# cases, warnings have been ignored because it's not viable to enforce my modern
# coding standard on this old code.

import re
import time

from . import writers

def inbase(i, chars="abcdefghijklmnopqrstuvwxyz", place=0):
    """Converts an integer into a postfix in base 26 using ascii chars.

    This is used to make a unique postfix for ReStructured Text URL
    references, which must be unique.  (Yes, this is over-engineering,
    but keeps it short and nicely arranged, and I want practice
    writing recursive functions.)
    """
    div, mod = divmod(i, len(chars) ** (place + 1))
    if div == 0:
        return chars[mod]
    else:
        return inbase(div, chars=chars, place=place + 1) + chars[mod]  # KJP original code had inbase2 here, no idea why


#
# These are objects which we can add to the meeting minutes.  Mainly
# they exist to aid in HTML-formatting.
#
class _BaseItem:
    itemtype = None
    starthtml = ""
    endhtml = ""
    startrst = ""
    endrst = ""
    starttext = ""
    endtext = ""
    startmw = ""
    endmw = ""
    url = ""
    nick = ""
    time = ""
    linenum = ""

    def get_replacements(self, M, escapewith):
        replacements = {}
        for name in dir(self):
            if name[0] == "_":
                continue
            replacements[name] = getattr(self, name)
        replacements["nick"] = escapewith(replacements["nick"])
        replacements["link"] = self.logURL(M)
        for key in ("line", "prefix", "suffix", "topic"):
            if key in replacements:
                replacements[key] = escapewith(replacements[key])
        if "url" in replacements:
            replacements["url_quoteescaped"] = escapewith(self.url.replace('"', "%22"))

        return replacements

    def template(self, M, escapewith):
        template = {}
        for k, v in self.get_replacements(M, escapewith).items():
            if k not in ("itemtype", "line", "topic", "url", "url_quoteescaped", "nick", "time", "link", "anchor"):
                continue
            template[k] = v
        return template

    def makeRSTref(self, M):
        if self.nick[-1] == "_":
            rstref = rstref_orig = "%s%s" % (self.nick, self.time)
        else:
            rstref = rstref_orig = "%s-%s" % (self.nick, self.time)
        count = 0
        while rstref in M.rst_refs:
            rstref = rstref_orig + inbase(count)
            count += 1
        link = self.logURL(M)
        M.rst_urls.append(".. _%s: %s" % (rstref, link + "#" + self.anchor))
        M.rst_refs[rstref] = True
        return rstref

    @property
    def anchor(self):
        return "l-" + str(self.linenum)

    def logURL(self, M):
        return M.config.basename + ".log.html"


class Topic(_BaseItem):
    itemtype = "TOPIC"
    html_template = """<tr><td><a href='%(link)s#%(anchor)s'>%(time)s</a></td>
        <th colspan=3>%(starthtml)sTopic: %(topic)s%(endhtml)s</th>
        </tr>"""
    # html2_template = ("""<b>%(starthtml)s%(topic)s%(endhtml)s</b> """
    #                  """(%(nick)s, <a href='%(link)s#%(anchor)s'>%(time)s</a>)""")
    html2_template = (
        """%(starthtml)s%(topic)s%(endhtml)s """
        """<span class="details">"""
        """(<a href='%(link)s#%(anchor)s'>%(nick)s</a>, """
        """%(time)s)"""
        """</span>"""
    )
    rst_template = """%(startrst)s%(topic)s%(endrst)s  (%(rstref)s_)"""
    text_template = """%(starttext)s%(topic)s%(endtext)s  (%(nick)s, %(time)s)"""
    mw_template = """%(startmw)s%(topic)s%(endmw)s  (%(nick)s, %(time)s)"""
    startrst = "**"
    endrst = "**"
    startmw = "'''"
    endmw = "'''"
    starthtml = '<b class="TOPIC">'
    endhtml = "</b>"

    def __init__(self, nick, line, linenum, time_):
        self.nick = nick
        self.topic = line
        self.linenum = linenum
        self.time = time.strftime("%H:%M:%S", time_)

    def _htmlrepl(self, M):
        repl = self.get_replacements(M, escapewith=writers.html)
        repl["link"] = self.logURL(M)
        return repl

    def html(self, M):
        return self.html_template % self._htmlrepl(M)

    def html2(self, M):
        return self.html2_template % self._htmlrepl(M)

    def rst(self, M):
        self.rstref = self.makeRSTref(M)
        repl = self.get_replacements(M, escapewith=writers.rst)
        if repl["topic"] == "":
            repl["topic"] = " "
        repl["link"] = self.logURL(M)
        return self.rst_template % repl

    def text(self, M):
        repl = self.get_replacements(M, escapewith=writers.text)
        repl["link"] = self.logURL(M)
        return self.text_template % repl

    def mw(self, M):
        repl = self.get_replacements(M, escapewith=writers.mw)
        return self.mw_template % repl


class GenericItem(_BaseItem):
    itemtype = ""
    html_template = """<tr><td><a href='%(link)s#%(anchor)s'>%(time)s</a></td>
        <td>%(itemtype)s</td><td>%(nick)s</td><td>%(starthtml)s%(line)s%(endhtml)s</td>
        </tr>"""
    # html2_template = ("""<i>%(itemtype)s</i>: %(starthtml)s%(line)s%(endhtml)s """
    #                  """(%(nick)s, <a href='%(link)s#%(anchor)s'>%(time)s</a>)""")
    html2_template = (
        """<i class="itemtype">%(itemtype)s</i>: """
        """<span class="%(itemtype)s">"""
        """%(starthtml)s%(line)s%(endhtml)s</span> """
        """<span class="details">"""
        """(<a href='%(link)s#%(anchor)s'>%(nick)s</a>, """
        """%(time)s)"""
        """</span>"""
    )
    rst_template = """*%(itemtype)s*: %(startrst)s%(line)s%(endrst)s  (%(rstref)s_)"""
    text_template = """%(itemtype)s: %(starttext)s%(line)s%(endtext)s  (%(nick)s, %(time)s)"""
    mw_template = """''%(itemtype)s:'' %(startmw)s%(line)s%(endmw)s  (%(nick)s, %(time)s)"""

    def __init__(self, nick, line, linenum, time_):
        self.nick = nick
        self.line = line
        self.linenum = linenum
        self.time = time.strftime("%H:%M:%S", time_)

    def _htmlrepl(self, M):
        repl = self.get_replacements(M, escapewith=writers.html)
        repl["link"] = self.logURL(M)
        return repl

    def html(self, M):
        return self.html_template % self._htmlrepl(M)

    def html2(self, M):
        return self.html2_template % self._htmlrepl(M)

    def rst(self, M):
        self.rstref = self.makeRSTref(M)
        repl = self.get_replacements(M, escapewith=writers.rst)
        repl["link"] = self.logURL(M)
        return self.rst_template % repl

    def text(self, M):
        repl = self.get_replacements(M, escapewith=writers.text)
        repl["link"] = self.logURL(M)
        return self.text_template % repl

    def mw(self, M):
        repl = self.get_replacements(M, escapewith=writers.mw)
        return self.mw_template % repl


class Info(GenericItem):
    itemtype = "INFO"
    html2_template = (
        """<span class="%(itemtype)s">"""
        """%(starthtml)s%(line)s%(endhtml)s</span> """
        """<span class="details">"""
        """(<a href='%(link)s#%(anchor)s'>%(nick)s</a>, """
        """%(time)s)"""
        """</span>"""
    )
    rst_template = """%(startrst)s%(line)s%(endrst)s  (%(rstref)s_)"""
    text_template = """%(starttext)s%(line)s%(endtext)s  (%(nick)s, %(time)s)"""
    mw_template = """%(startmw)s%(line)s%(endmw)s  (%(nick)s, %(time)s)"""


class Idea(GenericItem):
    itemtype = "IDEA"


class Agreed(GenericItem):
    itemtype = "AGREED"


class Action(GenericItem):
    itemtype = "ACTION"


class Help(GenericItem):
    itemtype = "HELP"


class Accepted(GenericItem):
    itemtype = "ACCEPTED"
    starthtml = '<font color="green">'
    endhtml = "</font>"


class Rejected(GenericItem):
    itemtype = "REJECTED"
    starthtml = '<font color="red">'
    endhtml = "</font>"


class Link(_BaseItem):
    itemtype = "LINK"
    html_template = """<tr><td><a href='%(link)s#%(anchor)s'>%(time)s</a></td>
        <td>%(itemtype)s</td><td>%(nick)s</td><td>%(starthtml)s%(prefix)s<a href="%(url)s">%(url_readable)s</a>%(suffix)s%(endhtml)s</td>
        </tr>"""
    html2_template = (
        """%(starthtml)s%(prefix)s<a href="%(url)s">%(url_readable)s</a>%(suffix)s%(endhtml)s """
        """<span class="details">"""
        """(<a href='%(link)s#%(anchor)s'>%(nick)s</a>, """
        """%(time)s)"""
        """</span>"""
    )
    rst_template = """*%(itemtype)s*: %(startrst)s%(prefix)s%(url)s%(suffix)s%(endrst)s  (%(rstref)s_)"""
    text_template = """%(itemtype)s: %(starttext)s%(prefix)s%(url)s%(suffix)s%(endtext)s  (%(nick)s, %(time)s)"""
    mw_template = """''%(itemtype)s:'' %(startmw)s%(prefix)s%(url)s%(suffix)s%(endmw)s  (%(nick)s, %(time)s)"""

    def __init__(self, nick, line, linenum, time_, M):
        self.nick = nick
        self.linenum = linenum
        self.time = time.strftime("%H:%M:%S", time_)
        self.line = line

        protocols = M.config.UrlProtocols
        protocols = "|".join(re.escape(p) for p in protocols)
        protocols = "(?:" + protocols + ")"
        # This is gross.
        # (.*?)          - any prefix, non-greedy
        # (%s//[^\s]+    - protocol://... until the next space
        # (?<!\.|\))     - but the last character can NOT be . or )
        # (.*)           - any suffix
        url_re = re.compile(r"(.*?)(%s//[^\s]+(?<![.)]))(.*)" % protocols)
        m = url_re.match(line)
        if m:
            self.prefix = m.group(1)
            self.url = m.group(2)
            self.suffix = m.group(3)
        else:
            # simple matching, the old way.
            self.url, self.suffix = (line + " ").split(" ", 1)
            self.suffix = " " + self.suffix
            self.prefix = ""
        # URL-sanitization
        self.url_readable = self.url  # readable line version
        self.url = self.url
        self.line = self.line.strip()

    def _htmlrepl(self, M):
        repl = self.get_replacements(M, escapewith=writers.html)
        # special: replace doublequote only for the URL.
        repl["url"] = writers.html(self.url.replace('"', "%22"))
        repl["url_readable"] = writers.html(self.url)
        repl["link"] = self.logURL(M)
        return repl

    def html(self, M):
        return self.html_template % self._htmlrepl(M)

    def html2(self, M):
        return self.html2_template % self._htmlrepl(M)

    def rst(self, M):
        self.rstref = self.makeRSTref(M)
        repl = self.get_replacements(M, escapewith=writers.rst)
        repl["link"] = self.logURL(M)
        # repl['url'] = writers.rst(self.url)
        return self.rst_template % repl

    def text(self, M):
        repl = self.get_replacements(M, escapewith=writers.text)
        repl["link"] = self.logURL(M)
        return self.text_template % repl

    def mw(self, M):
        repl = self.get_replacements(M, escapewith=writers.mw)
        return self.mw_template % repl
