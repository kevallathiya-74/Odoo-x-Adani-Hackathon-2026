# -*- coding: utf-8 -*-
{
    'name': 'Maintenance Management',
    'version': '1.0.0',
    'category': 'Services/Maintenance',
    'summary': 'Equipment and Maintenance Management System',
    'description': """
        Maintenance Management System for Odoo × Adani Hackathon 2026
        ================================================================
        
        Features:
        ---------
        * Equipment/Asset tracking
        * Maintenance team management
        * Corrective and preventive maintenance workflows
        * Kanban, Calendar, and Form views
        * Real-time analytics and reporting
        * MongoDB backend integration
        
        Technical:
        ----------
        * Custom ORM layer for MongoDB
        * Odoo-style MVC architecture
        * RESTful API endpoints
        * Real data persistence (no mock data)
    """,
    'author': 'Odoo × Adani Hackathon Team',
    'website': 'https://github.com/yourusername/Odoo-Adani-Hackathon-2026',
    'license': 'LGPL-3',
    'depends': [],
    'data': [
        # Security
        'security/maintenance_security.xml',
        'security/ir.model.access.csv',
        
        # Views
        'views/equipment_views.xml',
        'views/maintenance_team_views.xml',
        'views/maintenance_request_views.xml',
        'views/dashboard_views.xml',
        
        # Reports
        'reports/maintenance_reports.xml',
        
        # Data
        'data/maintenance_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['pymongo', 'flask', 'flask_cors', 'python-dateutil'],
    },
}
