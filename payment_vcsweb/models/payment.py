# -*- coding: utf-8 -*-

from flectra import models, fields, api
import hashlib 
from werkzeug import urls
import logging
from flectra import api, fields, models, _
from flectra.addons.payment.models.payment_acquirer import ValidationError
from flectra.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

class AcquirerVCSWeb(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('vcsweb', 'VCSWeb')])
    vcsweb_md5_secret = fields.Char('Shared MD5 Secret',help="Optional shared secret for use in hash token", required_if_provider='vcsweb', groups='base.group_user')
    vcsweb_terminal_id = fields.Char('Terminal ID', help="Your VCS terminal id", required_if_provider='vcsweb', groups='base.group_user')
    vcsweb_personal_authentication_message = fields.Char("PAM",help="Your Personal Authentication Message",required_if_provider='vcsweb', groups='base.group_user')
    _approved_url="/payment/vcsweb/approved"
    _declined_url="/payment/vcsweb/declined"
    _cancelled_url="/payment/vcsweb/cancelled"

    def _calculate_vcsweb_hash(self,inout,values):

        if inout not in ('in', 'out'):
            raise Exception("Type must be 'in' or 'out'")

        if inout == "out":
            params=values["terminal_id"]+values["tx_reference_no"]+values["tx_description"]+values["tx_amount"]+values["tx_currency"]
            params+=values["cancelled_url"]+values['customer_email'] +values["return_url"]+ values["customer_id"]
            params+=self.vcsweb_md5_secret
        else:
            keys = ['p1','p2','p3','p4','p5','p6','p7','p8','p9','p10','p11','p12',"pam","m_1","CardHolderIpAddr","CardholderIpAddr","MaskedCardNumber","TransactionType","CustomerID",'MerchantToken']
            params = ''
            for key in keys:
                if key == "pam":
                    params=params+self.vcsweb_personal_authentication_message
                elif key in values:
                    params = params + values[key]
            params= params + self.vcsweb_md5_secret
        return hashlib.md5(params.encode()).hexdigest()


    def _get_vcsweb_urls(self):
        return {
            'vcsweb_form_url': 'https://www.vcs.co.za/vvonline/vcspay.aspx',
        }   

    @api.multi
    def vcsweb_form_generate_values(self, values):
        #Should get url dynamically but doesn't appear to work for multi-site
        #base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url = "https://cyberconnect.shop"
        #base_url="http://35.200.126.168:7073"
        values.update({
            'tx_reference_no': values['reference'],
            'tx_amount': '%.2f' % values['amount'],
            'tx_description': "Goods from Cyber Connect",
            'tx_currency': 'ZAR',
            'terminal_id': self.vcsweb_terminal_id,
            'urls_provided': 'Y',
            'approved_url': urls.url_join(base_url, self._approved_url),
            'declined_url': urls.url_join(base_url, self._declined_url),
            'cancelled_url': urls.url_join(base_url, self._cancelled_url),
            'customer_id': "%d" % values.get('partner_id',""),
            'customer_email': values.get('partner_email', ''),
            'customer_name': values.get('partner_name', ''),
            'return_url': values.get("return_url"),
        }) 
        values['tx_hash'] = self._calculate_vcsweb_hash("out",values)
        return values

    @api.multi
    def vcsweb_get_form_action_url(self):
        return self._get_vcsweb_urls()['vcsweb_form_url']

class TxVCSWeb(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _vcsweb_form_get_tx_from_data(self, data):
        #if controller is called directly.
        reference = data.get('p2');
        if not reference:
            error_msg = _('VCSWeb: no transactional reference received') 
            raise ValidationError(error_msg)
        tx = self.search([("reference","=",reference)])
        #did we find the transaction?
        if not tx:
            error_msg = _('VCSWeb: received data for reference %s; no order found') % (reference)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = _('VCSWeb: received data for reference %s; multiple orders found') % (reference)
            raise ValidationError(error_msg)
        #check hash - just redisplay transaction
        if data.get("p3","") == '~MD5 Hash mismatch':
            _logger.info("acquirer found hash mismatch on input data")
            return tx
        hash = data.get("Hash",None)
        if hash:
            calculated_hash = tx.acquirer_id._calculate_vcsweb_hash('in', data)
            if hash.upper() != calculated_hash.upper():
                error_msg = _('VCSWeb: invalid hash, received %s, computed %s, for data %s') % (hash, calculated_hash, data)
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        return tx

    def _vcsweb_form_validate(self, data):
        status = data.get('p3', 'CANCELLED')
            
        if "APPROVED" in status:
            self.write({
                'state': 'done',
                'state_message': status,
                'acquirer_reference': data.get('Uti'),
            })
            return True
        elif "CANCELLED" in status:
            self.write({
                'state': 'cancel',
                'state_message': status,
                #'acquirer_reference': data.get('Uti'),
            })
            #return True
        else:
            self.write({
                'state': 'error',
                'state_message': status,
                'acquirer_reference': data.get('Uti'),
            })
            return False
        


    def _vcsweb_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        #don't know why we would already have the acquirer reference but all the built in 
        #addons do this test so just following tradition.
        if self.acquirer_reference and data.get('Uti') != self.acquirer_reference:
            invalid_parameters.append(('Uti', data.get('Uti'), self.acquirer_reference))

        #check if the reference we sent is what we get back
        if self.reference != data.get("p2"):
            invalid_parameters.append(('p2', data.get('p2'), self.acquirer_reference))\

        #other tests CustomerID?

        #another common check
        if 'p6' in data and  float_compare(float(data['p6']), self.amount, 2) != 0:
            invalid_parameters.append(
                ('Amount', data.get('p6'), '%.2f' % self.amount))

        return invalid_parameters
