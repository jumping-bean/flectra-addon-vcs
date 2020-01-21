import logging
import pprint
import werkzeug
from werkzeug.urls import url_unquote_plus

from flectra import http
from flectra.http import request
from flectra.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class VCSWebController(http.Controller):
    @http.route([
        "/payment/vcsweb/approved",
        "/payment/vcsweb/declined",
    ], type='http', auth='none',csrf=False)
    def vcsweb_form_feedback(self, **post):
        _logger.info('VCSWeb: entering form_feedback with post data %s', pprint.pformat(post))  
        request.env['payment.transaction'].sudo().form_feedback(post, 'vcsweb')
        return werkzeug.utils.redirect(url_unquote_plus(post.pop('m_1', '/')))

    @http.route([
        "/payment/vcsweb/cancelled"
    ], type='http', auth='none',csrf=False)
    def vcsweb_form_cancelled(self,**post):
        _logger.info('VCSWeb: payment cancelled. entering form_feedback with post data %s', pprint.pformat(post)) 
        post["p3"]="CANCELLED"
        request.env['payment.transaction'].sudo().form_feedback(post, 'vcsweb')
        return werkzeug.utils.redirect(url_unquote_plus(post.pop('m_1', '/')))

    #optional callback interface host to host payment feedback
    @http.route([
        "/payment/vcsweb/callback"
    ],type='http', auth='none',csrf=False)
    def vcsweb_host_callback(self,**post):
        _logger.info('VCSWeb: entering  callback feedback with post data %s', pprint.pformat(post))  
        request.env['payment.transaction'].sudo().form_feedback(post, 'vcsweb')
        return "<CallbackResponse>Accepted</CallbackResponse>"