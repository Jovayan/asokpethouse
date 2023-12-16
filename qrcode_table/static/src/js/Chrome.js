odoo.define('qrcode_table.Chrome', function(require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    const PosTableChrome = (Chrome) =>
        class extends Chrome {
            /**
             * @override
             */
            async start() {
                await super.start();
                this.env.services.bus_service.addChannel('table.order');
                this.env.services.bus_service.addEventListener('notification', this._onNotification.bind(this));
            }
            async _onNotification({ detail: notifications }) {
                for (var notif of notifications) {
                    if (notif.type == 'table.order' && notif.payload['table_order_display'] != undefined) {
                        var user_id = notif.payload;
                        var n = new Noty({
                            theme: 'light',
                            text: notif.payload.table_order_display.table_order_message,
                            timeout: false,
                            layout: 'topRight',
                            type: 'success',
                            closeWith: ['button'],
                            sounds: {
                                sources: ['/qrcode_table/static/lib/noty/lib/done-for-you.mp3'],
                                volume: 1,
                                conditions: ['docVisible']
                            },
                        });
                        n.show();
                        var table_id = notif.payload['table_order_display']['table_id'];
                        var table_obj = posmodel.tables_by_id[table_id];
                        await this.env.pos.setTable(table_obj);
                        this.updateTableorder();
                    }
                }
            }
            async updateTableorder() {
                // var table_id = await this.get_table_orders();
                var order = this.env.pos.get_order();
                var tableorder = await this.get_table_orders();
                if (tableorder[0]) {
                    var self = this;
                    var isexit = undefined;
                    var table = this.env.pos.tables_by_id[tableorder[0].table_id];
                    var orders = this.env.pos.orders.filter((order) => { return order.tableId == table.id && order.token == tableorder[0].token && !order.finalized });
                    if (orders.length > 0) {
                        order = orders[0];
                        isexit = order;
                        await this.env.pos.setTable(table, order.uid);
                        this.showScreen('ProductScreen');
                        setTimeout(() => {
                            this.showScreen('FloorScreen');
                        }, 200);
                    }
                    if (isexit != undefined) {
                        order = this.env.pos.get_order();
                        order.set_is_table_order(tableorder[0].is_table_order);
                        order.set_token_table(tableorder[0].token);
                        _.each(tableorder[0].line, function(line) {
                            if (line.state != 'cancel') {
                                var product = self.env.pos.db.get_product_by_id(line.product_id);
                                var is_line_exit = order.get_line_all_ready_exit(line.id);
                                if (!is_line_exit) {
                                    order.add_product(product, { quantity: line.qty, merge: false, description: line.description, price_extra: line.price_extra, table_order_line_id: line.id });
                                    var od_line = order.get_selected_orderline();
                                    od_line.set_table_order_line_id(line.id);
                                    od_line.set_note(line.note);
                                }
                            }
                        });
                        order.save_to_db();
                        await this.trigger('close-temp-screen');
                        // await this.env.pos._syncTableOrderToServer();
                    } else {
                        await this.env.pos.setTable(table, order.uid);
                        order = this.env.pos.get_order();
                        // order = this.env.pos.add_new_order();
                        order.set_is_table_order(tableorder[0].is_table_order);
                        order.set_token_table(tableorder[0].token);
                        _.each(tableorder[0].line, function(line) {
                            if (line.state != 'cancel') {
                                var product = self.env.pos.db.get_product_by_id(line.product_id);
                                var is_line_exit = order.get_line_all_ready_exit(line.id);
                                if (!is_line_exit) {
                                    order.add_product(product, { quantity: line.qty, merge: false, description: line.description, price_extra: line.price_extra });
                                    var od_line = order.get_selected_orderline();
                                    od_line.set_table_order_line_id(line.id);
                                    od_line.set_note(line.note);
                                }
                            }
                        });
                        await this.trigger('close-temp-screen');
                        // await this.env.pos._syncTableOrderToServer();
                    }
                    const SubmitOrderButton = Registries.Component.get('SubmitOrderButton');
                    await SubmitOrderButton.prototype._onClick.apply(this, arguments);
                    order.save_to_db();
                    if (tableorder[0]) {
                        // await this.env.pos._syncTableOrderToServer();
                        await this.rpc({
                            model: 'table.order',
                            method: 'change_table_prepare_order',
                            args: [tableorder[0].token.id],
                        });
                    }
                }
            }
            async get_table_orders() {
                var table_id = false;
                if (this.env.pos.table && this.env.pos.table.id) {
                    table_id = parseInt(this.env.pos.table.id);
                }
                try {
                    let tableorders = await this.rpc({
                        model: 'table.order',
                        method: 'get_table_order_lists',
                        args: [
                            [table_id]
                        ],
                    });
                    return tableorders;
                } catch (error) {
                    if (error.message.code < 0) {
                        await this.showPopup('OfflineErrorPopup', {
                            title: this.env._t('Offline'),
                            body: this.env._t('Unable to Fetch orders'),
                        });
                    } else {
                        throw error;
                    }
                }
            }
        };
    Registries.Component.extend(Chrome, PosTableChrome);
});