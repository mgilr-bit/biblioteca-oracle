/**
 * Utilidades de reportes: formateo de valores, descarga de archivos y
 * generación del PDF a partir del JSON que arma el backend
 * (GET /api/reportes/{seccion}?formato=json). El backend define columnas,
 * totales e indicadores; aquí solo se maqueta el documento.
 */

const TIPOS_NUMERICOS = new Set(['entero', 'decimal', 'moneda'])

// Paleta alineada con tokens.css ("ficha de catálogo").
const ACENTO = [44, 62, 88]
const TINTA = [32, 31, 36]
const TENUE = [109, 106, 97]
const BORDE = [212, 207, 192]
const PANEL = [242, 240, 234]
const PAPEL = [250, 249, 246]

const enteros = new Intl.NumberFormat('es-GT')
const decimales = new Intl.NumberFormat('es-GT', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

// Las fechas llegan como ISO sin zona ("2026-09-15T10:30:00"): se leen por
// partes para que no se desplacen de día al interpretarse como UTC.
function formatearFecha(valor, conHora) {
  const partes = String(valor).match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/)
  if (!partes) return String(valor)
  const [, anio, mes, dia, hora, minuto] = partes
  const fecha = `${dia}/${mes}/${anio}`
  return conHora && hora ? `${fecha} ${hora}:${minuto}` : fecha
}

export function formatearValor(valor, tipo) {
  if (valor === null || valor === undefined || valor === '') return ''
  switch (tipo) {
    case 'entero':
      return enteros.format(Number(valor))
    case 'decimal':
      return decimales.format(Number(valor))
    case 'moneda':
      return 'Q' + decimales.format(Number(valor))
    case 'fecha':
      return formatearFecha(valor, false)
    case 'fechahora':
      return formatearFecha(valor, true)
    default:
      return String(valor)
  }
}

export function marcaDeTiempo(fecha = new Date()) {
  const dosDigitos = (n) => String(n).padStart(2, '0')
  return (
    `${fecha.getFullYear()}${dosDigitos(fecha.getMonth() + 1)}${dosDigitos(fecha.getDate())}_` +
    `${dosDigitos(fecha.getHours())}${dosDigitos(fecha.getMinutes())}`
  )
}

export function descargarArchivo(blob, nombre) {
  const url = window.URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  document.body.appendChild(enlace)
  enlace.click()
  document.body.removeChild(enlace)
  window.URL.revokeObjectURL(url)
}

function dibujarEncabezado(doc, reporte, margen, ancho) {
  let y = margen + 2

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...TENUE)
  doc.text('BIBLIOTECA · REPORTE', margen, y)

  y += 8
  doc.setFont('times', 'bold')
  doc.setFontSize(20)
  doc.setTextColor(...ACENTO)
  doc.text(reporte.titulo, margen, y)

  if (reporte.subtitulo) {
    y += 6
    doc.setFont('helvetica', 'italic')
    doc.setFontSize(9.5)
    doc.setTextColor(...TENUE)
    const lineas = doc.splitTextToSize(reporte.subtitulo, ancho - margen * 2)
    doc.text(lineas, margen, y)
    y += (lineas.length - 1) * 4.2
  }

  y += 5.5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(...TINTA)
  doc.text(
    `Generado el ${formatearValor(reporte.generado_en, 'fechahora')} por ${reporte.generado_por}`,
    margen,
    y
  )

  y += 3.5
  doc.setDrawColor(...ACENTO)
  doc.setLineWidth(0.6)
  doc.line(margen, y, ancho - margen, y)
  y += 6

  const filtros = reporte.filtros.length
    ? reporte.filtros.map((f) => `${f.etiqueta}: ${f.valor}`).join('   ·   ')
    : 'Sin filtros adicionales'
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8.5)
  doc.text('Filtros aplicados', margen, y)
  doc.setFont('helvetica', 'normal')
  const lineasFiltros = doc.splitTextToSize(filtros, ancho - margen * 2 - 30)
  doc.text(lineasFiltros, margen + 30, y)
  y += lineasFiltros.length * 4 + 3

  return y
}

function dibujarIndicadores(doc, indicadores, y, margen, ancho, columnas) {
  if (!indicadores.length) return y
  const separacion = 3
  const anchoCaja = (ancho - margen * 2 - separacion * (columnas - 1)) / columnas
  const altoCaja = 15

  indicadores.forEach((indicador, i) => {
    const x = margen + (i % columnas) * (anchoCaja + separacion)
    const yCaja = y + Math.floor(i / columnas) * (altoCaja + separacion)

    doc.setFillColor(...PANEL)
    doc.setDrawColor(...BORDE)
    doc.setLineWidth(0.2)
    doc.rect(x, yCaja, anchoCaja, altoCaja, 'FD')
    doc.setFillColor(...ACENTO)
    doc.rect(x, yCaja, 0.9, altoCaja, 'F')

    // La etiqueta se achica hasta caber en la caja en vez de cortarse.
    const etiqueta = indicador.etiqueta.toUpperCase()
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(...TENUE)
    let tamano = 7
    doc.setFontSize(tamano)
    while (tamano > 5 && doc.getTextWidth(etiqueta) > anchoCaja - 6) {
      tamano -= 0.25
      doc.setFontSize(tamano)
    }
    doc.text(doc.splitTextToSize(etiqueta, anchoCaja - 6)[0], x + 3.5, yCaja + 5)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12.5)
    doc.setTextColor(...TINTA)
    doc.text(formatearValor(indicador.valor, indicador.tipo), x + 3.5, yCaja + 11.5)
  })

  const filas = Math.ceil(indicadores.length / columnas)
  return y + filas * (altoCaja + separacion) + 4
}

function dibujarPies(doc, reporte, margen, ancho, alto) {
  const total = doc.getNumberOfPages()
  for (let pagina = 1; pagina <= total; pagina++) {
    doc.setPage(pagina)
    doc.setDrawColor(...BORDE)
    doc.setLineWidth(0.2)
    doc.line(margen, alto - 11, ancho - margen, alto - 11)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.5)
    doc.setTextColor(...TENUE)
    doc.text(`Biblioteca · ${reporte.titulo}`, margen, alto - 7)
    doc.text(`Página ${pagina} de ${total}`, ancho - margen, alto - 7, { align: 'right' })
  }
}

export async function generarPdf(reporte) {
  // Carga diferida: jsPDF solo se descarga cuando alguien pide un PDF.
  const [{ jsPDF }, { autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')])

  const maxColumnas = Math.max(0, ...reporte.tablas.map((t) => t.columnas.length))
  const horizontal = maxColumnas > 6
  const doc = new jsPDF({ orientation: horizontal ? 'landscape' : 'portrait', unit: 'mm', format: 'letter' })
  doc.setProperties({ title: reporte.titulo, author: reporte.generado_por, creator: 'Biblioteca' })

  const ancho = doc.internal.pageSize.getWidth()
  const alto = doc.internal.pageSize.getHeight()
  const margen = 14

  let y = dibujarEncabezado(doc, reporte, margen, ancho)
  y = dibujarIndicadores(doc, reporte.indicadores, y, margen, ancho, horizontal ? 4 : 3)

  if (reporte.notas.length) {
    doc.setFont('helvetica', 'italic')
    doc.setFontSize(8)
    doc.setTextColor(...TENUE)
    reporte.notas.forEach((nota) => {
      const lineas = doc.splitTextToSize(nota, ancho - margen * 2)
      doc.text(lineas, margen, y)
      y += lineas.length * 4
    })
    y += 3
  }

  reporte.tablas.forEach((tabla) => {
    if (y > alto - 45) {
      doc.addPage()
      y = margen + 4
    }

    doc.setFont('times', 'bold')
    doc.setFontSize(13)
    doc.setTextColor(...ACENTO)
    doc.text(tabla.titulo, margen, y)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(...TENUE)
    doc.text(`${enteros.format(tabla.filas.length)} registro(s)`, ancho - margen, y, { align: 'right' })

    const columnas = tabla.columnas
    const body = tabla.filas.length
      ? tabla.filas.map((fila) => columnas.map((c) => formatearValor(fila[c.clave], c.tipo)))
      : [[{
          content: 'Sin registros para los filtros aplicados',
          colSpan: columnas.length,
          styles: { halign: 'center', fontStyle: 'italic', textColor: TENUE }
        }]]
    const foot = tabla.totales
      ? [columnas.map((c, i) =>
          c.clave in tabla.totales ? formatearValor(tabla.totales[c.clave], c.tipo) : i === 0 ? 'Total' : ''
        )]
      : undefined

    autoTable(doc, {
      startY: y + 2.5,
      margin: { left: margen, right: margen, top: margen + 4, bottom: 16 },
      head: [columnas.map((c) => c.titulo)],
      body,
      foot,
      showHead: 'everyPage',
      showFoot: 'lastPage',
      theme: 'plain',
      styles: {
        font: 'helvetica',
        fontSize: 8,
        cellPadding: { top: 1.8, bottom: 1.8, left: 2, right: 2 },
        textColor: TINTA,
        lineColor: BORDE,
        lineWidth: { bottom: 0.15 },
        overflow: 'linebreak'
      },
      // Borde del mismo color que el relleno: evita las costuras blancas entre celdas.
      headStyles: { fillColor: ACENTO, textColor: 255, fontStyle: 'bold', lineColor: ACENTO, lineWidth: 0.1 },
      footStyles: { fillColor: PANEL, fontStyle: 'bold', lineColor: ACENTO, lineWidth: { top: 0.4 } },
      alternateRowStyles: { fillColor: PAPEL },
      didParseCell: (data) => {
        if (data.cell.colSpan === 1 && TIPOS_NUMERICOS.has(columnas[data.column.index]?.tipo)) {
          data.cell.styles.halign = 'right'
        }
      }
    })

    y = doc.lastAutoTable.finalY + 10
  })

  dibujarPies(doc, reporte, margen, ancho, alto)

  const marca = reporte.generado_en.slice(0, 16).replace(/[-:]/g, '').replace('T', '_')
  doc.save(`reporte_${reporte.seccion}_${marca}.pdf`)
}
