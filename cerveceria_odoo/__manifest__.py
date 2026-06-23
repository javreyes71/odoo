# -*- coding: utf-8 -*-
{
    'name': 'Cervecería Odoo',
    'version': '18.0.1.0.0',
    'summary': 'Gestión integral de producción cervecera artesanal',
    'description': """
        Módulo para la gestión completa de una cervecería artesanal:
        - Recetas de cerveza
        - Lotes de producción
        - Trazabilidad de insumos
        - Control de calidad (temperatura, pH, densidad, etc.)
    """,
    'author': 'Cervecería Odoo',
    'category': 'Manufacturing',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'stock',
        'sale_management',
        'purchase',
        'mrp',
    ],
    'data': [
        # 1. Grupos de seguridad (deben ir primero)
        'security/cerveceria_security.xml',
        # 2. Datos base
        'data/cerveceria_data.xml',
        # 3. Vistas
        'views/receta_cerveza_views.xml',
        'views/lote_produccion_views.xml',
        'views/trazabilidad_insumos_views.xml',
        'views/control_calidad_views.xml',
        'views/herencia_nativos_views.xml',
        'views/cerveceria_menu.xml',
        # 4. Reportes gerenciales PDF
        'report/reporte_gerencial_produccion.xml',
        'report/reporte_gerencial_calidad.xml',
        # Reportes web
        'report/report_lote_produccion.xml',
        'report/report_receta_cerveza.xml',
        # 5. ACL al final, cuando los modelos ya están registrados
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
