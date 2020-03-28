# -*- coding: utf-8 -*-
import re

from streamlink.plugin import Plugin, PluginError
from streamlink.stream import HTTPStream
from streamlink.plugin.api.useragents import CHROME
from streamlink.plugin.api.utils import itertags


class Clipwatching(Plugin):

    _url_re = re.compile(r'https?://clipwatching\.com/(?:embed-)?\w+(?:\.html)?')

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url)

    def _get_streams(self):

        headers = {'User-Agent': CHROME}

        res = self.session.http.get(self.url, headers=headers)

        try:
            script = [i for i in list(itertags(res.text, 'script')) if 'v.mp4' in i.text][0].text

            stream = re.search(r'(http.+?v\.mp4)', script).group(1)

            headers.update({"Referer": self.url})

            return dict(vod=HTTPStream(self.session, stream, headers=headers))

        except Exception:

            raise PluginError('Couldnt find stream')


__plugin__ = Clipwatching
