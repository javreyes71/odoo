"""
Script de carga de datos demo para la Cervecería.
Inserta directamente en PostgreSQL via psycopg2 los datos del demo_data.xml.
Ejecutar: python cargar_demo.py
"""
import psycopg2

DB_CONFIG = {
    "dbname": "Cerveza01",
    "user": "odoo",
    "password": "myodoo",
    "host": "localhost",
    "port": "5432"
}

def cargar_datos():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("🍺 Iniciando carga de datos demo...")

    # 1. RECETAS
    recetas = [
        ("American Pale Ale",  "ale", 100.0, 1.052, 1.011, 5.38, 35, 6, 60, 60,  7, 14, "activa", "Pale Ale americana equilibrada con notas cítricas de lúpulo Cascade."),
        ("American IPA",       "ipa", 100.0, 1.065, 1.013, 6.82, 65, 8, 75, 60, 10, 21, "activa", "IPA americana con fuerte presencia de lúpulo Centennial. Alta amargor y aroma intenso."),
        ("Munich Helles",      "lager", 100.0, 1.048, 1.010, 4.99, 18, 3, 60, 90, 14, 28, "activa", "Lager alemana suave, dorada y refrescante con carácter maltoso limpio."),
        ("Stout Irlandesa",    "stout", 80.0,  1.043, 1.011, 4.20, 40, 35, 60, 60, 10, 14, "activa", "Stout seca de estilo irlandés con notas de café y chocolate amargo."),
        ("Trigo Alemana",      "wheat", 120.0, 1.050, 1.012, 4.99, 15, 4, 45, 60,  7, 14, "activa", "Weissbier con esteres de plátano y clavo, alta turbidez y espuma persistente."),
        ("Amber Ale",          "amber", 90.0,  1.055, 1.013, 5.51, 28, 14, 60, 60, 10, 14, "activa", "Amber Ale con balance entre caramelo y amargor moderado de lúpulo."),
    ]

    receta_ids = {}
    for r in recetas:
        cur.execute("""
            INSERT INTO cerveceria_receta 
                (name, estilo_cerveza, volumen_produccion, densidad_original, densidad_final, abv,
                 ibu, srm, tiempo_macerado, tiempo_coccion, tiempo_fermentacion, tiempo_madurado,
                 estado, descripcion, create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,1,NOW(),NOW())
            ON CONFLICT DO NOTHING
            RETURNING id, name;
        """, r)
        result = cur.fetchone()
        if result:
            receta_ids[r[0]] = result[0]
            print(f"  ✅ Receta creada: {r[0]} (id={result[0]})")
        else:
            cur.execute("SELECT id FROM cerveceria_receta WHERE name = %s;", (r[0],))
            row = cur.fetchone()
            if row:
                receta_ids[r[0]] = row[0]
                print(f"  ⚠️  Receta ya existía: {r[0]} (id={row[0]})")

    conn.commit()

    # 2. LOTES DE PRODUCCIÓN
    lotes = [
        ("LOTE-2026-0001", "Batch Verano 2026",       "American Pale Ale", 100, 96.0,  "2026-01-10", "2026-02-10", "2026-02-08", 1.051, 1.010, 34, 19.5, 96.0, 5.38, "liberado",    "Lote sin incidencias. Fermentación estable. Excelente rendimiento."),
        ("LOTE-2026-0002", "IPA Invierno 2026",        "American IPA",      100,  0.0,  "2026-02-15", "2026-03-20", None,         1.065, 1.013, 65, 22.0,  0.0, 0.0,  "fermentando", "Temperatura de fermentación elevada. Monitorear."),
        ("LOTE-2026-0003", "Lager Otoño 2026",         "Munich Helles",     100, 98.5,  "2026-02-20", "2026-03-30", "2026-03-28", 1.048, 1.010, 18, 10.0, 98.5, 4.99, "liberado",    "Fermentación lager perfecta. Producto cristalino y bien carbonatado."),
        ("LOTE-2026-0004", "Stout Invierno 2026",      "Stout Irlandesa",    80, 77.5,  "2026-03-01", "2026-04-01", "2026-03-31", 1.043, 1.011, 40, 20.0, 96.8, 4.20, "liberado",    "Excelente color negro y aroma a café. Sin incidencias."),
        ("LOTE-2026-0005", "Trigo Primavera 2026",     "Trigo Alemana",     120, 115.0, "2026-03-15", "2026-04-15", "2026-04-14", 1.050, 1.012, 15, 20.0, 95.8, 4.99, "liberado",    "Turbidez característica del estilo. Sabor frutal intenso."),
        ("LOTE-2026-0006", "Amber Mayo 2026",          "Amber Ale",          90, 88.0,  "2026-04-05", "2026-05-05", "2026-05-04", 1.055, 1.013, 28, 19.0, 97.7, 5.51, "liberado",    "Perfil de caramelo bien logrado. Excelente para presentación."),
        ("LOTE-2026-0007", "Pale Ale Mayo 2026",       "American Pale Ale", 100, 94.0,  "2026-04-20", "2026-05-20", "2026-05-19", 1.052, 1.011, 35, 19.5, 94.0, 5.38, "liberado",    "Segunda producción del estilo. Consistente con el primero."),
        ("LOTE-2026-0008", "IPA Junio 2026",           "American IPA",      100, 91.0,  "2026-05-10", "2026-06-10", None,         1.065, 1.013, 63, 21.0, 91.0, 6.82, "madurando",   "En proceso de maduración. Dry hopping aplicado correctamente."),
    ]

    lote_ids = {}
    for l in lotes:
        receta_id = receta_ids.get(l[2])
        if not receta_id:
            print(f"  ❌ Receta no encontrada para lote: {l[0]}")
            continue

        cur.execute("""
            INSERT INTO cerveceria_lote
                (name, descripcion, receta_id, volumen_planificado, volumen_real,
                 fecha_inicio, fecha_fin_estimada, fecha_fin_real,
                 densidad_original_real, densidad_final_real, ibu_real,
                 temperatura_fermentacion, rendimiento, abv_real,
                 estado, notas_produccion, create_uid, write_uid, create_date, write_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,1,NOW(),NOW())
            ON CONFLICT DO NOTHING
            RETURNING id, name;
        """, (l[0], l[1], receta_id, l[3], l[4], l[5], l[6], l[7],
              l[8], l[9], l[10], l[11], l[12], l[13], l[14], l[15]))
        result = cur.fetchone()
        if result:
            lote_ids[l[0]] = result[0]
            print(f"  ✅ Lote creado: {l[0]} (id={result[0]})")
        else:
            cur.execute("SELECT id FROM cerveceria_lote WHERE name = %s;", (l[0],))
            row = cur.fetchone()
            if row:
                lote_ids[l[0]] = row[0]
                print(f"  ⚠️  Lote ya existía: {l[0]} (id={row[0]})")

    conn.commit()

    # 3. TRAZABILIDAD DE INSUMOS
    trazabilidades = [
        ("TRAZ-0001", "LOTE-2026-0001", "malta",   "macerado",     18.0, 18.0, 1500.0, 27000.0, True,  "2026-01-10 08:00:00"),
        ("TRAZ-0002", "LOTE-2026-0001", "lupulo",  "coccion",     150.0,150.0,   85.0, 12750.0, True,  "2026-01-10 11:00:00"),
        ("TRAZ-0003", "LOTE-2026-0001", "levadura","fermentacion",  2.0,  2.0, 4500.0,  9000.0, True,  "2026-01-10 16:00:00"),
        ("TRAZ-0004", "LOTE-2026-0002", "malta",   "macerado",     25.0, 22.0, 1500.0, 37500.0, False, "2026-02-15 08:00:00"),
        ("TRAZ-0005", "LOTE-2026-0002", "lupulo",  "coccion",     300.0,300.0,   95.0, 28500.0, True,  "2026-02-15 11:00:00"),
        ("TRAZ-0006", "LOTE-2026-0003", "malta",   "macerado",     20.0, 20.0, 1500.0, 30000.0, True,  "2026-02-20 08:00:00"),
        ("TRAZ-0007", "LOTE-2026-0003", "lupulo",  "coccion",      80.0, 80.0,   75.0,  6000.0, True,  "2026-02-20 11:00:00"),
        ("TRAZ-0008", "LOTE-2026-0004", "malta",   "macerado",     16.0, 16.0, 1500.0, 24000.0, True,  "2026-03-01 08:00:00"),
        ("TRAZ-0009", "LOTE-2026-0004", "lupulo",  "coccion",     120.0,120.0,   80.0,  9600.0, True,  "2026-03-01 11:00:00"),
        ("TRAZ-0010", "LOTE-2026-0005", "malta",   "macerado",     24.0, 24.0, 1500.0, 36000.0, True,  "2026-03-15 08:00:00"),
        ("TRAZ-0011", "LOTE-2026-0006", "malta",   "macerado",     19.0, 19.0, 1500.0, 28500.0, True,  "2026-04-05 08:00:00"),
        ("TRAZ-0012", "LOTE-2026-0006", "lupulo",  "coccion",     160.0,160.0,   85.0, 13600.0, True,  "2026-04-05 11:00:00"),
        ("TRAZ-0013", "LOTE-2026-0007", "malta",   "macerado",     18.0, 18.0, 1500.0, 27000.0, True,  "2026-04-20 08:00:00"),
        ("TRAZ-0014", "LOTE-2026-0008", "malta",   "macerado",     22.0, 22.0, 1500.0, 33000.0, True,  "2026-05-10 08:00:00"),
        ("TRAZ-0015", "LOTE-2026-0008", "lupulo",  "coccion",     300.0,300.0,   95.0, 28500.0, True,  "2026-05-10 11:00:00"),
    ]

    cur.execute("SELECT id FROM product_product LIMIT 1;")
    row = cur.fetchone()
    default_product_id = row[0] if row else None

    if not default_product_id:
        print("  ⚠️  No se encontraron productos en la BD. Saltando trazabilidad.")
    else:
        for t in trazabilidades:
            lote_id = lote_ids.get(t[1])
            if not lote_id:
                print(f"  ❌ Lote no encontrado para trazabilidad: {t[0]}")
                continue
            cur.execute("""
                INSERT INTO cerveceria_trazabilidad
                    (name, lote_id, product_id, uom_id, tipo_insumo, etapa_uso, cantidad_usada, cantidad_planificada,
                     costo_unitario, costo_total, conforme, fecha_uso,
                     create_uid, write_uid, create_date, write_date)
                VALUES (%s,%s,%s,1,%s,%s,%s,%s,%s,%s,%s,%s,1,1,NOW(),NOW())
                ON CONFLICT DO NOTHING;
            """, (t[0], lote_id, default_product_id, t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9]))
            print(f"  OK Trazabilidad: {t[0]} -> {t[1]}")

    conn.commit()
    cur.close()
    conn.close()

    print("\n🎉 ¡Datos demo cargados exitosamente!")

if __name__ == "__main__":
    cargar_datos()
