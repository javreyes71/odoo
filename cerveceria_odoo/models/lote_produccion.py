# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class LoteProduccion(models.Model):
    _name = 'cerveceria.lote'
    _description = 'Lote de Producción de Cerveza'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc'

    # ─── Identificación ───────────────────────────────────────────────────────
    name = fields.Char(
        string='Nº de Lote',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
    )
    descripcion = fields.Char(string='Descripción / Alias del Lote')

    estado = fields.Selection([
        ('planificado', 'Planificado'),
        ('en_proceso', 'En Proceso'),
        ('fermentando', 'Fermentando'),
        ('madurando', 'Madurando'),
        ('envasado', 'Envasado'),
        ('liberado', 'Liberado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='planificado', tracking=True)

    # ─── Relación con receta ──────────────────────────────────────────────────
    receta_id = fields.Many2one(
        'cerveceria.receta',
        string='Receta',
        required=True,
        tracking=True,
        domain=[('estado', '=', 'activa')],
    )
    estilo_cerveza = fields.Selection(
        related='receta_id.estilo_cerveza',
        string='Estilo',
        store=True,
    )

    # ─── Volúmenes ────────────────────────────────────────────────────────────
    volumen_planificado = fields.Float(
        string='Volumen Planificado (L)',
        required=True,
    )
    volumen_real = fields.Float(
        string='Volumen Real Obtenido (L)',
        tracking=True,
    )
    rendimiento = fields.Float(
        string='Rendimiento (%)',
        compute='_compute_rendimiento',
        store=True,
    )

    # ─── Fechas ───────────────────────────────────────────────────────────────
    fecha_inicio = fields.Date(string='Fecha de Inicio', default=fields.Date.today, required=True)
    fecha_fin_estimada = fields.Date(string='Fecha de Fin Estimada')
    fecha_fin_real = fields.Date(string='Fecha de Fin Real', tracking=True)
    fecha_envasado = fields.Date(string='Fecha de Envasado', tracking=True)

    # ─── Responsable ──────────────────────────────────────────────────────────
    responsable_id = fields.Many2one(
        'res.users',
        string='Maestro Cervecero',
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ─── Parámetros técnicos reales ───────────────────────────────────────────
    densidad_original_real = fields.Float(string='OG Real', digits=(5, 3))
    densidad_final_real = fields.Float(string='FG Real', digits=(5, 3))
    abv_real = fields.Float(
        string='ABV Real (%)',
        compute='_compute_abv_real',
        store=True,
    )
    ibu_real = fields.Integer(string='IBU Real')
    temperatura_fermentacion = fields.Float(string='Temp. Fermentación (°C)')

    # ─── Observaciones ────────────────────────────────────────────────────────
    notas_produccion = fields.Text(string='Notas de Producción')

    # ─── Relaciones con otros modelos nativos ─────────────────────────────────
    trazabilidad_ids = fields.One2many(
        'cerveceria.trazabilidad',
        'lote_id',
        string='Insumos Utilizados',
    )
    control_calidad_ids = fields.One2many(
        'cerveceria.control.calidad',
        'lote_id',
        string='Controles de Calidad',
    )
    insumos_count = fields.Integer(
        string='Insumos',
        compute='_compute_counts',
    )
    controles_count = fields.Integer(
        string='Controles',
        compute='_compute_counts',
    )

    # ─── Herencia Manufacturing (mrp.production) ──────────────────────────────
    mrp_production_id = fields.Many2one(
        'mrp.production',
        string='Orden de Fabricación',
        copy=False,
        tracking=True,
    )

    # ─── Herencia Inventory (stock.lot) ───────────────────────────────────────
    stock_lot_id = fields.Many2one(
        'stock.lot',
        string='Lote en Inventario',
        copy=False,
        help='Lote de seguimiento en Inventario vinculado a este lote cervecero.',
    )

    # ─── Herencia Sales (sale.order) ──────────────────────────────────────────
    sale_order_ids = fields.Many2many(
        'sale.order',
        'cerveceria_lote_sale_rel',
        'lote_id',
        'sale_id',
        string='Pedidos de Venta',
    )
    ventas_count = fields.Integer(
        string='Ventas',
        compute='_compute_ventas_count',
    )

    # ─── Computes ─────────────────────────────────────────────────────────────
    @api.depends('volumen_real', 'volumen_planificado')
    def _compute_rendimiento(self):
        for rec in self:
            if rec.volumen_planificado:
                rec.rendimiento = (rec.volumen_real / rec.volumen_planificado) * 100
            else:
                rec.rendimiento = 0.0

    @api.depends('densidad_original_real', 'densidad_final_real')
    def _compute_abv_real(self):
        for rec in self:
            if rec.densidad_original_real and rec.densidad_final_real:
                rec.abv_real = (rec.densidad_original_real - rec.densidad_final_real) * 131.25
            else:
                rec.abv_real = 0.0

    def _compute_counts(self):
        for rec in self:
            rec.insumos_count = len(rec.trazabilidad_ids)
            rec.controles_count = len(rec.control_calidad_ids)

    def _compute_ventas_count(self):
        for rec in self:
            rec.ventas_count = len(rec.sale_order_ids)

    # ─── Secuencia automática ─────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('cerveceria.lote') or 'Nuevo'
        return super().create(vals_list)

    # ─── Restricciones ────────────────────────────────────────────────────────
    @api.constrains('volumen_planificado')
    def _check_volumen_planificado(self):
        for rec in self:
            if rec.volumen_planificado <= 0:
                raise ValidationError('El volumen planificado debe ser mayor a 0 litros.')

    @api.constrains('volumen_real')
    def _check_volumen_real(self):
        for rec in self:
            if rec.volumen_real < 0:
                raise ValidationError('El volumen real no puede ser negativo.')

    @api.constrains('fecha_inicio', 'fecha_fin_estimada')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_fin_estimada and rec.fecha_inicio:
                if rec.fecha_fin_estimada < rec.fecha_inicio:
                    raise ValidationError('La fecha de fin estimada no puede ser anterior a la de inicio.')

    @api.constrains('densidad_original_real', 'densidad_final_real')
    def _check_densidades_reales(self):
        for rec in self:
            if rec.densidad_original_real and rec.densidad_final_real:
                if rec.densidad_final_real >= rec.densidad_original_real:
                    raise ValidationError('La FG real debe ser menor que la OG real.')

    # ─── Acciones de estado ───────────────────────────────────────────────────
    def action_iniciar(self):
        self.write({'estado': 'en_proceso'})

    def action_fermentar(self):
        self.write({'estado': 'fermentando'})

    def action_madurar(self):
        self.write({'estado': 'madurando'})

    def action_envasar(self):
        self.write({
            'estado': 'envasado',
            'fecha_envasado': date.today(),
        })

    def action_liberar(self):
        self.write({
            'estado': 'liberado',
            'fecha_fin_real': date.today(),
        })

    def action_cancelar(self):
        self.write({'estado': 'cancelado'})

    def action_ver_insumos(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Insumos del Lote {self.name}',
            'res_model': 'cerveceria.trazabilidad',
            'view_mode': 'list,form',
            'domain': [('lote_id', '=', self.id)],
            'context': {'default_lote_id': self.id},
        }

    def action_ver_ventas(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ventas del Lote {self.name}',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
        }

    def action_ver_controles(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Controles del Lote {self.name}',
            'res_model': 'cerveceria.control.calidad',
            'view_mode': 'list,form',
            'domain': [('lote_id', '=', self.id)],
            'context': {'default_lote_id': self.id},
        }

    # ─── SQL Constraints ──────────────────────────────────────────────────────
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'El número de lote debe ser único.'),
    ]
