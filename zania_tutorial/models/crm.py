from odoo import fields, models, api
from odoo.addons.website.tools import get_video_embed_code
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import contextlib
import re
from unittest.mock import Mock, MagicMock, patch
import werkzeug
import odoo
from odoo.tools.misc import DotDict


class ModelName(models.Model):
    _name = 'crm.tutorial'
    _description = 'Description'

    name = fields.Text()
    video_url = fields.Char('Video URL', help='URL of a video for showcasing your product.')
    embed_code = fields.Char(compute="_compute_embed_code")


    @api.depends('video_url')
    def _compute_embed_code(self):
        for image in self:
            image.embed_code = get_video_embed_code(image.video_url)

    def get_video_embed_code(video_url):
        ''' Computes the valid iframe from given URL that can be embedded
            (or False in case of invalid URL).
        '''

        if not video_url:
            return False

        # To detect if we have a valid URL or not
        validURLRegex = r'^(http:\/\/|https:\/\/|\/\/)[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$'

        # Regex for few of the widely used video hosting services
        ytRegex = r'^(?:(?:https?:)?\/\/)?(?:www\.)?(?:youtu\.be\/|youtube(-nocookie)?\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((?:\w|-){11})(?:\S+)?$'
        vimeoRegex = r'\/\/(player.)?vimeo.com\/([a-z]*\/)*([0-9]{6,11})[?]?.*'
        dmRegex = r'.+dailymotion.com\/(video|hub|embed)\/([^_?]+)[^#]*(#video=([^_&]+))?'
        igRegex = r'(.*)instagram.com\/p\/(.[a-zA-Z0-9]*)'
        ykuRegex = r'(.*).youku\.com\/(v_show\/id_|embed\/)(.+)'

        if not re.search(validURLRegex, video_url):
            return False
        else:
            embedUrl = False
            ytMatch = re.search(ytRegex, video_url)
            vimeoMatch = re.search(vimeoRegex, video_url)
            dmMatch = re.search(dmRegex, video_url)
            igMatch = re.search(igRegex, video_url)
            ykuMatch = re.search(ykuRegex, video_url)

            if ytMatch and len(ytMatch.groups()[1]) == 11:
                embedUrl = '//www.youtube%s.com/embed/%s' % (ytMatch.groups()[0] or '', ytMatch.groups()[1])
            elif vimeoMatch:
                embedUrl = '//player.vimeo.com/video/%s' % (vimeoMatch.groups()[2])
            elif dmMatch:
                embedUrl = '//www.dailymotion.com/embed/video/%s' % (dmMatch.groups()[1])
            elif igMatch:
                embedUrl = '//www.instagram.com/p/%s/embed/' % (igMatch.groups()[1])
            elif ykuMatch:
                ykuLink = ykuMatch.groups()[2]
                if '.html?' in ykuLink:
                    ykuLink = ykuLink.split('.html?')[0]
                embedUrl = '//player.youku.com/embed/%s' % (ykuLink)
            else:
                # We directly use the provided URL as it is
                embedUrl = video_url
            return '<iframe width="560" height="315"  src="https:%s" title="YouTube video player" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"  allowFullScreen="true" frameborder="0"></iframe>' % embedUrl
