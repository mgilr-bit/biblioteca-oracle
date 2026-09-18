"""DTOs de los reportes por sección.

Un reporte es un documento autodescriptivo: metadatos (quién/cuándo),
filtros aplicados, indicadores de resumen y una o más tablas con columnas
tipadas. El mismo objeto alimenta los tres formatos de salida — JSON (que
la SPA convierte en PDF), XLSX y CSV — así las columnas y totales se
definen una sola vez, en el backend.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

TipoDato = Literal["texto", "entero", "decimal", "moneda", "fecha", "fechahora"]
FormatoReporte = Literal["json", "xlsx", "csv"]


class ReporteColumna(BaseModel):
    clave: str
    titulo: str
    tipo: TipoDato = "texto"
    #: Si es True, la tabla incluye una fila de totales con la suma de esta columna.
    sumar: bool = False


class ReporteTabla(BaseModel):
    titulo: str
    columnas: list[ReporteColumna]
    filas: list[dict[str, Any]]
    totales: Optional[dict[str, Any]] = None


class ReporteIndicador(BaseModel):
    etiqueta: str
    valor: Any
    tipo: TipoDato = "entero"


class ReporteFiltro(BaseModel):
    etiqueta: str
    valor: str


class ReporteResponse(BaseModel):
    seccion: str
    titulo: str
    subtitulo: Optional[str] = None
    generado_en: datetime
    generado_por: str
    filtros: list[ReporteFiltro] = Field(default_factory=list)
    indicadores: list[ReporteIndicador] = Field(default_factory=list)
    tablas: list[ReporteTabla] = Field(default_factory=list)
    notas: list[str] = Field(default_factory=list)

    @property
    def total_filas(self) -> int:
        return sum(len(tabla.filas) for tabla in self.tablas)


def construir_tabla(titulo: str, columnas: list[ReporteColumna], filas: list[dict]) -> ReporteTabla:
    """Arma la tabla y calcula la fila de totales de las columnas `sumar`."""
    totales = None
    if filas and any(c.sumar for c in columnas):
        totales = {}
        for columna in columnas:
            if columna.sumar:
                total = sum((Decimal(str(f.get(columna.clave) or 0)) for f in filas), Decimal(0))
                totales[columna.clave] = int(total) if columna.tipo == "entero" else float(total)
    return ReporteTabla(titulo=titulo, columnas=columnas, filas=filas, totales=totales)
