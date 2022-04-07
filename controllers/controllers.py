# -*- coding: utf-8 -*-
from werkzeug.utils import redirect
from odoo import http, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import logging
import json
from odoo.http import request

_logger = logging.getLogger(__name__)


class InheritAuthSignupHome(AuthSignupHome):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        res = super(InheritAuthSignupHome, self).web_auth_signup(*args, **kw)
        partner = http.request.env['res.partner'].sudo().search([('refer_partner', '=', kw.get('refer_partner'))])
        new_partner = http.request.env['res.partner'].sudo().search([('email', '=', kw.get('login'))])
        if partner and len(partner) == 1:
            if new_partner and len(new_partner) == 1:
                ircsudo = http.request.env['ir.config_parameter'].sudo()
                not_immediate_get_referring_partner = ircsudo.get_param(
                    'website_registration_referral_coupon.not_immediate_get_referring_partner')
                old_partner_coupon_rule_id = int(ircsudo.get_param(
                    'website_registration_referral_coupon.old_partner_coupon_rule_id'))
                new_partner_coupon_rule_id = int(ircsudo.get_param(
                    'website_registration_referral_coupon.new_partner_coupon_rule_id'))
                if bool(not_immediate_get_referring_partner):
                    new_partner.referred_by = partner.id
                else:
                    new_partner.generate_coupon(coupon_rule_id=old_partner_coupon_rule_id, partner_id=partner,
                                                referred_by=new_partner)
                new_partner.generate_coupon(coupon_rule_id=new_partner_coupon_rule_id, partner_id=new_partner)
        return res

    @http.route("/check/partner/referral_code", type='http', auth="public", website=True)
    def check_vendor_profile(self, referral_code):
        if referral_code:
            res = request.env["res.partner"].sudo().search([("refer_partner", "=", referral_code)])
            if res:
                return "is-valid"
            else:
                return "is-invalid"


class ReferralCoupon(http.Controller):
    @http.route(['/my/ref-coupons', '/my/ref-coupons/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_coupons(self, page=1, **kw):
        values = {}
        _items_per_page = 10
        partner = request.env.user.partner_id
        coupon_ids = http.request.env['coupon.coupon'].sudo().search([('partner_id', '=', partner.id)], )
        pager = portal_pager(
            url="/my/ref-coupons",
            url_args={},
            total=len(coupon_ids),
            page=page,
            step=_items_per_page
        )
        coupon_ids = http.request.env['coupon.coupon'].sudo().search(
            [('partner_id', '=', http.request.env.user.partner_id.id)],
            order='id desc',
            limit=_items_per_page, offset=pager['offset'])
        values.update({
            'coupon_ids': coupon_ids,
            'page_name': 'Coupons',
            'pager': pager,
            'default_url': '/my/ref-coupons',
        })
        return http.request.render("website_registration_referral_coupon.portal_my_coupons", values)

    @http.route('/edit-referral-code', type='http', auth='user', website=True, sitemap=False, csrf=False)
    def edit_referral_code(self, **kw):
        partner_id = request.env['res.users'].sudo().search([('id', '=', request.env.uid)]).partner_id
        ref_code = kw.get('reg_ref_code')
        if ref_code:
            partner_id.refer_partner = ref_code
        return redirect('/my/home')

    @http.route('/ref_code_availability', auth="user", type='http', website=True, csrf=False)
    def ref_code_availability(self, **kw):
        res_dict = {}
        ref_code = kw.get('ref_code')
        resp = self.check_ref_code(ref_code)
        if not resp:
            msg = 'Referral Code is not acceptable.'
            if 'code_length' in resp.keys():
                msg += 'Code length must be 8 character.'
            if 'special_char' in resp.keys():
                msg += "Only alphanumeric acceptable. Some special character found in code '%s'." % ', '.join(
                    resp.get('special_char'))
            res_dict.update({
                'msg': msg,
                'classes': 'alert alert-danger',
            })
        else:
            if request.env['res.partner'].sudo().search([('refer_partner', '=', ref_code)]):
                res_dict.update({
                    'msg': 'Referral Code is not available. Choose another.',
                    'classes': 'alert alert-warning',
                })
            else:
                res_dict.update({
                    'msg': 'Referral Code is available',
                    'classes': 'alert alert-success',
                    'available': True,
                })
        return json.dumps(res_dict)

    def check_ref_code(self, ref_code):
        res = {}
        if len(ref_code) != 8:
            res.update({'code_length': len(ref_code)})
        sm_alfa = 'abcdefghijklmnopqrstuvwxyz'
        cp_alfa = sm_alfa.upper()
        num = '0987654321'
        alfa_num = sm_alfa + cp_alfa + num
        no_alfa_num = []
        for char in ref_code:
            if char not in alfa_num:
                if char == ' ':
                    no_alfa_num.append('_blank')
                else:
                    no_alfa_num.append(char)
        if no_alfa_num:
            res.update({'special_char': no_alfa_num})
        if res.keys():
            return res
        else:
            return True


class InheritCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        coupon_ids = http.request.env['coupon.coupon'].sudo()
        if 'coupon_count' in counters:
            values['coupon_count'] = coupon_ids.search_count(
                [('partner_id', '=', partner.id)])
        return values
