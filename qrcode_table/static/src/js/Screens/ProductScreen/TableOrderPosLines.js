odoo.define('qrcode_table.TableOrderPosLines', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class TableOrderPosLines extends PosComponent {
        setup() {
            super.setup();
            useListener('change-linne-state', this.LineStateChnage);
        }
        async LineStateChnage(event) {
            try {
                const detail = event.detail;
                let tableorderslinestate = await this.rpc({
                    model: 'table.order.line',
                    method: 'change_table_order_state',
                    args: [detail.line_id, detail.state],
                });
                if (tableorderslinestate) {
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
                        body: this.env._t('Unable to change state'),
                    });
                } else {
                    throw error;
                }
            }
        }
    }
    TableOrderPosLines.template = 'TableOrderPosLines';

    Registries.Component.add(TableOrderPosLines);

    return TableOrderPosLines;
});