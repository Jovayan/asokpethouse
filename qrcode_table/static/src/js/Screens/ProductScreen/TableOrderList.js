odoo.define('qrcode_table.TableOrderList', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class TableOrderList extends PosComponent {
        setup() {
            super.setup();
            this.top_orders = [];
        }
        back() {
            this.trigger('close-temp-screen');
            this.showScreen('FloorScreen');
        }
        get tableorders() {
            return this.props.tableorders || [];
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
                        []
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
    }
    TableOrderList.template = 'TableOrderList';

    Registries.Component.add(TableOrderList);

    return TableOrderList;
});