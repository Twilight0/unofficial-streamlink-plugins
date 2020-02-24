# -*- coding: utf-8 -*-
import re

from distutils.util import strtobool
from streamlink.plugin import Plugin, PluginArguments, PluginArgument
from streamlink.compat import parse_qsl, urlparse
from streamlink.stream import HLSStream, HTTPStream
from streamlink.plugin.api.useragents import CHROME
from streamlink.plugin.api.utils import itertags
from streamlink.exceptions import NoStreamsError


class Ant1Cy(Plugin):

    _url_re = re.compile(r'https?://w{3}\.ant1\.com\.cy/(?:web-tv-live|webtv/show-page/(?:episodes|episodeinner)/\?(?:show|showID)=\d+&episodeID=\d+)/?')

    _api_url = 'https://www.ant1.com.cy/ajax.aspx?m=Atcom.Sites.Ant1iwo.Modules.TokenGenerator&videoURL={0}'

    arguments = PluginArguments(PluginArgument("parse_hls", default='true'))

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url)

    def _get_streams(self):

        headers = {'User-Agent': CHROME}

        if 'web-tv-live' in self.url:
            live = True
        else:
            live = False
            self.url = self.url.replace('episodeinner', 'episodes').replace('showID', 'show')

        res = self.session.http.get(self.url, headers=headers)

        if live:

            tags = list(itertags(res.text, 'script'))

            tag = [i for i in tags if 'm3u8' in i.text][0].text

            m3u8 = re.search(r'''["'](http.+?\.m3u8)['"]''', tag)

            if m3u8:
                m3u8 = m3u8.group(1)
            else:
                raise NoStreamsError('Ant1 CY Broadcast is currently disabled')

        else:

            eid = dict(parse_qsl(urlparse(self.url).query))['episodeID']

            tags = [i for i in list(itertags(res.text, 'a')) if eid in i.attributes.get('data-innerurl', '')]

            tag = tags[0].attributes.get('data-video')

            m3u8 = re.search(r"&quot;(http.+?master\.m3u8)&quot;", tag).group(1)

        stream = self.session.http.get(self._api_url.format(m3u8), headers=headers).text

        headers.update({"Referer": self.url})

        try:
            parse_hls = bool(strtobool(self.get_option('parse_hls')))
        except AttributeError:
            parse_hls = True

        if parse_hls:
            return HLSStream.parse_variant_playlist(self.session, stream, headers=headers)
        else:
            return dict(stream=HTTPStream(self.session, stream, headers=headers))


__plugin__ = Ant1Cy
