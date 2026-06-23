# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrazabilidadInsumos(models.Model):
    _name = 'cerveceria.trazabilidad'
    _description = 'Trazabilidad de Insumos por Lote'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'lote_id, fecha_uso desc'

    # ─── Identificación ───────────────────────────────────────────────────────
    name = fields.Char(
        string='Referencia',
        compute='_compute_name',
        store=True,
    )

    # ─── Relaciones principales ───────────────────────────────────────────────
    lote_id = fields.Many2one(
        'cerveceria.lote',
        string='Lote de Producción',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    receta_id = fields.Many2one(
        related='lote_id.receta_id',
        string='Receta',
        store=True,
    )

    # ─── Insumo utilizado ─────────────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='Insumo',
        required=True,
        tracking=True,
    )
    tipo_insumo = fields.Selection([
        ('malta', 'Malta'),
        ('lupulo', 'Lúpulo'),
        ('levadura', 'Levadura'),
        ('adjunto', 'Adjunto'),
        ('agua', 'Agua'),
        ('quimico', 'Químico / Aditivo'),
        ('envase', 'Material de Envase'),
        ('otro', 'Otro'),
    ], string='Tipo de Insumo', required=True)

    cantidad_usada = fields.Float(string='Cantidad Usada', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unidad', required=True)

    # ─── Fecha y etapa de uso ─────────────────────────────────────────────────
    fecha_uso = fields.Datetime(
        string='Fecha/Hora de Uso',
        default=fields.Datetime.now,
        required=True,
    )
    etapa_uso = fields.Selection([
        ('macerado', 'Macerado'),
        ('coccion', 'Cocción'),
        ('whirlpool', 'Whirlpool'),
        ('enfriamiento', 'Enfriamiento'),
        ('fermentacion', 'Fermentación'),
        ('madurado', 'Madurado'),
        ('envasado', 'Envasado'),
        ('otro', 'Otro'),
    ], string='Etapa de Uso', required=True)

    # ─── Herencia Inventory ───────────────────────────────────────────────────
    # Movimiento de stock asociado al consumo del insumo
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Movimiento de Stock',
        copy=False,
        help='Movimiento de inventario generado al registrar el consumo.',
    )
    # Lote de proveedor (stock.lot) del insumo
    stock_lot_insumo_id = fields.Many2one(
        'stock.lot',
        string='Lote del Insumo (Inventario)',
        domain="[('product_id', '=', product_id)]",
        help='Lote específico del insumo usado, para trazabilidad completa.',
    )
    ubicacion_origen_id = fields.Many2one(
        'stock.location',
        string='Ubicación de Origen',
        domain=[('usage', '=', 'internal')],
    )

    # ─── Herencia Purchase ────────────────────────────────────────────────────
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Línea de Compra',
        help='Orden de compra desde donde provino este insumo.',
    )
    proveedor_id = fields.Many2one(
        related='purchase_order_line_id.partner_id',
        string='Proveedor',
        store=True,
    )

    # ─── Costos ───────────────────────────────────────────────────────────────
    costo_unitario = fields.Float(
        string='Costo Unitario',
        digits=(16, 4),
    )
    costo_total = fields.Float(
        string='Costo Total',
        compute='_compute_costo_total',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
    )

    # ─── Información adicional ────────────────────────────────────────────────
    conforme = fields.Boolean(
        string='Insumo Conforme',
        default=True,
        tracking=True,
        help='Indica si el insumo cumple con las especificaciones de la receta.',
    )
    desviacion = fields.Float(
        string='Desviación vs. Receta (%)',
        compute='_compute_desviacion',
        store=True,
    )
    cantidad_planificada = fields.Float(
        string='Cantidad Planificada (Receta)',
        compute='_compute_cantidad_planificada',
        store=True,
    )
    notas = fields.Text(string='Observaciones')

    # ─── Computes ─────────────────────────────────────────────────────────────
    @api.depends('product_id', 'lote_id', 'fecha_uso')
    def _compute_name(self):
        for rec in self:
            product = rec.product_id.name or ''
            lote = rec.lote_id.name or ''
            rec.name = f'{product} / {lote}'

    @api.depends('cantidad_usada', 'costo_unitario')
    def _compute_costo_total(self):
        for rec in self:
            rec.costo_total = rec.cantidad_usada * rec.costo_unitario

    @api.depends('lote_id', 'product_id')
    def _compute_cantidad_planificada(self):
        for rec in self:
            if rec.lote_id.receta_id and rec.product_id:
                ingrediente = rec.lote_id.receta_id.ingrediente_ids.filtered(
                    lambda i: i.product_id == rec.product_id
                )
                if ingrediente:
                    factor = rec.lote_id.volumen_planificado / (rec.lote_id.receta_id.volumen_produccion or 1)
                    rec.cantidad_planificada = ingrediente[0].cantidad * factor
                else:
                    rec.cantidad_planificada = 0.0
            else:
                rec.cantidad_planificada = 0.0

    @api.depends('cantidad_usada', 'cantidad_planificada')
    def _compute_desviacion(self):
        for rec in self:
            if rec.cantidad_planificada:
                rec.desviacion = ((rec.cantidad_usada - rec.cantidad_planificada) / rec.cantidad_planificada) * 100
            else:
                rec.desviacion = 0.0

    # ─── Restricciones ────────────────────────────────────────────────────────
    @api.constrains('cantidad_usada')
    def _check_cantidad(self):
        for rec in self:
            if rec.cantidad_usada <= 0:
                raise ValidationError('La cantidad usada debe ser mayor a 0.')

    @api.constrains('costo_unitario')
    def _check_costo(self):
        for rec in self:
            if rec.costo_unitario < 0:
                raise ValidationError('El costo unitario no puede ser negativo.')

    @api.constrains('lote_id', 'estado_lote')
    def _check_lote_activo(self):
        for rec in self:
            if rec.lote_id.estado in ('liberado', 'cancelado'):
                raise ValidationError(
                    f'No se pueden agregar insumos a un lote en estado "{rec.lote_id.estado}".'
                )

    # Validar que el estado del lote permita agregar insumos
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            lote = self.env['cerveceria.lote'].browse(vals.get('lote_id'))
            if lote and lote.estado in ('liberado', 'cancelado'):
                raise ValidationError(
                    f'No se pueden agregar insumos a un lote en estado "{lote.estado}".'
                )
        return super().create(vals_list)

    # ─── SQL Constraints ──────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'lote_product_etapa_fecha_uniq',
            'UNIQUE(lote_id, product_id, etapa_uso, fecha_uso)',
            'Ya existe un registro de este insumo en la misma etapa y hora para este lote.',
        ),
    ]
