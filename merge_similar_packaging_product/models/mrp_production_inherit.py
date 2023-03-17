# If not, see <https://store.webkul.com/license.html/>
##########################################################################

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from functools import reduce

import logging
_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    description_mrp = fields.Html(string='Description',compute="_compute_description_mrp")

    def _compute_description_mrp(self):
        for line in self.env['sale.order'].sudo().search([('name','=',self.origin)], limit=1).order_line.filtered(lambda line: True if line.product_id.id ==self.product_id.id else False):

            line.name
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
        raw_data = ""
        for line in self.env['sale.order'].sudo().search([('name','=',self.origin)], limit=1).order_line.filtered(lambda line: True if line.product_id.id ==self.product_id.id else False):
            raw_data += "\
                <tr>\
                    <td>"+line.product_id.name+"</td>\
                    <td>"+line.name+"</td>\
                    <td>"+str(line.product_uom_qty)+"</td>\
                    <td>"+str((line.product_packaging_id.name) if line.product_packaging_id else "Pack of 1")+"</td>\
                    <td>"+str( (line.product_packaging_qty) if line.product_packaging_qty else int(line.product_uom_qty*1))+" Packages</td>\
                    <td>"+str(line.price_subtotal)+"</td>\
                </tr>"
            

        self.description_mrp=html_data+raw_data+"</tbody></table>"

        
        

    def action_merge_mo(self):
        self = self.filtered(lambda rec: True if rec.origin else False)
        filtered_record = {rec.product_id.name+' '+rec.origin:[self.search([('product_id','=',rec.product_id.id),('origin','=',rec.origin),('state','=','confirmed')])] for rec in self}
        
        temp=dict()
        for key,value in filtered_record.items():
            if len(value[0])>1:
                temp[key]=value
        for key,value in temp.items():
            product_qty=0
            for val in value[0]:
                val_create={
                    'origin': val.origin,
                    'product_id': val.product_id.id,
                    'product_uom_id': val.product_uom_id.id,
                    'location_src_id': val.location_src_id.id or val.picking_type_id.default_location_src_id.id,
                    'location_dest_id': val.location_dest_id.id,
                    'bom_id': val.bom_id.id,
                    'date_deadline': val.date_deadline,
                    'date_planned_finished': val.date_planned_finished,
                    'date_planned_start': val.date_planned_start,
                    'procurement_group_id': val.procurement_group_id.id,
                    'propagate_cancel': val.propagate_cancel,
                    'orderpoint_id': val.orderpoint_id.id,
                    'picking_type_id': val.picking_type_id.id,
                    'company_id': val.company_id.id,
                    'move_dest_ids': val.move_dest_ids,
                    'user_id': False,
                    'state':val.state,
                    'reservation_state':val.reservation_state,
                }
                product_qty += val.product_qty
                val.action_cancel()
            val_create.update({'product_qty': product_qty})           
            production=val.env['mrp.production'].sudo().create(val_create)
            self.env['stock.move'].sudo().create(production._get_moves_raw_values())
            self.env['stock.move'].sudo().create(production._get_moves_finished_values())
            production._create_workorder()
            production.filtered(lambda p: not p.orderpoint_id).action_confirm()
            production.action_confirm()

    
