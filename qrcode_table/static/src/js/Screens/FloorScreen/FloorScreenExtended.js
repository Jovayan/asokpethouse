odoo.define('qrcode_table.FloorScreenExtended', function(require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const FloorScreen = require('pos_restaurant.FloorScreen');
    const Registries = require('point_of_sale.Registries');

    const FloorScreenExtended = (FloorScreen) =>
        class extends FloorScreen {
            async onSelectTable(table) {
                if (this.state.isEditMode) {
                    this.state.selectedTableId = table.id;
                } else {
                    try {
                        if (this.env.pos.orderToTransfer) {
                            await this.env.pos.transferTable(table);
                        } else {
                            await this.env.pos.setTable(table);
                        }
                    } catch (error) {
                        if (isConnectionError(error)) {
                            await this.showPopup('OfflineErrorPopup', {
                                title: this.env._t('Offline'),
                                body: this.env._t('Unable to fetch orders'),
                            });
                        } else {
                            throw error;
                        }
                    }
                    var order = this.env.pos.get_order();
                    var tableorder = await this.get_table_orders();
                    if (tableorder[0]) {
                        var self = this;
                        var isexit = undefined
                        var table = this.env.pos.tables_by_id[tableorder[0].table_id];
                        var orders = this.env.pos.orders.filter((order) => { return order.tableId == table.id && order.token == tableorder[0].token && !order.finalized });
                        if (orders.length > 0) {
                            order = orders[0];
                            isexit = order;
                            await this.env.pos.setTable(table, order.uid);
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
                            await this.trigger('close-temp-screen');
                            order.save_to_db();
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
                                        order.add_product(product, { quantity: line.qty, merge: false, description: line.description, price_extra: line.price_unit });
                                        var od_line = order.get_selected_orderline();
                                        od_line.set_table_order_line_id(line.id);
                                        od_line.set_note(line.note);
                                    }
                                }
                            });
                            await this.trigger('close-temp-screen');
                            // await this.env.pos._syncTableOrderToServer();
                        }
                        // const SubmitOrderButton = Registries.Component.get('SubmitOrderButton');
                        // await SubmitOrderButton.prototype._onClick.apply(this, arguments);
                        // order.save_to_db();
                        // if (tableorder[0]) {
                        //     // await this.env.pos._syncTableOrderToServer();
                        //     await this.rpc({
                        //         model: 'table.order',
                        //         method: 'change_table_prepare_order',
                        //         args: [tableorder[0].token.id],
                        //     });
                        // }
                    }
                }
                this.showScreen(order.get_screen_data().name);
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
    Registries.Component.extend(FloorScreen, FloorScreenExtended);
    return FloorScreen;
});