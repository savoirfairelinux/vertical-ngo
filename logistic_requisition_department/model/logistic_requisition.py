# -*- coding: utf-8 -*-
# Author: Leonardo Pistone
# Copyright 2014 Camptocamp SA (http://www.camptocamp.com)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public Lice
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from openerp import models, fields, api


class LogisticRequisition(models.Model):
    _inherit = 'logistic.requisition'

    def _get_my_department(self):
        return self.env.user.employee_ids[0].department_id

    department_id = fields.Many2one('hr.department', 'Department',
                                    default=_get_my_department)


class LogisticRequisitionLine(models.Model):
    _inherit = 'logistic.requisition.line'

    department_id = fields.Many2one(related='requisition_id.department_id',
                                    store=True)


class LogisticRequisitionSource(models.Model):
    _inherit = 'logistic.requisition.source'

    department_id = fields.Many2one(
        related='requisition_line_id.requisition_id.department_id',
        store=True)

    @api.multi
    def _prepare_po_requisition(self, purch_req_lines, pricelist=None):
        res = super(LogisticRequisitionSource, self)._prepare_po_requisition(
            purch_req_lines, pricelist)

        res['department_id'] = self.department_id.id
        return res
