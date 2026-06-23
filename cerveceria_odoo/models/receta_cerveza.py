# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RecetaCerveza(models.Model):
    _name = 'cerveceria.receta'
    _description = 'Receta de Cerveza'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    # ─── Campos básicos ───────────────────────────────────────────────────────
    name = fields.Char(
        string='Nombre de la Receta',
        required=True,
        tracking=True,
    )
    codigo = fields.Char(
        string='Código',
        copy=False,
        readonly=True,
        default='Nuevo',
    )
    estilo_cerveza = fields.Selection([
        ('lager', 'Lager'),
        ('ale', 'Ale'),
        ('ipa', 'IPA (India Pale Ale)'),
        ('stout', 'Stout'),
        ('porter', 'Porter'),
        ('wheat', 'Trigo / Wheat'),
        ('sour', 'Ácida / Sour'),
        ('saison', 'Saison'),
        ('pilsner', 'Pilsner'),
        ('otro', 'Otro'),
    ], string='Estilo', required=True, tracking=True)

    descripcion = fields.Text(string='Descripción')
    volumen_produccion = fields.Float(
        string='Volumen de Producción (L)',
        required=True,
        help='Litros que produce esta receta base.',
    )
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('activa', 'Activa'),
        ('archivada', 'Archivada'),
    ], string='Estado', default='borrador', tracking=True)

    # ─── Parámetros técnicos ──────────────────────────────────────────────────
    densidad_original = fields.Float(string='Densidad Original (OG)', digits=(5, 3))
    densidad_final = fields.Float(string='Densidad Final (FG)', digits=(5, 3))
    ibu = fields.Integer(string='Amargor (IBU)')
    srm = fields.Integer(string='Color (SRM)')
    abv = fields.Float(string='ABV (%)', digits=(5, 2), compute='_compute_abv', store=True)

    # ─── Tiempos ──────────────────────────────────────────────────────────────
    tiempo_macerado = fields.Integer(string='Tiempo de Macerado (min)')
    tiempo_coccion = fields.Integer(string='Tiempo de Cocción (min)')
    tiempo_fermentacion = fields.Integer(string='Tiempo de Fermentación (días)')
    tiempo_madurado = fields.Integer(string='Tiempo de Madurado (días)')

    # ─── Relaciones ───────────────────────────────────────────────────────────
    ingrediente_ids = fields.One2many(
        'cerveceria.receta.ingrediente',
        'receta_id',
        string='Ingredientes',
    )
    lote_ids = fields.One2many(
        'cerveceria.lote',
        'receta_id',
        string='Lotes Producidos',
    )
    lotes_count = fields.Integer(
        string='Nº Lotes',
        compute='_compute_lotes_count',
    )

    # ─── Herencia Inventory (stock.picking.type) ──────────────────────────────
    # Vinculamos la receta a una ruta de almacén por defecto
    route_ids = fields.Many2many(
        'stock.route',
        string='Rutas de Stock',
        help='Rutas de inventario asociadas a esta receta.',
    )

    # ─── Herencia Manufacturing (mrp.bom) ─────────────────────────────────────
    mrp_bom_id = fields.Many2one(
        'mrp.bom',
        string='Lista de Materiales (MRP)',
        help='BoM de fabricación generada automáticamente al activar la receta.',
        copy=False,
    )

    # ─── Computes ─────────────────────────────────────────────────────────────
    @api.depends('densidad_original', 'densidad_final')
    def _compute_abv(self):
        for rec in self:
            if rec.densidad_original and rec.densidad_final:
                rec.abv = (rec.densidad_original - rec.densidad_final) * 131.25
            else:
                rec.abv = 0.0

    def _compute_lotes_count(self):
        for rec in self:
            rec.lotes_count = len(rec.lote_ids)

    # ─── Secuencia automática ─────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('codigo', 'Nuevo') == 'Nuevo':
                vals['codigo'] = self.env['ir.sequence'].next_by_code('cerveceria.receta') or 'Nuevo'
        return super().create(vals_list)

    # ─── Restricciones ────────────────────────────────────────────────────────
    @api.constrains('volumen_produccion')
    def _check_volumen(self):
        for rec in self:
            if rec.volumen_produccion <= 0:
                raise ValidationError('El volumen de producción debe ser mayor a 0 litros.')

    @api.constrains('densidad_original', 'densidad_final')
    def _check_densidades(self):
        for rec in self:
            if rec.densidad_original and rec.densidad_final:
                if rec.densidad_final >= rec.densidad_original:
                    raise ValidationError(
                        'La densidad final (FG) debe ser menor que la densidad original (OG).'
                    )

    @api.constrains('ibu')
    def _check_ibu(self):
        for rec in self:
            if rec.ibu and rec.ibu < 0:
                raise ValidationError('El IBU no puede ser negativo.')

    # ─── Acciones de estado ───────────────────────────────────────────────────
    def action_activar(self):
        self.write({'estado': 'activa'})

    def action_archivar(self):
        self.write({'estado': 'archivada'})

    def action_borrador(self):
        self.write({'estado': 'borrador'})

    def action_ver_lotes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Lotes de {self.name}',
            'res_model': 'cerveceria.lote',
            'view_mode': 'list,form',
            'domain': [('receta_id', '=', self.id)],
            'context': {'default_receta_id': self.id},
        }

    # ─── SQL Constraints ──────────────────────────────────────────────────────
    _sql_constraints = [
        ('codigo_uniq', 'UNIQUE(codigo)', 'El código de receta debe ser único.'),
        ('name_estilo_uniq', 'UNIQUE(name, estilo_cerveza)', 'Ya existe una receta con ese nombre y estilo.'),
    ]


class RecetaCervezaIngrediente(models.Model):
    _name = 'cerveceria.receta.ingrediente'
    _description = 'Ingrediente de Receta de Cerveza'
    _order = 'tipo_ingrediente, sequence'

    receta_id = fields.Many2one(
        'cerveceria.receta',
        string='Receta',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Orden', default=10)
    product_id = fields.Many2one(
        'product.product',
        string='Insumo / Producto',
        required=True,
        domain=[('type', 'in', ['consu', 'product'])],
    )
    tipo_ingrediente = fields.Selection([
        ('malta', 'Malta'),
        ('lupulo', 'Lúpulo'),
        ('levadura', 'Levadura'),
        ('adjunto', 'Adjunto'),
        ('agua', 'Agua'),
        ('otro', 'Otro'),
    ], string='Tipo', required=True)
    cantidad = fields.Float(string='Cantidad', required=True)
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de Medida',
        required=True,
    )
    momento_adicion = fields.Selection([
        ('macerado', 'Macerado'),
        ('coccion', 'Cocción'),
        ('whirlpool', 'Whirlpool'),
        ('fermentacion', 'Fermentación'),
        ('madurado', 'Madurado'),
        ('envasado', 'Envasado'),
    ], string='Momento de Adición')
    notas = fields.Char(string='Notas')

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for rec in self:
            if rec.cantidad <= 0:
                raise ValidationError('La cantidad del ingrediente debe ser mayor a 0.')
