# Copyright 2024 Raphaël Reverdy <raphael.reverdy@akretion.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Odoo Repository PR",
    "summary": "add forked branch / Pull Request concept",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/akretion/odoo-repository",
    "installable": True,
    "depends": [
        "odoo_repository",
        "odoo_project",
        "odoo_project_migration",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/odoo_repository.xml",
        "views/odoo_module_branch.xml",
    ],
    "license": "AGPL-3",
}
