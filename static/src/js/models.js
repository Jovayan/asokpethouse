odoo.define('qrcode_table.models', function(require) {
    "use strict";

    const { Order, Orderline } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const QrcodeTableOrder = (Order) => class QrcodeTableOrder extends Order {
        constructor(obj, options) {
            super(...arguments);
            this.is_table_order = false;
            this.token = false;
        }
        set_is_table_order(is_table_order) {
            this.is_table_order = is_table_order;
        }
        get_is_table_order() {
            return this.is_table_order;
        }
        set_token_table(token) {
            this.token = token;
        }
        get_token_table() {
            return this.token;
        }
        get_line_all_ready_exit(line_id) {
            var self = this;
            var orderlines = self.orderlines;
            var flag = false;
            _.each(orderlines, function(line) {
                if (line_id == line.table_order_line_id) {
                    flag = true;
                }
            });
            return flag;
        }
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.is_table_order = this.get_is_table_order();
            json.token = this.get_token_table();
            return json;
        }
    }
    Registries.Model.extend(Order, QrcodeTableOrder);

    const QrcodeTableOrderLine = (Orderline) => class QrcodeTableOrderLine extends Orderline {
        constructor(obj, options) {
            super(...arguments);
            this.table_order_line_id = false;
        }
        set_table_order_line_id(table_order_line_id) {
            this.table_order_line_id = table_order_line_id;
        }
        get_table_order_line_id() {
            return this.table_order_line_id;
        }
    }
    Registries.Model.extend(Orderline, QrcodeTableOrderLine);
});