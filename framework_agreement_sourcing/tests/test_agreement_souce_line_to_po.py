# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from .common import CommonSourcingSetUp


class TestSourceToPo(CommonSourcingSetUp):

    def setUp(self):
        # we generate a source line
        super(TestSourceToPo, self).setUp()
        cr, uid = self.cr, self.uid
        lines = self.requisition.line_ids
        self.agr_line = None
        self.wiz_model = self.registry(
            'logistic.requisition.source.create.agr.po')
        for line in lines:
            if line.product_id == self.cheap_on_low_agreement.product_id:
                self.agr_line = line
                break
        self.assertTrue(self.agr_line, 'no agr line found')
        self.agr_line.write({'requested_qty': 400})
        self.agr_line.refresh()
        source_ids = []
        for line in lines:
            if (line.product_id.id == self.product_id or
                    line.product_id.type == 'service'):
                lid = self.requisition_line_model._generate_source_line(
                    cr, uid, line)
                source_ids += lid
        self.assertEqual(len(source_ids), 2)
        self.source_lines = self.source_line_model.browse(cr, uid, source_ids)
        self.lta_source = next(x for x in self.source_lines
                               if x.procurement_method == 'fw_agreement')
        self.other_source = next(x for x in self.source_lines
                                 if x.procurement_method == 'other')

    def test_01_transform_source_to_agreement_wh_dest(self):
        """Test transformation of an agreement source line into PO"""
        cr, uid = self.cr, self.uid

        # Set destination address
        partner_vals = {
            'name': 'Warehouse address',
            }
        partner_wh = self.env['res.partner'].create(partner_vals)
        warehouse_id = self.ref('stock.warehouse0')
        warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        warehouse.partner_id = partner_wh
        picking_type_wh = self.ref('stock.picking_type_in')
        self.agr_line.consignee_shipping_id = partner_wh

        self.assertTrue(self.lta_source, 'no lta source found')
        self.lta_source.refresh()
        active_ids = [x.id for x in self.source_lines]
        wiz_ctx = {'active_model': 'logistic.requisition.source',
                   'active_ids': active_ids}
        wiz_id = self.wiz_model.create(self.cr, self.uid, {},
                                       context=wiz_ctx)

        po_id = self.wiz_model.action_create_agreement_po_requisition(
            cr, uid, [wiz_id], context=wiz_ctx)['res_id']
        self.assertTrue(po_id, "no PO created")
        supplier = self.lta_source.framework_agreement_id.supplier_id
        add = self.lta_source.requisition_id.consignee_shipping_id
        consignee = self.lta_source.requisition_id.consignee_id
        po = self.registry('purchase.order').browse(cr, uid, po_id)
        date_order = self.lta_source.requisition_id.date
        date_delivery = self.lta_source.requisition_id.date_delivery
        self.assertEqual(po.partner_id, supplier)
        self.assertEqual(
            po.pricelist_id, supplier.property_product_pricelist_purchase)
        self.assertEqual(po.date_order, date_order)
        self.assertEqual(po.dest_address_id, add)
        self.assertEqual(po.picking_type_id.id, picking_type_wh)
        self.assertEqual(po.consignee_id, consignee)
        self.assertEqual(po.state, 'draftpo')
        self.assertNotEqual(po.name, self.requisition.name)
        self.assertEqual(len(po.order_line), 2)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.lta_source.framework_agreement_id.product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.lta_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(po_line.product_uom, self.lta_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 50.0)
        self.assertEqual(po_line.lr_source_line_id, self.lta_source)
        self.assertEqual(po_line.date_planned, date_delivery)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_uom, self.other_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 1.0)
        self.assertEqual(po_line.lr_source_line_id, self.other_source)

    def test_01_transform_source_to_agreement_dropshipping(self):
        """Test transformation of an agreement source line into PO"""
        cr, uid = self.cr, self.uid

        # Set destination address
        partner_dropship = self.ref('base.res_partner_12')
        self.agr_line.consignee_shipping_id = partner_dropship

        self.assertTrue(self.lta_source, 'no lta source found')
        self.lta_source.refresh()
        active_ids = [x.id for x in self.source_lines]
        wiz_ctx = {'active_model': 'logistic.requisition.source',
                   'active_ids': active_ids}
        wiz_id = self.wiz_model.create(self.cr, self.uid, {}, context=wiz_ctx)

        po_id = self.wiz_model.action_create_agreement_po_requisition(
            cr, uid, [wiz_id], context=wiz_ctx)['res_id']
        self.assertTrue(po_id, "no PO created")
        supplier = self.lta_source.framework_agreement_id.supplier_id
        add = self.lta_source.requisition_id.consignee_shipping_id
        consignee = self.lta_source.requisition_id.consignee_id
        po = self.registry('purchase.order').browse(cr, uid, po_id)
        date_order = self.lta_source.requisition_id.date
        date_delivery = self.lta_source.requisition_id.date_delivery
        self.assertEqual(po.partner_id, supplier)
        self.assertEqual(
            po.pricelist_id, supplier.property_product_pricelist_purchase)
        self.assertEqual(po.date_order, date_order)
        self.assertEqual(po.dest_address_id, add)
        self.assertEqual(po.picking_type_id.name, 'Dropship')
        self.assertEqual(po.consignee_id, consignee)
        self.assertEqual(po.state, 'draftpo')
        self.assertNotEqual(po.name, self.requisition.name)
        self.assertEqual(len(po.order_line), 2)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.lta_source.framework_agreement_id.product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.lta_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.lta_source.proposed_qty)
        self.assertEqual(po_line.product_uom, self.lta_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 50.0)
        self.assertEqual(po_line.lr_source_line_id, self.lta_source)
        self.assertEqual(po_line.date_planned, date_delivery)

        po_line = next(x for x in po.order_line
                       if x.product_id ==
                       self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_id, self.other_source.proposed_product_id)
        self.assertEqual(po_line.product_qty, self.other_source.proposed_qty)
        self.assertEqual(
            po_line.product_uom, self.other_source.proposed_uom_id)
        self.assertAlmostEqual(po_line.price_unit, 1.0)
        self.assertEqual(po_line.lr_source_line_id, self.other_source)
