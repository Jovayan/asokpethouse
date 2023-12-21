odoo.define('qrcode_table.FloorScreenExtended', function(require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    var currentTableID = 0;
    window.currentTableID = currentTableID;

    const FloorScreen = require('pos_restaurant.FloorScreen');
    const Registries = require('point_of_sale.Registries');
    var addedLineIds = [];

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
                    this.showScreen(order.get_screen_data().name);
                    window.currentTableID = table;
                }
            }
            // async get_table_orders() {
            //     var table_id = false;
            //     if (this.env.pos.table && this.env.pos.table.id) {
            //         table_id = parseInt(this.env.pos.table.id);
            //     }
            //     try {
            //         let tableorders = await this.rpc({
            //             model: 'table.order',
            //             method: 'get_table_order_lists',
            //             args: [
            //                 [table_id]
            //             ],
            //         });
            //         return tableorders;
            //     } catch (error) {
            //         if (error.message.code < 0) {
            //             await this.showPopup('OfflineErrorPopup', {
            //                 title: this.env._t('Offline'),
            //                 body: this.env._t('Unable to Fetch orders'),
            //             });
            //         } else {
            //             throw error;
            //         }
            //     }
            // }
        };
    Registries.Component.extend(FloorScreen, FloorScreenExtended);
    return FloorScreen;
});