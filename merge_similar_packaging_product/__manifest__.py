# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Merge Similar Packaging Product",
  "summary"              :  """Merge Similar Packaging Product in Odoo facilitates the creation of Packaging-based products in the Odoo.""",
  "category"             :  "Sales",
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Merge-Similar-Packaging-Product.html",
  "description"          :  """Odoo Merge Similar packaging orders""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=merge_similar_packaging_product",
  "depends"              :  [
                             'sale_management',
                             'product',
                             'mrp',
                            ],
  "data"                 :  [
                             'views/stock_picking.xml',
                             'views/res_config.xml',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  15,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}