# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging

_logger = logging.getLogger('**********demo data ************')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    automatic_merge = fields.Boolean(string="Automatically Merge Similar Manufacturing orderlines.",default=False)


    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update({
            'automatic_merge':IrDefault.get('res.config.settings','automatic_merge'), 
            'group_stock_packaging':IrDefault.get('res.config.settings','group_stock_packaging'), 
            'group_stock_tracking_lot':IrDefault.get('res.config.settings','group_stock_tracking_lot'), 
            'default_picking_policy':IrDefault.get('res.config.settings','default_picking_policy'),           
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings','automatic_merge', self.automatic_merge)
        IrDefault.set('res.config.settings','group_stock_packaging', self.group_stock_packaging )
        IrDefault.set('res.config.settings','group_stock_tracking_lot', self.group_stock_tracking_lot )
        IrDefault.set('res.config.settings','default_picking_policy', self.default_picking_policy )
        return True

    @api.model
    def action_wk_set_packaging_option(self):
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings','automatic_merge', True )
        IrDefault.set('res.config.settings','group_stock_packaging', True )
        IrDefault.set('res.config.settings','group_stock_tracking_lot', True )
        IrDefault.set('res.config.settings','default_picking_policy', 'one' )
        return True

    @api.model
    def demo_data_product(self,product_name,pack_name1,pack_name2,pack_qty1,pack_qty2,dummy_product):
        dummy = self.env['product.product'].sudo().create({
            'name':dummy_product,
        })
        rec = self.env['product.product'].sudo().create({
            'name':product_name,
            'categ_id':6,
            'standard_price':500.0,
            'list_price':750.0,
            'type':'product',
            'uom_id':1,
            'description_sale':'A dummy Packaged Product',
        })

        self.env['product.packaging'].sudo().create({
            'name':pack_name1,
            'qty':pack_qty1,
            'product_id':rec.id,
        })
        self.env['product.packaging'].sudo().create({
            'name':pack_name2,
            'qty':pack_qty2,
            'product_id':rec.id,
        })

        self.env['mrp.bom'].sudo().create({
            'product_tmpl_id':rec.product_tmpl_id.id,
            'product_qty':1.00,
            'bom_line_ids':[(0,0,{'product_id':dummy.id,})]
        })


        return True

    @api.model
    def demo_data_sale_order(self):
        rec_product=self.env['product.product'].sudo().search([('type','=','product'),('name','ilike','Test Product'),]).filtered(lambda rec:True if len(rec.packaging_ids)>0 else False)
        rec_so=self.env['sale.order'].sudo().create({
            'partner_id':10,
        })
        self.env['sale.order.line'].sudo().create({
            'product_id':rec_product[0].id,
            'name':rec_product[0].description_sale,
            'product_uom_qty':rec_product[0].packaging_ids[0].qty*2.0,
            'product_packaging_id':rec_product[0].packaging_ids[0].id,
            'order_id':rec_so.id,
        })
        self.env['sale.order.line'].sudo().create({
            'product_id':rec_product[0].id,
            'name':rec_product[0].description_sale,
            'product_uom_qty':rec_product[0].packaging_ids[1].qty*3.0,
            'product_packaging_id':rec_product[0].packaging_ids[1].id,
            'order_id':rec_so.id,
        })
        self.env['sale.order.line'].sudo().create({
            'product_id':rec_product[1].id,
            'name':rec_product[1].description_sale,
            'product_uom_qty':rec_product[1].packaging_ids[0].qty*2.0,
            'product_packaging_id':rec_product[1].packaging_ids[0].id,
            'order_id':rec_so.id,
        })
        self.env['sale.order.line'].sudo().create({
            'product_id':rec_product[1].id,
            'name':rec_product[1].description_sale,
            'product_uom_qty':rec_product[1].packaging_ids[1].qty*1.0,
            'product_packaging_id':rec_product[1].packaging_ids[1].id,
            'order_id':rec_so.id,
        })
        rec_so.action_confirm()
        

        return True






