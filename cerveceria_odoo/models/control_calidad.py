# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ControlCalidad(models.Model):
    _name = 'cerveceria.control.calidad'
    _description = 'Control de Calidad - Lote de Cerveza'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'lote_id, fecha_control desc'

    # ─── Identificación ───────────────────────────────────────────────────────
    name = fields.Char(
        string='Referencia Control',
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

    # ─── Datos del control ────────────────────────────────────────────────────
    fecha_control = fields.Datetime(
        string='Fecha / Hora del Control',
        default=fields.Datetime.now,
        required=True,
    )
    etapa_control = fields.Selection([
        ('pre_macerado', 'Pre-Macerado'),
        ('macerado', 'Macerado'),
        ('post_macerado', 'Post-Macerado'),
        ('coccion', 'Cocción'),
        ('post_coccion', 'Post-Cocción / Enfriamiento'),
        ('inoculacion', 'Inoculación de Levadura'),
        ('fermentacion_inicial', 'Fermentación Inicial'),
        ('fermentacion_activa', 'Fermentación Activa'),
        ('fermentacion_final', 'Fermentación Final'),
        ('madurado', 'Madurado / Acondicionamiento'),
        ('pre_envasado', 'Pre-Envasado'),
        ('post_envasado', 'Post-Envasado'),
        ('producto_terminado', 'Producto Terminado'),
    ], string='Etapa', required=True)

    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable del Control',
        default=lambda self: self.env.user,
    )

    resultado_general = fields.Selection([
        ('aprobado', 'Aprobado'),
        ('aprobado_condicionado', 'Aprobado con Condiciones'),
        ('rechazado', 'Rechazado'),
        ('pendiente', 'Pendiente de Evaluación'),
    ], string='Resultado General', default='pendiente', tracking=True)

    # ─── Parámetros físico-químicos ───────────────────────────────────────────

    # Temperatura
    temperatura = fields.Float(string='Temperatura (°C)', digits=(5, 2))
    temperatura_min = fields.Float(string='Temp. Mínima Permitida (°C)', digits=(5, 2))
    temperatura_max = fields.Float(string='Temp. Máxima Permitida (°C)', digits=(5, 2))
    temperatura_ok = fields.Boolean(
        string='Temperatura OK',
        compute='_compute_temperatura_ok',
        store=True,
    )

    # pH
    ph = fields.Float(string='pH', digits=(4, 2))
    ph_min = fields.Float(string='pH Mínimo', digits=(4, 2))
    ph_max = fields.Float(string='pH Máximo', digits=(4, 2))
    ph_ok = fields.Boolean(
        string='pH OK',
        compute='_compute_ph_ok',
        store=True,
    )

    # Densidad
    densidad = fields.Float(string='Densidad (SG)', digits=(5, 3))
    densidad_esperada = fields.Float(string='Densidad Esperada', digits=(5, 3))

    # Alcohol
    abv_estimado = fields.Float(string='ABV Estimado (%)', digits=(5, 2))

    # Otros parámetros
    turbidez = fields.Selection([
        ('cristalina', 'Cristalina'),
        ('ligeramente_turbia', 'Ligeramente Turbia'),
        ('turbia', 'Turbia'),
        ('muy_turbia', 'Muy Turbia'),
    ], string='Turbidez')

    color_visual = fields.Char(string='Color Visual')
    aroma = fields.Text(string='Descripción de Aroma')
    sabor = fields.Text(string='Descripción de Sabor')
    carbonatacion = fields.Float(string='Carbonatación (vol CO₂)', digits=(4, 2))
    oxigeno_disuelto = fields.Float(string='Oxígeno Disuelto (ppm)', digits=(5, 3))
    celulas_levadura = fields.Float(string='Células de Levadura (mill/mL)', digits=(10, 2))

    # ─── Resultado y acciones correctivas ────────────────────────────────────
    observaciones = fields.Text(string='Observaciones Técnicas')
    accion_correctiva = fields.Text(
        string='Acción Correctiva',
        tracking=True,
    )
    requiere_accion = fields.Boolean(
        string='Requiere Acción Correctiva',
        compute='_compute_requiere_accion',
        store=True,
    )

    # ─── Herencia Manufacturing ───────────────────────────────────────────────
    mrp_production_id = fields.Many2one(
        related='lote_id.mrp_production_id',
        string='Orden de Fabricación',
        store=True,
    )

    # ─── Computes ─────────────────────────────────────────────────────────────
    @api.depends('lote_id', 'etapa_control', 'fecha_control')
    def _compute_name(self):
        for rec in self:
            lote = rec.lote_id.name or ''
            etapa = dict(rec._fields['etapa_control'].selection).get(rec.etapa_control, '')
            rec.name = f'Control {lote} - {etapa}'

    @api.depends('temperatura', 'temperatura_min', 'temperatura_max')
    def _compute_temperatura_ok(self):
        for rec in self:
            if rec.temperatura and rec.temperatura_min and rec.temperatura_max:
                rec.temperatura_ok = rec.temperatura_min <= rec.temperatura <= rec.temperatura_max
            else:
                rec.temperatura_ok = True

    @api.depends('ph', 'ph_min', 'ph_max')
    def _compute_ph_ok(self):
        for rec in self:
            if rec.ph and rec.ph_min and rec.ph_max:
                rec.ph_ok = rec.ph_min <= rec.ph <= rec.ph_max
            else:
                rec.ph_ok = True

    @api.depends('temperatura_ok', 'ph_ok', 'resultado_general')
    def _compute_requiere_accion(self):
        for rec in self:
            rec.requiere_accion = (
                not rec.temperatura_ok
                or not rec.ph_ok
                or rec.resultado_general == 'rechazado'
            )

    # ─── Restricciones ────────────────────────────────────────────────────────
    @api.constrains('ph')
    def _check_ph(self):
        for rec in self:
            if rec.ph and not (0 <= rec.ph <= 14):
                raise ValidationError('El pH debe estar entre 0 y 14.')

    @api.constrains('temperatura_min', 'temperatura_max')
    def _check_rango_temperatura(self):
        for rec in self:
            if rec.temperatura_min and rec.temperatura_max:
                if rec.temperatura_min >= rec.temperatura_max:
                    raise ValidationError(
                        'La temperatura mínima debe ser menor que la máxima.'
                    )

    @api.constrains('ph_min', 'ph_max')
    def _check_rango_ph(self):
        for rec in self:
            if rec.ph_min and rec.ph_max:
                if rec.ph_min >= rec.ph_max:
                    raise ValidationError('El pH mínimo debe ser menor que el pH máximo.')

    @api.constrains('abv_estimado')
    def _check_abv(self):
        for rec in self:
            if rec.abv_estimado and not (0 <= rec.abv_estimado <= 100):
                raise ValidationError('El ABV debe estar entre 0% y 100%.')

    @api.constrains('carbonatacion')
    def _check_carbonatacion(self):
        for rec in self:
            if rec.carbonatacion < 0:
                raise ValidationError('La carbonatación no puede ser negativa.')

    # ─── Acciones ─────────────────────────────────────────────────────────────
    def action_aprobar(self):
        self.write({'resultado_general': 'aprobado'})

    def action_rechazar(self):
        self.write({'resultado_general': 'rechazado'})

    def action_aprobar_condicionado(self):
        self.write({'resultado_general': 'aprobado_condicionado'})

    # ─── SQL Constraints ──────────────────────────────────────────────────────
    _sql_constraints = [
        (
            'lote_etapa_fecha_uniq',
            'UNIQUE(lote_id, etapa_control, fecha_control)',
            'Ya existe un control para este lote en la misma etapa y fecha/hora.',
        ),
    ]
