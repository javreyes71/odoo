# -*- coding: utf-8 -*-
from odoo import models, fields


# ══════════════════════════════════════════════════════════════════════════════
# HERENCIA 1: product.template (Inventario / Productos)
# Agrega información cervecera a la ficha de producto
# ══════════════════════════════════════════════════════════════════════════════
class ProductTemplateCerveceria(models.Model):
    _inherit = 'product.template'

    es_insumo_cervecero = fields.Boolean(
        string='Es Insumo Cervecero',
        default=False,
        help='Indica que este producto se usa en la producción de cerveza.',
    )
    tipo_insumo_cervecero = fields.Selection([
        ('malta', 'Malta'),
        ('lupulo', 'Lúpulo'),
        ('levadura', 'Levadura'),
        ('adjunto', 'Adjunto'),
        ('agua', 'Agua'),
        ('quimico', 'Químico / Aditivo'),
        ('envase', 'Material de Envase'),
        ('otro', 'Otro'),
    ], string='Tipo de Insumo Cervecero')
    origen_insumo = fields.Char(
        string='Origen / Variedad',
        help='Ej: Malta Pilsner alemana, Lúpulo Cascade USA.',
    )
    alpha_acidos = fields.Float(
        string='Alpha Ácidos (%)',
        digits=(5, 2),
        help='Solo para lúpulos. Porcentaje de alfa ácidos.',
    )


# ══════════════════════════════════════════════════════════════════════════════
# HERENCIA 2: sale.order (Ventas)
# Agrega campos de lote cervecero y estilo directamente en el pedido
# ══════════════════════════════════════════════════════════════════════════════
class SaleOrderCerveceria(models.Model):
    _inherit = 'sale.order'

    lote_cervecero_id = fields.Many2one(
        'cerveceria.lote',
        string='Lote Cervecero',
        domain=[('estado', '=', 'liberado')],
        help='Lote de cerveza al que corresponde este pedido de venta.',
    )
    estilo_cerveza_venta = fields.Selection(
        related='lote_cervecero_id.estilo_cerveza',
        string='Estilo de Cerveza',
        store=True,
        readonly=True,
    )
    notas_cerveceria = fields.Text(
        string='Notas de Cervecería',
        help='Información adicional sobre el lote o producto para el cliente.',
    )


# ══════════════════════════════════════════════════════════════════════════════
# HERENCIA 3: purchase.order (Compras)
# Vincula órdenes de compra con recetas que requieren esos insumos
# ══════════════════════════════════════════════════════════════════════════════
class PurchaseOrderCerveceria(models.Model):
    _inherit = 'purchase.order'

    receta_destino_id = fields.Many2one(
        'cerveceria.receta',
        string='Receta Destino',
        help='Receta de cerveza para la que se compran estos insumos.',
    )
    lote_destino_id = fields.Many2one(
        'cerveceria.lote',
        string='Lote Destino',
        domain=[('estado', 'in', ('planificado', 'en_proceso'))],
        help='Lote de producción al que se destinarán estos insumos.',
    )
    es_compra_cerveceria = fields.Boolean(
        string='Compra para Cervecería',
        compute='_compute_es_compra_cerveceria',
        store=True,
    )

    def _compute_es_compra_cerveceria(self):
        for rec in self:
            rec.es_compra_cerveceria = bool(rec.receta_destino_id or rec.lote_destino_id)


# ══════════════════════════════════════════════════════════════════════════════
# HERENCIA 4: mrp.production (Fabricación)
# Vincula la orden de fabricación con receta y lote cervecero
# ══════════════════════════════════════════════════════════════════════════════
class MrpProductionCerveceria(models.Model):
    _inherit = 'mrp.production'

    receta_cerveza_id = fields.Many2one(
        'cerveceria.receta',
        string='Receta de Cerveza',
        domain=[('estado', '=', 'activa')],
        help='Receta cervecera que origina esta orden de fabricación.',
    )
    lote_cervecero_id = fields.Many2one(
        'cerveceria.lote',
        string='Lote Cervecero',
        help='Lote de producción cervecera asociado a esta orden.',
    )
    estilo_cerveza = fields.Selection(
        related='receta_cerveza_id.estilo_cerveza',
        string='Estilo',
        store=True,
        readonly=True,
    )
    abv_objetivo = fields.Float(
        related='receta_cerveza_id.abv',
        string='ABV Objetivo (%)',
        readonly=True,
        digits=(5, 2),
    )
