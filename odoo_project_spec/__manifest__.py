# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Odoo Project Spec",
    "summary": "Handle module import from spec.yaml",
    "version": "16.0.1.0.0",
    "category": "Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/camptocamp/odoo-repository",
    "installable": True,
    "depends": [
        "odoo_project",
    ],
    "data": [
        "wizards/odoo_project_import_modules.xml",
    ],
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [
            "pyyaml>=6.0.2",
        ],
    },
}
