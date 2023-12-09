odoo.define('qrcode_table.TableOrderLine', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class TableOrderLine extends PosComponent {
        setup() {
            super.setup();
            useListener('toggleLineChange', (ev) => this.toggle_table_order(ev));
            this.clicked = false;
        }
        toggle_table_order(ev) {
            var line_id = $(ev.currentTarget).closest('tr').data('id');
            $('.table_order_client_line').removeClass('highlight');
            $('.table_order_list_product').addClass('trhide');
            $(ev.currentTarget).closest('tr').toggleClass('highlight');
            $('tr[data-parent_id~="' + line_id + '"]').toggleClass('trhide');
        }
        async add_to_cart_table_order() {
            var self = this;
            var order = undefined;
            var isexit = undefined
            var table = this.env.pos.tables_by_id[this.props.tos.table_id];
            var orders = this.env.pos.orders.filter((order) => { return order.tableId == table.id && order.token == this.props.tos.token && !order.finalized });
            if (orders.length > 0) {
                order = orders[0];
                isexit = order;
                await this.env.pos.setTable(table, order.uid);
            }
            if (isexit != undefined) {
                order = this.env.pos.get_order();
                order.set_is_table_order(this.props.tos.is_table_order);
                order.set_token_table(this.props.tos.token);
                _.each(this.props.tos.line, function(line) {
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
                await this.env.pos._syncTableOrdersToServer();
            } else {
                await this.env.pos.setTable(table);
                order = this.env.pos.get_order();
                // order = this.env.pos.add_new_order();
                order.set_is_table_order(this.props.tos.is_table_order);
                order.set_token_table(this.props.tos.token);
                _.each(this.props.tos.line, function(line) {
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
                await this.env.pos.setTable(table, order.uid);
                await this.env.pos._syncTableOrdersToServer();
            }
        }
        async _onClickSendKitchen() {
            await this.add_to_cart_table_order();
            const order = this.env.pos.get_order();
            const SubmitOrderButton = Registries.Component.get('SubmitOrderButton');
            await SubmitOrderButton.prototype._onClick.apply(this, arguments);
            order.save_to_db();
            await this.env.pos._syncTableOrdersToServer();
            await this.rpc({
                model: 'table.order',
                method: 'change_table_prepare_order',
                args: [this.props.tos.id],
            });
        }
        async _onClickAcceptAllOrder() {
            try {
                let res = await this.rpc({
                    model: 'table.order',
                    method: 'change_table_accept_all_order',
                    args: [this.props.tos.id],
                });
                if (res) {
                    const TableOrderList = Registries.Component.get('TableOrderList');
                    var tableorders = await TableOrderList.prototype.get_table_orders.apply(this, arguments);
                    await this.trigger('close-temp-screen');
                    await this.showTempScreen('TableOrderList', {
                        'tableorders': tableorders || []
                    });
                }
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to Accept order'),
                    });
                } else {
                    throw error;
                }
            }
        }
        async _onClickCancelAllOrder() {
            try {
                let res = await this.rpc({
                    model: 'table.order',
                    method: 'change_table_cance_all_order',
                    args: [this.props.tos.id],
                });
                if (res) {
                    const TableOrderList = Registries.Component.get('TableOrderList');
                    var tableorders = await TableOrderList.prototype.get_table_orders.apply(this, arguments);
                    this.trigger('close-temp-screen');
                    await this.showTempScreen('TableOrderList', {
                        'tableorders': tableorders || []
                    });
                }
            } catch (error) {
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to Cancel Order'),
                    });
                } else {
                    throw error;
                }
            }
        }
        filter_order(token, table_id) {
            var ex_order = false
            _.each(this.env.pos.get_order_list(), function(order) {
                if (order.token == token && order.is_table_order) {
                    ex_order = order;
                }
            });
            return ex_order;
        }
    }
    TableOrderLine.template = 'TableOrderLine';

    Registries.Component.add(TableOrderLine);

    return TableOrderLine;
});