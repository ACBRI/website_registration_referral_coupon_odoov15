# -*- coding: utf-8 -*-
import random
from random import randint

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo import models, fields, api

import ast


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    coupon_got=fields.Boolean(compute='get_coupon',store=True)

    @api.depends('invoice_status')
    def get_coupon(self):
        for rec in self:
            if rec.invoice_status == "invoiced":
                if not rec.coupon_got:
                    ircsudo = self.env['ir.config_parameter'].sudo()
                    old_partner_coupon_rule_id = int(ircsudo.get_param(
                        'website_registration_referral_coupon.old_partner_coupon_rule_id'))
                    rec.partner_id.generate_coupon(coupon_rule_id=old_partner_coupon_rule_id, partner_id=rec.partner_id.referred_by,referred_by=rec.partner_id)
                    rec.coupon_got=True
            else:
                rec.coupon_got=False


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    refer_partner = fields.Char(string='Reference Code')
    refer_url = fields.Char(string='Reference URL',compute='get_shareable_url')
    referred_by = fields.Many2one('res.partner')
    is_first_login = fields.Boolean(default=True)

    def first_login(self):
        self.sudo().is_first_login =False

    @api.depends('refer_partner')
    def get_shareable_url(self):
        for rec in self:
            if rec.refer_partner:
                token = 'pr=' +rec.refer_partner
                rec.refer_url = rec.get_base_url() + '/web/signup?' + token
            else:
                rec.refer_url = ''

    @api.model
    def create(self, vals):
        res = super(InheritResPartner, self).create(vals)
        res.refer_partner = res.generate_referral()
        return res

    @api.model
    def assign_referral_code(self):
        partner_ids=self.env['res.partner'].search([('refer_partner','=',False)])
        for partner_id in partner_ids:
            partner_id.refer_partner=partner_id.generate_referral()

    def generate_referral(self):
        sm_alfa = 'abcdefghijklmnopqrstuvwxyz'
        cp_alfa = sm_alfa.upper()
        num = '0987654321'
        ref_str = ''
        for item in range(8):
            choose = random.choice(['sm_alfa', 'cp_alfa', 'num'])
            if choose == 'cp_alfa':
                ref_str += cp_alfa[randint(0, len(cp_alfa) - 1)]
            elif choose == 'num':
                ref_str += num[randint(0, len(num) - 1)]
            elif choose == 'sm_alfa':
                ref_str += sm_alfa[randint(0, len(sm_alfa) - 1)]
        partner = self.env['res.partner'].search([('refer_partner', '=', ref_str)])
        if partner:
            self.generate_referral()
        gen_for_me=self.env.context.get('gen_for_me', False)
        if gen_for_me:
            self.refer_partner = ref_str
        return ref_str

    def generate_coupon(self,coupon_rule_id=None,partner_id=None,referred_by=None):
        coupon_rule_id = self.env['coupon.program'].search([('id','=',coupon_rule_id)])
        self.env['coupon.generate.wizard'].with_context(active_id=coupon_rule_id.id).create({
            'generation_type': 'nbr_customer',
            'partners_domain': "[('id', 'in', [%s])]" % (partner_id.id),
            'referred_by':referred_by.id if referred_by else False,
        }).generate_coupon()


class InheritCouponCoupon(models.Model):
    _inherit ='coupon.coupon'

    referred_by = fields.Many2one('res.partner')


#
class InheritCouponGenerate(models.TransientModel):
    _inherit = 'coupon.generate.wizard'
    referred_by = fields.Many2one('res.partner')

    def generate_coupon(self):
        """Generates the number of coupons entered in wizard field nbr_coupons
        """
        program = self.env['coupon.program'].browse(self.env.context.get('active_id'))

        vals = {'program_id': program.id}
        if self.referred_by:
            vals.update(referred_by=self.referred_by.id)

        if self.generation_type == 'nbr_coupon' and self.nbr_coupons > 0:
            for count in range(0, self.nbr_coupons):
                self.env['coupon.coupon'].create(vals)

        if self.generation_type == 'nbr_customer' and self.partners_domain:
            for partner in self.env['res.partner'].search(ast.literal_eval(self.partners_domain)):
                vals.update({'partner_id': partner.id, 'state': 'sent' if partner.email else 'new'})
                coupon = self.env['coupon.coupon'].create(vals)
                subject = '%s, a coupon has been generated for you' % (partner.name)
                if self.referred_by:
                    subject+=' by referral code program'

                template = self.env.ref('website_registration_referral_coupon.mail_template_sale_coupon', raise_if_not_found=False)
                if template:
                    email_values = {'email_to': partner.email, 'email_from': self.env.user.email or '', 'subject': subject}
                    template.send_mail(coupon.id, email_values=email_values, notif_layout='mail.mail_notification_light')



class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    program_active = fields.Boolean()
    old_partner_coupon_rule_id = fields.Many2one('coupon.program',domain=[('program_type','=', 'coupon_program')])
    new_partner_coupon_rule_id = fields.Many2one('coupon.program',domain=[('program_type','=', 'coupon_program')])
    not_immediate_get_referring_partner = fields.Boolean()

    def coupon_program_send_mail(self):
        template_id = self.env.ref('website_registration_referral_coupon.email_template_coupon_program_notification').id
        template = self.env['mail.template'].browse(template_id)
        partners = self.env['res.partner'].search([])
        if partners:
            email_values = {'recipient_ids': partners.ids}
            template.browse(template_id).send_mail(self.env.user.id, force_send=True, email_values=email_values)

    def set_values(self):
        res = super(InheritResConfigSettings, self).set_values()

        self.env['ir.config_parameter'].set_param('website_registration_referral_coupon.program_active',
                                                          self.program_active)
        self.env['ir.config_parameter'].set_param('website_registration_referral_coupon.old_partner_coupon_rule_id',
                                                  self.old_partner_coupon_rule_id.id)
        self.env['ir.config_parameter'].set_param('website_registration_referral_coupon.new_partner_coupon_rule_id',
                                                          self.new_partner_coupon_rule_id.id)
        self.env['ir.config_parameter'].set_param('website_registration_referral_coupon.not_immediate_get_referring_partner',
                                                  self.not_immediate_get_referring_partner)
        return res

    @api.model
    def get_values(self):
        res = super(InheritResConfigSettings, self).get_values()
        ircsudo = self.env['ir.config_parameter'].sudo()
        program_active = ircsudo.get_param('website_registration_referral_coupon.program_active')
        old_partner_coupon_rule_id = ircsudo.get_param('website_registration_referral_coupon.old_partner_coupon_rule_id')
        new_partner_coupon_rule_id = ircsudo.get_param('website_registration_referral_coupon.new_partner_coupon_rule_id')
        not_immediate_get_referring_partner = ircsudo.get_param(
            'website_registration_referral_coupon.not_immediate_get_referring_partner')
        res.update(
            program_active=bool(program_active) if program_active else False,
            old_partner_coupon_rule_id=int(old_partner_coupon_rule_id) if old_partner_coupon_rule_id else 0,
            new_partner_coupon_rule_id=int(new_partner_coupon_rule_id) if new_partner_coupon_rule_id else 0,
            not_immediate_get_referring_partner=bool(
                not_immediate_get_referring_partner) if not_immediate_get_referring_partner else False,
        )
        return res
