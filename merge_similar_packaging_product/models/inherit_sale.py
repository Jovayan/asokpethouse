#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    line_merge_description = fields.Html(string='Order Line Merge Description')

    def _sanity_check(self, product_with_packages):
        productObj = self.env['product.product']  
        for key in product_with_packages:     
            product_id = productObj.browse(key)
            product_packaging_ids = self.env['product.packaging'].search(['&',('product_id','=', product_id.id),('sales','=',True)])                                   
            product_packaging_ids_qty = product_packaging_ids.mapped('qty')
            product_packaging_ids_qty.sort(reverse=True)
            len_product_packaging_ids_qty = len(product_packaging_ids_qty)

            computed_line_qty = product_with_packages[key][1]
            
            index, future_line_qty = 0, []
            
            while computed_line_qty > 0 and index < len_product_packaging_ids_qty:
                if computed_line_qty >= product_packaging_ids_qty[index]:                   
                    future_line_qty.append(computed_line_qty//product_packaging_ids_qty[index] * product_packaging_ids_qty[index])  
                    computed_line_qty %= product_packaging_ids_qty[index]
                index += 1
            if computed_line_qty > 0:
                future_line_qty.append(computed_line_qty)                
            product_with_packages[key][2] = future_line_qty
        return product_with_packages

    def action_confirm(self):
        try:
            automatic_merger = self.env['res.config.settings'].sudo().get_values()['automatic_merge']
           
            if automatic_merger:
                product_with_packages = {}
                non_pack_lines = self.env['sale.order.line']             
                lines_to_unlink = self.env['sale.order.line']
                line_to_assign = self.env['sale.order.line']

                html_data = '''<table class="table">
                        <thead>
                                <tr>
                                    <th>Product Name</th>
                                    <th>Product Description</th>
                                    <th>Quantity</th>
                                    <th>Unit pack</th>
                                    <th>Package to be delivered</th>
                                    <th>Subtotal</th>
                                </tr>
                        </thead>
                        <tbody>
                    '''
                raw_data, old_lines_qty_dict = '', {}
                for line in self.order_line:
                    if line.product_id.packaging_ids:
                        if line.product_id.id in old_lines_qty_dict:
                            old_lines_qty_dict[line.product_id.id].append(line.product_uom_qty)
                        else:
                            old_lines_qty_dict.update({line.product_id.id: [line.product_uom_qty]})
                        raw_data += \
                            "<tr>\
                                <td>"+line.product_id.name+"</td>\
                                <td>"+line.name+"</td>\
                                <td>"+str(line.product_uom_qty)+"</td>\
                                <td>"+str((line.product_packaging_id.name) if line.product_packaging_id else "Pack of 1")+"</td>\
                                <td>"+str( (line.product_packaging_qty) if line.product_packaging_qty else int(line.product_uom_qty*1))+" Packages</td>\
                                <td>"+str(line.price_subtotal)+"</td>\
                            </tr>"     

                for line in self.order_line:
                    if line.product_id.packaging_ids.ids:
                        lines_to_unlink |= line
                        if line.product_id.id in product_with_packages:
                            product_with_packages[line.product_id.id][1] += line.product_uom_qty
                        else:
                            product_with_packages.update({line.product_id.id: [line.product_id.uom_id.id, line.product_uom_qty, 0]})
                    else:
                        non_pack_lines |= line

                product_with_packages = self._sanity_check(product_with_packages)

                for product_id in product_with_packages:
                    new_qty_to_update = product_with_packages[product_id][2]                    
                    old_line_qty = old_lines_qty_dict[product_id]                  
                    new_qty_to_update.sort()
                    old_line_qty.sort()
                    check_equal = [i for i, j in zip(new_qty_to_update, old_line_qty) if i != j]
                    if len(check_equal) == 0:
                        non_pack_lines |= lines_to_unlink.filtered(lambda line: line.product_id.id == product_id)
                        lines_to_unlink = lines_to_unlink.filtered(lambda line: line.product_id.id != product_id)
                        continue

                    for qty in new_qty_to_update:
                        vals = {
                            'order_id': self.id,
                            'product_id': product_id,
                            'product_uom_qty': qty,
                            'product_uom': product_with_packages[product_id][0]
                        }
                        sale_line_id = self.env['sale.order.line'].sudo().create(vals)
                        sale_line_id._onchange_product_id_warning()
                        line_to_assign |= sale_line_id
                
                line_to_assign |= non_pack_lines
                lines_to_unlink.unlink()

        except Exception as e:
            _logger.info('merge_similar_packaging_product == > {}'.format(e))

        return super(SaleOrder,self).action_confirm()
    





class Picking(models.Model):
    _inherit = 'stock.picking'

     
    description =fields.Html(string='Description',compute="_compute_description")


    def _compute_description(self):
        html_data = '''<table class="table">
                        <thead>
                                <tr>
                                    <th>Product Name</th>
                                    <th>Product Description</th>
                                    <th>Quantity</th>
                                    <th>Unit pack</th>
                                    <th>Package to be delivered</th>
                                    <th>Subtotal</th>
                                </tr>
                        </thead>
                        <tbody>
                                            
                                            '''
        raw_data=""
        for line in self.sale_id.order_line:
            raw_data += \
                "<tr>\
                    <td>"+line.product_template_id.name+"</td>\
                    <td>"+str((line.name) if line.name else line.product_template_id.name)+"</td>\
                    <td>"+str(line.product_uom_qty)+"</td>\
                    <td>"+str((line.product_packaging_id.name) if line.product_packaging_id else "Pack of 1")+"</td>\
                    <td>"+str(int(line.product_packaging_qty)  if line.product_packaging_qty else int(line.product_uom_qty/1.0))+" Packages</td>\
                    <td>"+self.sale_id.pricelist_id.currency_id.symbol+" "+str(line.price_subtotal)+"</td>\
                </tr>"
        self.description  = html_data+raw_data+"</tbody></table>"
            

            
                
        

