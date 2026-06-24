from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

app = FastAPI(
    title="Dashboard Analítico ERP API",
    description="API RESTful modular para el consumo de datos de Odoo (Cervecería).",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos PostgreSQL
DB_CONFIG = {
    "dbname": "Cerveza01",
    "user": "odoo",
    "password": "myodoo",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """
    Retorna la conexión activa a la base de datos.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a la base de datos: {e}")

@app.get("/")
def read_root():
    """
    Endpoint raíz para comprobar que la API está funcionando.
    """
    return {
        "mensaje": "¡La API del Dashboard Analítico está funcionando correctamente!",
        "documentacion": "Visita http://localhost:8000/docs para ver y probar los endpoints interactivos."
    }

@app.get("/api/filtros")
def get_filtros():
    """
    Obtiene la lista de recetas disponibles para los filtros del dashboard.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT id, name, estilo_cerveza, estado
                FROM cerveceria_receta
                ORDER BY name ASC;
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            return {"status": "success", "data": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/kpi/grafico_uno")
def get_grafico_uno(
    receta_id: Optional[int] = Query(None, description="Filtro por ID de Receta"),
    mes: Optional[str] = Query(None, description="Filtro por mes (YYYY-MM)")
):
    """
    Retorna la producción por lote, permitiendo filtrar por receta y por mes.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # JOIN: lote de producción con su receta
            query = """
                SELECT 
                    cl.name AS codigo_batch,
                    cr.name AS nombre_receta,
                    cr.estilo_cerveza,
                    cl.volumen_real AS litros_producidos,
                    cl.rendimiento,
                    cl.abv_real,
                    cl.estado,
                    TO_CHAR(cl.fecha_inicio, 'YYYY-MM') AS mes,
                    cl.fecha_inicio,
                    cl.fecha_fin_real
                FROM cerveceria_lote cl
                JOIN cerveceria_receta cr ON cl.receta_id = cr.id
                WHERE 1=1
            """
            params = []

            # Sanitización: filtro por receta
            if receta_id:
                query += " AND cl.receta_id = %s"
                params.append(receta_id)

            # Sanitización: filtro por mes usando TO_CHAR para comparar
            if mes:
                query += " AND TO_CHAR(cl.fecha_inicio, 'YYYY-MM') = %s"
                params.append(mes)

            query += " ORDER BY cl.fecha_inicio DESC;"

            cursor.execute(query, tuple(params))
            resultados = cursor.fetchall()
            return {"status": "success", "data": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/kpi/grafico_dos")
def get_grafico_dos():
    """
    Retorna la tendencia mensual de litros producidos, vendidos y stock estimado.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Agregación mensual con CASE WHEN para calcular ventas estimadas por estado del lote
            query = """
                SELECT
                    TO_CHAR(fecha_inicio, 'YYYY-MM') AS mes,
                    COUNT(*) AS total_lotes,
                    ROUND(SUM(volumen_real)::numeric, 2) AS litros_producidos,
                    ROUND(SUM(
                        CASE
                            WHEN estado = 'liberado' THEN volumen_real * 0.85
                            ELSE 0
                        END
                    )::numeric, 2) AS litros_vendidos,
                    ROUND(SUM(
                        CASE
                            WHEN estado = 'liberado' THEN volumen_real * 0.15
                            WHEN estado IN ('fermentando', 'madurando', 'en_proceso') THEN volumen_real
                            ELSE 0
                        END
                    )::numeric, 2) AS stock_actual
                FROM cerveceria_lote
                WHERE fecha_inicio IS NOT NULL
                GROUP BY TO_CHAR(fecha_inicio, 'YYYY-MM')
                ORDER BY mes ASC;
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            return {"status": "success", "data": resultados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


