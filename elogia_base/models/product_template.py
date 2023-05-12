# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product brand"

    name = fields.Char(
        string="Brand name",
        required=True,
        help="Brand name"
    )
    description = fields.Text(
        string="Description",
        help="Description for Brand"
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        comodel_name="product.brand",
        string="Brands"
    )