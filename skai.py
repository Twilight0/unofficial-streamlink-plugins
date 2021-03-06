# -*- coding: utf-8 -*-
import re, json

from distutils.util import strtobool
from streamlink.plugin import Plugin, PluginArguments, PluginArgument
from streamlink.stream import HLSStream, HTTPStream
from streamlink.plugin.api.useragents import CHROME
from streamlink.plugin.api.utils import itertags


class SkaiGr(Plugin):

    _url_re = re.compile(r'https?://www\.skai(?:tv)?\.gr/(?:episode|videos|live)/?(?:\S+|\w+/[\w-]+/[\d-]+)?')
    _player_url = 'http://videostream.skai.gr/'

    arguments = PluginArguments(PluginArgument("parse_hls", default='true'))

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url)

    def _get_streams(self):

        headers = {'User-Agent': CHROME}

        res = self.session.http.get(self.url, headers=headers)

        if '/videos' not in self.url:

            json_ = re.search(r'var data = ({.+?});', res.text).group(1)

            json_ = json.loads(json_)

            if '/live' not in self.url:
                stream = ''.join([self._player_url, json_['episode'][0]['media_item_file'], '.m3u8'])
            else:
                stream = json_['now']['livestream']

        else:

            stream = [
                i for i in list(itertags(res.text, 'meta')) if 'videostream' in i.attributes.get('content', '')
            ][0].attributes.get('content')

        headers.update({"Referer": self.url})

        try:
            parse_hls = bool(strtobool(self.get_option('parse_hls')))
        except AttributeError:
            parse_hls = True

        if parse_hls:
            return HLSStream.parse_variant_playlist(self.session, stream, headers=headers)
        else:
            return dict(vod=HTTPStream(self.session, stream, headers=headers))


__plugin__ = SkaiGr
