odoo.define('qrcode_table.models', function(require) {
    "use strict";

    const { Order, Orderline } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const QrcodeTableOrder = (Order) => class QrcodeTableOrder extends Order {
        constructor(obj, options) {
            super(...arguments);
            if (options.json && options.json.token) {
                this.is_table_order = options.json.is_table_order;
                this.token = options.json.token;
            } else {
                this.is_table_order = false;
                this.token = false;
            }
        }
        set_orderline_options(orderline, options) {
            super.set_orderline_options(...arguments);
            if (options.table_order_line_id !== undefined) {
                orderline.set_table_order_line_id(options.table_order_line_id);
            }
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
            json['is_table_order'] = this.get_is_table_order();
            json['token'] = this.get_token_table();
            return json;
        }
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.token = json.token;
        }
        export_for_printing() {
            const json = super.export_for_printing(...arguments);
            if (this.pos.config.module_pos_restaurant) {
                if (this.pos.config.iface_floorplan) {
                    json.table = this.getTable().name;
                    const hasMinimumSpendingProduct = this.orderlines.some(line => {
                        const productName = line.product.display_name;
                        return productName && productName.toLowerCase().includes("minimum spending");
                    });
                    if (hasMinimumSpendingProduct) {
                        json.qr_image = this.getTable().qr_image;
                    }
                }
                json.customer_count = this.getCustomerCount();
            }
            return json;
        }
    }
    Registries.Model.extend(Order, QrcodeTableOrder);

    const QrcodeTableOrderLine = (Orderline) => class QrcodeTableOrderLine extends Orderline {
        constructor(obj, options) {
            super(...arguments);
            if (options.json && options.json.table_order_line_id) {
                this.table_order_line_id = options.json.table_order_line_id;
            } else {
                this.table_order_line_id = this.table_order_line_id || 0;
            }

        }
        set_table_order_line_id(table_order_line_id) {
            this.table_order_line_id = table_order_line_id;
        }
        get_table_order_line_id() {
            return this.table_order_line_id;
        }
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json['table_order_line_id'] = this.get_table_order_line_id();
            return json;
        }
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.table_order_line_id = json.table_order_line_id;
        }
        clone() {
            var line = super.clone(...arguments);
            line.table_order_line_id = this.table_order_line_id;
            return line;
        }
    }
    Registries.Model.extend(Orderline, QrcodeTableOrderLine);
});