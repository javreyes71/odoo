// Variables globales para guardar las instancias de los gráficos
let chartUno = null;
let chartDos = null;

// ─────────────────────────────────────────────────────────
// INICIO: Al cargar la página, poblar filtros y cargar todo
// ─────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    await cargarFiltros();
    await cargarGraficos(null, null); // Cargar sin filtros al inicio

    // Segmentador por Receta
    document.getElementById("filtro-carrera").addEventListener("change", (e) => {
        const receta = e.target.value || null;
        const mes    = document.getElementById("filtro-mes").value || null;
        cargarGraficos(receta, mes);
    });

    // Segmentador por Mes
    document.getElementById("filtro-mes").addEventListener("change", (e) => {
        const mes    = e.target.value || null;
        const receta = document.getElementById("filtro-carrera").value || null;
        cargarGraficos(receta, mes);
    });

    configurarExportacionPDF();
});

// Poblar los elementos select del filtro
async function cargarFiltros() {
    const selectReceta = document.getElementById("filtro-carrera");
    const selectMes    = document.getElementById("filtro-mes");

    try {
        const respuesta = await fetch('http://localhost:8000/api/filtros');
        const json = await respuesta.json();

        // Poblar select de recetas
        selectReceta.innerHTML = '<option value="">Todas las Recetas</option>';
        json.data.forEach(item => {
            const opcion = document.createElement("option");
            opcion.value = item.id;
            opcion.textContent = `${item.name} (${item.estilo_cerveza})`;
            selectReceta.appendChild(opcion);
        });

        // Poblar select de meses con datos reales desde grafico_dos
        const resDos = await fetch('http://localhost:8000/api/kpi/grafico_dos');
        const jsonDos = await resDos.json();
        selectMes.innerHTML = '<option value="">Todos los Meses</option>';
        jsonDos.data.forEach(item => {
            const opcion = document.createElement("option");
            opcion.value = item.mes;
            opcion.textContent = item.mes;
            selectMes.appendChild(opcion);
        });

    } catch (error) {
        console.error("Error al cargar los filtros:", error);
        selectReceta.innerHTML = '<option value="">Error de conexión con la API</option>';
    }
}

// Cargar y renderizar gráficos y actualizar KPIs
async function cargarGraficos(recetaId, mes) {
    try {
        // Gráfico 1: Producción por lote (filtrado opcional por receta y/o mes)
        let urlUno = 'http://localhost:8000/api/kpi/grafico_uno';
        const params = [];
        if (recetaId) params.push(`receta_id=${recetaId}`);
        if (mes)      params.push(`mes=${mes}`);
        if (params.length) urlUno += '?' + params.join('&');

        const respUno  = await fetch(urlUno);
        const jsonUno  = await respUno.json();
        const datosUno = jsonUno.data;

        // Mapear campos del JSON de la API
        const labelsUno   = datosUno.map(d => d.codigo_batch);
        const dataLitros  = datosUno.map(d => parseFloat(d.litros_producidos) || 0);
        const dataRendimiento = datosUno.map(d => parseFloat(d.rendimiento) || 0);

        // Actualizar KPIs dinámicamente (stock y ratio vienen del gráfico 2)
        const totalLitros = dataLitros.reduce((a, b) => a + b, 0);

        document.getElementById("kpi-litros").textContent = totalLitros.toFixed(0) + " L";
        document.getElementById("kpi-lotes").textContent  = datosUno.length;

        // Destruir instancia anterior para evitar superposición
        if (chartUno) chartUno.destroy();
        const ctxUno = document.getElementById('graficoUno').getContext('2d');
        chartUno = new Chart(ctxUno, {
            type: 'bar',
            data: {
                labels: labelsUno,
                datasets: [{
                    label: 'Litros Producidos',
                    data: dataLitros,
                    backgroundColor: 'rgba(247, 201, 72, 0.75)',
                    borderColor:     'rgba(232, 165, 0, 1)',
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#a0aec0', font: { family: 'Inter' } } }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { color: '#718096' }, grid: { color: '#2d3748' } },
                    x: { ticks: { color: '#718096', maxRotation: 30 }, grid: { color: '#2d3748' } }
                }
            }
        });

        // Gráfico 2: Tendencia mensual (Producido, Vendido, Stock)
        const respDos  = await fetch('http://localhost:8000/api/kpi/grafico_dos');
        const jsonDos  = await respDos.json();
        const datosDos = jsonDos.data;

        const labelsDos    = datosDos.map(d => d.mes);
        const producido    = datosDos.map(d => parseFloat(d.litros_producidos) || 0);
        const vendido      = datosDos.map(d => parseFloat(d.litros_vendidos)   || 0);
        const stockMensual = datosDos.map(d => parseFloat(d.stock_actual)      || 0);

        // Calcular stock total acumulado y ratio vendido/producido para los KPIs
        const stockTotal      = stockMensual.reduce((a, b) => a + b, 0);
        const totalProducido  = producido.reduce((a, b) => a + b, 0);
        const totalVendido    = vendido.reduce((a, b) => a + b, 0);
        const ratioDespacho   = totalProducido > 0 ? (totalVendido / totalProducido) * 100 : 0;

        document.getElementById("kpi-abv").textContent         = stockTotal.toFixed(0) + " L";
        document.getElementById("kpi-rendimiento").textContent = ratioDespacho.toFixed(1) + "%";

        if (chartDos) chartDos.destroy();
        const ctxDos = document.getElementById('graficoDos').getContext('2d');
        chartDos = new Chart(ctxDos, {
            type: 'line',
            data: {
                labels: labelsDos,
                datasets: [
                    {
                        label: '🔵 Litros Producidos',
                        data: producido,
                        backgroundColor: 'rgba(99, 179, 237, 0.15)',
                        borderColor:     'rgba(99, 179, 237, 1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointBackgroundColor: 'rgba(99, 179, 237, 1)'
                    },
                    {
                        label: '🟢 Litros Vendidos',
                        data: vendido,
                        backgroundColor: 'rgba(104, 211, 145, 0.15)',
                        borderColor:     'rgba(104, 211, 145, 1)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 5,
                        pointBackgroundColor: 'rgba(104, 211, 145, 1)'
                    },
                    {
                        label: '⚪ Stock en Bodega',
                        data: stockMensual,
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        borderColor:     'rgba(220, 220, 220, 0.85)',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 5,
                        borderDash: [5, 4],
                        pointBackgroundColor: 'rgba(220, 220, 220, 1)'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        labels: { color: '#a0aec0', font: { family: 'Inter' } }
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)} L`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#718096' },
                        grid:  { color: '#2d3748' },
                        title: { display: true, text: 'Litros', color: '#718096' }
                    },
                    x: {
                        ticks: { color: '#718096' },
                        grid:  { color: '#2d3748' }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Error al cargar los gráficos:", error);
        document.getElementById("kpi-litros").textContent = "Error";
    }
}

// Configurar exportación a PDF
function configurarExportacionPDF() {
    const btnExportar = document.getElementById("btn-exportar");

    btnExportar.addEventListener("click", () => {
        // Ocultar botón durante la exportación
        btnExportar.style.display = "none";

        const elementoAExportar = document.getElementById("panel-principal");

        const opciones = {
            margin:      10, // Margen estándar de 10mm
            filename:    'reporte_produccion_cervecera.pdf',
            image:       { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
                scale: 2, 
                backgroundColor: '#0f1117',
                useCORS: true,
                logging: false,
                width: elementoAExportar.scrollWidth,   // Capturar el ancho completo real del contenido
                height: elementoAExportar.scrollHeight, // Capturar el alto completo real del contenido
                scrollX: 0,
                scrollY: 0
            },
            jsPDF:       { unit: 'mm', format: 'a4', orientation: 'landscape' }
        };

        // Generar PDF y mostrar botón al terminar
        html2pdf()
            .set(opciones)
            .from(elementoAExportar)
            .save()
            .then(() => {
                btnExportar.style.display = "";
            })
            .catch(err => {
                console.error("Error al exportar PDF:", err);
                btnExportar.style.display = "";
            });
    });
}