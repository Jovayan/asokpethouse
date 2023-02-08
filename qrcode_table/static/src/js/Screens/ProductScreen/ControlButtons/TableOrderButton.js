odoo.define('qrcode_table.TableOrderButton', function(require) {
    'use strict';

    const { useListener } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class TableOrderButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            const TableOrderListScreen = Registries.Component.get('TableOrderList');
            var tableorders = await TableOrderListScreen.prototype.get_table_orders.apply(this, arguments);
            await this.showTempScreen('TableOrderList', {
                'tableorders': tableorders || []
            });
        }
    }
    TableOrderButton.template = 'TableOrderButton';

    ProductScreen.addControlButton({
        component: TableOrderButton,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(TableOrderButton);

    return TableOrderButton;
});