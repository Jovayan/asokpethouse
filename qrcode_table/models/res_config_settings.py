# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    website_confirm_order_meesage = fields.Html(
        string='Website Confirm Order Message',
        translate=True,
        default=lambda s: _(
            'We are preparing your order. Please be patient, we will serve you as soon as possible.')
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_confirm_order_meesage = fields.Html(
        string='Website Confirm Order Message',
        translate=True,
        related='pos_config_id.website_confirm_order_meesage',
        readonly=False,
        default=lambda s: _(
            'We are preparing your order. Please be patient, we will serve you as soon as possible.')
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        website_confirm_order_meesage = self.env['ir.config_parameter'].sudo(
        ).get_param('qrcode_table.website_confirm_order_meesage')
        res.update(
            website_confirm_order_meesage=website_confirm_order_meesage
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'qrcode_table.website_confirm_order_meesage', self.website_confirm_order_meesage)
