"""Construcción de los reportes de cada sección de la aplicación.

Cada método devuelve un `ReporteResponse` (ver schemas/reporte.py) que
después se entrega como JSON, XLSX o CSV (utils/reporte_export.py). Los
reportes reutilizan los mismos servicios/repositorios que las pantallas,
así los números coinciden con lo que el usuario ve.

El alcance lo decide el router (`ver_todo`): un BIBLIOTECARIO/ADMIN obtiene
los registros de todos los usuarios y un LECTOR/PROFESOR solo los propios,
igual que en las vistas.
"""
import math
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from core.sessions import SessionUser
from repositories.auditoria_repository import AuditoriaRepository
from repositories.editorial_repository import EditorialRepository
from repositories.ejemplar_repository import EjemplarRepository
from repositories.libro_repository import LibroRepository
from repositories.usuario_repository import UsuarioRepository
from schemas.reporte import (
    ReporteColumna,
    ReporteFiltro,
    ReporteIndicador,
    ReporteResponse,
    construir_tabla,
)
from services.analytics_service import AnalyticsService
from services.ejemplar_service import EJEMPLAR_ESTADOS
from services.multa_service import MultaService
from services.notificacion_service import NotificacionService
from services.prestamo_service import PrestamoService
from services.reserva_service import ReservaService

#: Tope de filas por reporte, para no agotar memoria con tablas históricas.
LIMITE_FILAS = 10_000
#: Umbral de "bajo stock", el mismo que usa GET /libros/bajo-stock.
UMBRAL_BAJO_STOCK = 2
DIAS_POR_VENCER = 3

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ESTADOS_RESERVA = ("ACTIVA", "CUMPLIDA", "CANCELADA", "EXPIRADA")
ROLES = ("ADMIN", "BIBLIOTECARIO", "PROFESOR", "LECTOR")
VISTAS_PRESTAMO = {"todos": "Todos", "activos": "Activos (incluye vencidos)", "vencidos": "Vencidos"}
TIPOS_NOTIFICACION = {
    "RECORDATORIO_HOY": "Recordatorio",
    "RECORDATORIO_3D": "Recordatorio",
    "VENCIDO": "Vencimiento",
    "RESERVA_DISPONIBLE": "Reserva disponible",
    "MULTA": "Multa",
    "SISTEMA": "Sistema",
}


def _col(clave: str, titulo: str, tipo: str = "texto", sumar: bool = False) -> ReporteColumna:
    return ReporteColumna(clave=clave, titulo=titulo, tipo=tipo, sumar=sumar)


def _ind(etiqueta: str, valor, tipo: str = "entero") -> ReporteIndicador:
    return ReporteIndicador(etiqueta=etiqueta, valor=valor, tipo=tipo)


def _filtros(*pares) -> list[ReporteFiltro]:
    """Solo los filtros con valor, en el orden recibido."""
    return [ReporteFiltro(etiqueta=etiqueta, valor=str(valor)) for etiqueta, valor in pares if valor]


def _contiene(texto: Optional[str], patron: str) -> bool:
    return patron.lower() in (texto or "").lower()


def _suma(valores) -> float:
    return float(sum((Decimal(str(v or 0)) for v in valores), Decimal(0)))


def _truncar(registros: list, notas: list[str]) -> list:
    if len(registros) > LIMITE_FILAS:
        notas.append(f"El reporte se limitó a los primeros {LIMITE_FILAS:,} registros.")
        return registros[:LIMITE_FILAS]
    return registros


def _dias_retraso(prestamo, ahora: datetime) -> int:
    esperada = prestamo.fecha_devolucion_esperada
    if not esperada:
        return 0
    if prestamo.estado == "VENCIDO":
        return max((ahora - esperada).days, 0)
    if prestamo.fecha_devolucion_real and prestamo.fecha_devolucion_real > esperada:
        return (prestamo.fecha_devolucion_real - esperada).days
    return 0


def _dias_restantes(esperada: Optional[datetime], ahora: datetime) -> Optional[int]:
    if not esperada:
        return None
    return math.ceil((esperada - ahora).total_seconds() / 86_400)


class ReporteService:
    def __init__(self, session):
        self.session = session

    def _reporte(self, seccion: str, titulo: str, usuario: SessionUser, **datos) -> ReporteResponse:
        return ReporteResponse(
            seccion=seccion,
            titulo=titulo,
            generado_en=datetime.now(),
            generado_por=f"{usuario.nombre} ({usuario.email})",
            **datos,
        )

    # --- Catálogo -----------------------------------------------------------

    def libros(self, usuario: SessionUser, titulo: str = "", autor: str = "", isbn: str = "", genero: str = "") -> ReporteResponse:
        notas: list[str] = []
        libros = _truncar(
            LibroRepository(self.session).search(
                titulo=titulo, autor=autor, isbn=isbn, genero=genero, limit=LIMITE_FILAS + 1
            ),
            notas,
        )

        filas = [
            {
                "id_libro": l.id_libro,
                "titulo": l.titulo,
                "autor": l.autor,
                "isbn": l.isbn,
                "anio_publicacion": l.anio_publicacion,
                "genero": l.genero,
                "editorial": l.editorial,
                "numero_copias": l.numero_copias,
                "copias_disponibles": l.copias_disponibles,
                "copias_prestadas": max((l.numero_copias or 0) - (l.copias_disponibles or 0), 0),
                "fecha_registro": l.fecha_registro,
            }
            for l in libros
        ]

        por_genero: dict[str, dict] = {}
        for fila in filas:
            grupo = por_genero.setdefault(
                fila["genero"] or "Sin género",
                {"genero": fila["genero"] or "Sin género", "titulos": 0, "copias": 0, "disponibles": 0},
            )
            grupo["titulos"] += 1
            grupo["copias"] += fila["numero_copias"] or 0
            grupo["disponibles"] += fila["copias_disponibles"] or 0

        return self._reporte(
            "libros",
            "Reporte de libros",
            usuario,
            subtitulo="Catálogo de títulos con existencias y disponibilidad",
            filtros=_filtros(
                ("Título contiene", titulo), ("Autor contiene", autor), ("ISBN contiene", isbn), ("Género", genero)
            ),
            indicadores=[
                _ind("Títulos", len(filas)),
                _ind("Copias totales", sum(f["numero_copias"] or 0 for f in filas)),
                _ind("Copias disponibles", sum(f["copias_disponibles"] or 0 for f in filas)),
                _ind("Copias prestadas", sum(f["copias_prestadas"] for f in filas)),
                _ind("Títulos sin copias disponibles", sum(1 for f in filas if not f["copias_disponibles"])),
                _ind(
                    f"Títulos con bajo stock (< {UMBRAL_BAJO_STOCK} disponibles)",
                    sum(1 for f in filas if (f["copias_disponibles"] or 0) < UMBRAL_BAJO_STOCK),
                ),
            ],
            tablas=[
                construir_tabla(
                    "Libros",
                    [
                        _col("id_libro", "ID"),
                        _col("titulo", "Título"),
                        _col("autor", "Autor"),
                        _col("isbn", "ISBN"),
                        _col("anio_publicacion", "Año"),
                        _col("genero", "Género"),
                        _col("editorial", "Editorial"),
                        _col("numero_copias", "Copias", "entero", sumar=True),
                        _col("copias_disponibles", "Disponibles", "entero", sumar=True),
                        _col("copias_prestadas", "Prestadas", "entero", sumar=True),
                        _col("fecha_registro", "Registrado", "fecha"),
                    ],
                    filas,
                ),
                construir_tabla(
                    "Resumen por género",
                    [
                        _col("genero", "Género"),
                        _col("titulos", "Títulos", "entero", sumar=True),
                        _col("copias", "Copias", "entero", sumar=True),
                        _col("disponibles", "Disponibles", "entero", sumar=True),
                    ],
                    sorted(por_genero.values(), key=lambda g: (-g["titulos"], g["genero"])),
                ),
            ],
            notas=notas,
        )

    def editoriales(self, usuario: SessionUser) -> ReporteResponse:
        repositorio = EditorialRepository(self.session)
        conteo = repositorio.contar_libros_por_editorial()
        filas = [
            {
                "id_editorial": e.id_editorial,
                "nombre": e.nombre,
                "pais": e.pais,
                "sitio_web": e.sitio_web,
                "libros": conteo.get(e.id_editorial, 0),
            }
            for e in repositorio.get_ordered_by_nombre()
        ]
        return self._reporte(
            "editoriales",
            "Reporte de editoriales",
            usuario,
            subtitulo="Catálogo de editoriales y libros vinculados a cada una",
            indicadores=[
                _ind("Editoriales", len(filas)),
                _ind("Países distintos", len({f["pais"].strip().lower() for f in filas if f["pais"]})),
                _ind("Libros vinculados", sum(f["libros"] for f in filas)),
                _ind("Editoriales sin libros", sum(1 for f in filas if not f["libros"])),
            ],
            tablas=[
                construir_tabla(
                    "Editoriales",
                    [
                        _col("id_editorial", "ID"),
                        _col("nombre", "Nombre"),
                        _col("pais", "País"),
                        _col("sitio_web", "Sitio web"),
                        _col("libros", "Libros", "entero", sumar=True),
                    ],
                    filas,
                )
            ],
        )

    def ejemplares(self, usuario: SessionUser, id_libro: Optional[int] = None, estado: str = "") -> ReporteResponse:
        estado = estado.upper().strip()
        notas: list[str] = []
        titulo_libro = None
        if id_libro:
            libro = LibroRepository(self.session).get_by_id(id_libro)
            titulo_libro = f"{libro.titulo} (#{id_libro})" if libro else f"#{id_libro}"

        registros = _truncar(
            EjemplarRepository(self.session).get_paginated_with_details(
                0, LIMITE_FILAS + 1, id_libro=id_libro, estado=estado or None
            ),
            notas,
        )
        filas = [
            {
                "codigo_ejemplar": ejemplar.codigo_ejemplar,
                "titulo": titulo,
                "id_libro": ejemplar.id_libro,
                "estado": ejemplar.estado,
                "ubicacion": ejemplar.ubicacion,
                "fecha_adquisicion": ejemplar.fecha_adquisicion,
            }
            for ejemplar, titulo in registros
        ]
        por_estado = Counter(f["estado"] for f in filas)

        return self._reporte(
            "ejemplares",
            "Reporte de ejemplares",
            usuario,
            subtitulo="Copias físicas por libro, con su estado y ubicación",
            filtros=_filtros(("Libro", titulo_libro), ("Estado", estado)),
            indicadores=[_ind("Ejemplares", len(filas))]
            + [_ind(f"En estado {e}", por_estado[e]) for e in EJEMPLAR_ESTADOS if por_estado[e]],
            tablas=[
                construir_tabla(
                    "Ejemplares",
                    [
                        _col("codigo_ejemplar", "Código"),
                        _col("titulo", "Libro"),
                        _col("id_libro", "ID libro"),
                        _col("estado", "Estado"),
                        _col("ubicacion", "Ubicación"),
                        _col("fecha_adquisicion", "Adquirido", "fecha"),
                    ],
                    filas,
                )
            ],
            notas=notas,
        )

    # --- Circulación --------------------------------------------------------

    def reservas(self, usuario: SessionUser, ver_todo: bool, estado: str = "") -> ReporteResponse:
        estado = estado.upper().strip()
        servicio = ReservaService(self.session)
        reservas = servicio.get_all() if ver_todo else servicio.get_by_usuario(usuario.id)
        if estado:
            reservas = [r for r in reservas if r.estado == estado]
        notas: list[str] = []
        reservas = _truncar(reservas, notas)

        columnas = [_col("id_reserva", "ID"), _col("titulo", "Libro"), _col("autor", "Autor")]
        if ver_todo:
            columnas.append(_col("nombre_usuario", "Usuario"))
        columnas += [
            _col("fecha_reserva", "Reservado", "fechahora"),
            _col("fecha_expiracion", "Expira", "fecha"),
            _col("estado", "Estado"),
        ]
        por_estado = Counter(r.estado for r in reservas)

        return self._reporte(
            "reservas",
            "Reporte de reservas" if ver_todo else "Mis reservas",
            usuario,
            subtitulo="Reservas de todos los usuarios" if ver_todo else "Reservas a nombre del usuario en sesión",
            filtros=_filtros(("Estado", estado)),
            indicadores=[_ind("Reservas", len(reservas))]
            + [_ind(f"{e.capitalize()}s", por_estado[e]) for e in ESTADOS_RESERVA],
            tablas=[construir_tabla("Reservas", columnas, [r.model_dump() for r in reservas])],
            notas=notas,
        )

    def prestamos(
        self,
        usuario: SessionUser,
        ver_todo: bool,
        vista: str = "todos",
        fecha_prestamo: Optional[date] = None,
        fecha_devolucion: Optional[date] = None,
        libro: str = "",
    ) -> ReporteResponse:
        servicio = PrestamoService(self.session)
        prestamos = servicio.get_all() if ver_todo else servicio.get_by_usuario(usuario.id)

        if vista == "activos":
            prestamos = [p for p in prestamos if p.estado in ("ACTIVO", "VENCIDO")]
        elif vista == "vencidos":
            prestamos = [p for p in prestamos if p.estado == "VENCIDO"]
        if fecha_prestamo:
            prestamos = [p for p in prestamos if p.fecha_prestamo and p.fecha_prestamo.date() == fecha_prestamo]
        if fecha_devolucion:
            prestamos = [
                p for p in prestamos
                if p.fecha_devolucion_esperada and p.fecha_devolucion_esperada.date() == fecha_devolucion
            ]
        if libro:
            prestamos = [p for p in prestamos if _contiene(p.titulo, libro)]
        notas: list[str] = []
        prestamos = _truncar(prestamos, notas)

        ahora = datetime.now()
        filas = [p.model_dump() | {"dias_retraso": _dias_retraso(p, ahora)} for p in prestamos]

        columnas = [_col("id_prestamo", "ID"), _col("titulo", "Libro"), _col("autor", "Autor")]
        if ver_todo:
            columnas.append(_col("nombre_usuario", "Usuario"))
        columnas += [
            _col("codigo_ejemplar", "Ejemplar"),
            _col("fecha_prestamo", "Prestado", "fecha"),
            _col("fecha_devolucion_esperada", "Devolución esperada", "fecha"),
            _col("fecha_devolucion_real", "Devuelto", "fecha"),
            _col("estado", "Estado"),
            _col("dias_retraso", "Días de retraso", "entero"),
        ]
        por_estado = Counter(p.estado for p in prestamos)

        return self._reporte(
            "prestamos",
            "Reporte de préstamos" if ver_todo else "Mis préstamos",
            usuario,
            subtitulo="Préstamos de todos los usuarios" if ver_todo else "Préstamos a nombre del usuario en sesión",
            filtros=_filtros(
                ("Vista", VISTAS_PRESTAMO.get(vista) if vista != "todos" else None),
                ("Fecha de préstamo", fecha_prestamo and fecha_prestamo.strftime("%d/%m/%Y")),
                ("Fecha de devolución esperada", fecha_devolucion and fecha_devolucion.strftime("%d/%m/%Y")),
                ("Libro contiene", libro),
            ),
            indicadores=[
                _ind("Préstamos", len(prestamos)),
                _ind("Activos al día", por_estado["ACTIVO"]),
                _ind("Vencidos", por_estado["VENCIDO"]),
                _ind("Devueltos", por_estado["DEVUELTO"]),
                _ind(
                    "Devoluciones con retraso",
                    sum(1 for f in filas if f["estado"] == "DEVUELTO" and f["dias_retraso"] > 0),
                ),
            ],
            tablas=[construir_tabla("Préstamos", columnas, filas)],
            notas=notas,
        )

    def multas(self, usuario: SessionUser, ver_todo: bool, vista: str = "todas") -> ReporteResponse:
        servicio = MultaService(self.session)
        if not ver_todo:
            multas = servicio.get_by_usuario(usuario.id)
        elif vista == "pendientes":
            multas = servicio.get_pendientes()
        else:
            multas = servicio.get_all()
        notas: list[str] = []
        multas = _truncar(multas, notas)

        def total(estado: Optional[str] = None) -> float:
            return _suma(m.monto for m in multas if estado is None or m.estado == estado)

        columnas = [_col("id_multa", "ID"), _col("id_prestamo", "Préstamo"), _col("titulo", "Libro")]
        if ver_todo:
            columnas.append(_col("nombre_usuario", "Usuario"))
        columnas += [
            _col("motivo", "Motivo"),
            _col("dias_retraso", "Días de retraso", "entero"),
            _col("fecha_generacion", "Generada", "fecha"),
            _col("fecha_pago", "Pagada", "fecha"),
            _col("estado", "Estado"),
            _col("monto", "Monto", "moneda", sumar=True),
        ]

        return self._reporte(
            "multas",
            "Reporte de multas" if ver_todo else "Mis multas",
            usuario,
            subtitulo="Multas por devolución tardía" + ("" if ver_todo else " del usuario en sesión"),
            filtros=_filtros(("Vista", "Solo pendientes" if ver_todo and vista == "pendientes" else None)),
            indicadores=[
                _ind("Multas", len(multas)),
                _ind("Pendientes", sum(1 for m in multas if m.estado == "PENDIENTE")),
                _ind("Monto total", total(), "moneda"),
                _ind("Pendiente de cobro", total("PENDIENTE"), "moneda"),
                _ind("Recaudado", total("PAGADA"), "moneda"),
                _ind("Condonado", total("CONDONADA"), "moneda"),
            ],
            tablas=[construir_tabla("Multas", columnas, [m.model_dump() for m in multas])],
            notas=notas,
        )

    # --- Administración -----------------------------------------------------

    def usuarios(self, usuario: SessionUser, nombre: str = "", rol: str = "", estado: str = "") -> ReporteResponse:
        rol, estado = rol.upper().strip(), estado.upper().strip()
        usuarios = UsuarioRepository(self.session).get_all()
        if nombre:
            usuarios = [u for u in usuarios if _contiene(u.nombre, nombre) or _contiene(u.email, nombre)]
        if rol:
            usuarios = [u for u in usuarios if u.rol == rol]
        if estado:
            usuarios = [u for u in usuarios if u.activo == estado]

        filas = [
            {
                "id_usuario": u.id_usuario,
                "nombre": u.nombre,
                "email": u.email,
                "rol": u.rol,
                "estado": "Activo" if u.activo == "S" else "Inactivo",
                "fecha_registro": u.fecha_registro,
            }
            for u in usuarios
        ]
        por_rol = Counter(f["rol"] for f in filas)

        return self._reporte(
            "usuarios",
            "Reporte de usuarios",
            usuario,
            subtitulo="Cuentas registradas en el sistema (sin credenciales)",
            filtros=_filtros(
                ("Nombre o email contiene", nombre),
                ("Rol", rol),
                ("Estado", {"S": "Activos", "N": "Inactivos"}.get(estado)),
            ),
            indicadores=[
                _ind("Usuarios", len(filas)),
                _ind("Activos", sum(1 for f in filas if f["estado"] == "Activo")),
                _ind("Inactivos", sum(1 for f in filas if f["estado"] == "Inactivo")),
            ]
            + [_ind(f"Rol {r}", por_rol[r]) for r in ROLES if por_rol[r]],
            tablas=[
                construir_tabla(
                    "Usuarios",
                    [
                        _col("id_usuario", "ID"),
                        _col("nombre", "Nombre"),
                        _col("email", "Email"),
                        _col("rol", "Rol"),
                        _col("estado", "Estado"),
                        _col("fecha_registro", "Registrado", "fecha"),
                    ],
                    filas,
                )
            ],
        )

    def auditoria(self, usuario: SessionUser, accion: str = "", recurso: str = "") -> ReporteResponse:
        repositorio = AuditoriaRepository(self.session)
        total = repositorio.count(accion=accion or None, recurso=recurso or None)
        registros = repositorio.search(0, LIMITE_FILAS, accion=accion or None, recurso=recurso or None)
        notas = []
        if total > len(registros):
            notas.append(
                f"Hay {total:,} eventos que coinciden; el reporte incluye los {len(registros):,} más recientes."
            )

        filas = [
            {
                "id_auditoria": r.id_auditoria,
                "fecha": r.created_at,
                "accion": r.accion,
                "recurso": r.recurso,
                "id_recurso": r.id_recurso,
                "email": r.email,
                "rol": r.rol,
                "detalle": r.detalle,
            }
            for r in registros
        ]
        por_accion = Counter(f["accion"] for f in filas)

        return self._reporte(
            "auditoria",
            "Reporte de auditoría",
            usuario,
            subtitulo="Bitácora de eventos clave del sistema, del más reciente al más antiguo",
            filtros=_filtros(("Acción", accion), ("Recurso", recurso)),
            indicadores=[
                _ind("Eventos que coinciden", total),
                _ind("Eventos incluidos", len(filas)),
                _ind("Usuarios distintos", len({f["email"] for f in filas if f["email"]})),
                _ind("Inicios de sesión fallidos", por_accion["LOGIN_FALLIDO"]),
            ],
            tablas=[
                construir_tabla(
                    "Eventos",
                    [
                        _col("id_auditoria", "ID"),
                        _col("fecha", "Fecha", "fechahora"),
                        _col("accion", "Acción"),
                        _col("recurso", "Recurso"),
                        _col("id_recurso", "ID recurso"),
                        _col("email", "Usuario"),
                        _col("rol", "Rol"),
                        _col("detalle", "Detalle"),
                    ],
                    filas,
                ),
                construir_tabla(
                    "Resumen por acción",
                    [_col("accion", "Acción"), _col("eventos", "Eventos", "entero", sumar=True)],
                    [{"accion": a, "eventos": n} for a, n in por_accion.most_common()],
                ),
            ],
            notas=notas,
        )

    def notificaciones(self, usuario: SessionUser) -> ReporteResponse:
        notificaciones = NotificacionService(self.session).get_mis_notificaciones(usuario.id, limit=LIMITE_FILAS)
        filas = [
            {
                "fecha_generacion": n.fecha_generacion,
                "tipo": TIPOS_NOTIFICACION.get(n.tipo, n.tipo),
                "mensaje": n.mensaje,
                "estado": "Leída" if n.leida else "No leída",
            }
            for n in notificaciones
        ]
        no_leidas = sum(1 for n in notificaciones if not n.leida)

        return self._reporte(
            "notificaciones",
            "Mis notificaciones",
            usuario,
            subtitulo="Recordatorios de devolución, vencimientos y avisos del sistema",
            indicadores=[
                _ind("Notificaciones", len(filas)),
                _ind("No leídas", no_leidas),
                _ind("Leídas", len(filas) - no_leidas),
            ],
            tablas=[
                construir_tabla(
                    "Notificaciones",
                    [
                        _col("fecha_generacion", "Fecha", "fechahora"),
                        _col("tipo", "Tipo"),
                        _col("mensaje", "Mensaje"),
                        _col("estado", "Estado"),
                    ],
                    filas,
                )
            ],
        )

    # --- Tableros -----------------------------------------------------------

    def analitica(self, usuario: SessionUser) -> ReporteResponse:
        resumen = AnalyticsService(self.session).resumen()
        totales = resumen["totales"]

        def mes(fila: dict) -> str:
            indice = int(fila["mes"]) - 1
            return f"{MESES[indice] if 0 <= indice < 12 else fila['mes']} {fila['anio']}"

        prestamos_mes = [f | {"periodo": mes(f)} for f in resumen["prestamos_mensual"]]
        multas_mes = [f | {"periodo": mes(f)} for f in resumen["multas_mensual"]]
        top = [f | {"posicion": i} for i, f in enumerate(resumen["top_libros"], start=1)]

        return self._reporte(
            "analitica",
            "Reporte analítico",
            usuario,
            subtitulo="Métricas OLAP de circulación y multas de los últimos 12 meses",
            indicadores=[
                _ind("Préstamos activos", totales["prestamos_activos"]),
                _ind("Copias disponibles", totales["copias_disponibles"]),
                _ind("Usuarios activos", totales["usuarios_activos"]),
                _ind("Multas pendientes", totales["multas_pendientes"]),
                _ind("Deuda pendiente", totales["deuda_pendiente"], "moneda"),
                _ind("Préstamos (12 meses)", sum(f["total_prestamos"] for f in prestamos_mes)),
                _ind("Multas generadas (12 meses)", _suma(f["monto_generado"] for f in multas_mes), "moneda"),
                _ind("Multas recaudadas (12 meses)", _suma(f["monto_recaudado"] for f in multas_mes), "moneda"),
            ],
            tablas=[
                construir_tabla(
                    "Préstamos por mes",
                    [
                        _col("periodo", "Mes"),
                        _col("total_prestamos", "Totales", "entero", sumar=True),
                        _col("devueltos", "Devueltos", "entero", sumar=True),
                        _col("activos", "Activos", "entero", sumar=True),
                        _col("vencidos", "Vencidos", "entero", sumar=True),
                    ],
                    prestamos_mes,
                ),
                construir_tabla(
                    "Top libros prestados",
                    [
                        _col("posicion", "#"),
                        _col("titulo", "Título"),
                        _col("autor", "Autor"),
                        _col("total_prestamos", "Préstamos", "entero"),
                    ],
                    top,
                ),
                construir_tabla(
                    "Préstamos por género",
                    [_col("genero", "Género"), _col("total_prestamos", "Préstamos", "entero", sumar=True)],
                    resumen["prestamos_por_genero"],
                ),
                construir_tabla(
                    "Multas por mes",
                    [
                        _col("periodo", "Mes"),
                        _col("monto_generado", "Generado", "moneda", sumar=True),
                        _col("monto_recaudado", "Recaudado", "moneda", sumar=True),
                        _col("pendientes", "Pendientes", "entero", sumar=True),
                    ],
                    multas_mes,
                ),
            ],
            notas=["Fuente: vistas materializadas OLAP con refresco diario; pueden no reflejar movimientos de hoy."],
        )

    def dashboard(self, usuario: SessionUser, ver_todo: bool) -> ReporteResponse:
        ahora = datetime.now()
        prestamo_service = PrestamoService(self.session)
        multa_service = MultaService(self.session)

        def fila_prestamo(p) -> dict:
            return p.model_dump() | {"dias_restantes": _dias_restantes(p.fecha_devolucion_esperada, ahora)}

        columnas_multa = [
            _col("id_multa", "ID"),
            _col("titulo", "Libro"),
            _col("fecha_generacion", "Generada", "fecha"),
            _col("dias_retraso", "Días de retraso", "entero"),
            _col("monto", "Monto", "moneda", sumar=True),
        ]

        if ver_todo:
            libros_repo = LibroRepository(self.session)
            estadisticas = libros_repo.get_estadisticas()
            activos = prestamo_service.get_activos()
            bajo_stock = libros_repo.get_bajo_stock()
            multas = multa_service.get_pendientes()
            return self._reporte(
                "dashboard",
                "Resumen general de la biblioteca",
                usuario,
                subtitulo="Estado actual del catálogo, la circulación y las multas por cobrar",
                indicadores=[
                    _ind("Títulos en catálogo", estadisticas["total_libros"]),
                    _ind("Copias totales", estadisticas["total_copias"]),
                    _ind("Copias disponibles", estadisticas["total_disponibles"]),
                    _ind("Préstamos activos", len(activos)),
                    _ind("Préstamos vencidos", sum(1 for p in activos if p.estado == "VENCIDO")),
                    _ind("Libros con bajo stock", len(bajo_stock)),
                    _ind("Multas pendientes", len(multas)),
                    _ind("Monto por cobrar", _suma(m.monto for m in multas), "moneda"),
                ],
                tablas=[
                    construir_tabla(
                        "Préstamos activos",
                        [
                            _col("id_prestamo", "ID"),
                            _col("titulo", "Libro"),
                            _col("nombre_usuario", "Usuario"),
                            _col("fecha_prestamo", "Prestado", "fecha"),
                            _col("fecha_devolucion_esperada", "Devolución", "fecha"),
                            _col("estado", "Estado"),
                            _col("dias_restantes", "Días restantes", "entero"),
                        ],
                        [fila_prestamo(p) for p in activos],
                    ),
                    construir_tabla(
                        "Libros con bajo stock",
                        [
                            _col("titulo", "Título"),
                            _col("autor", "Autor"),
                            _col("copias_disponibles", "Disponibles", "entero"),
                            _col("numero_copias", "Total", "entero"),
                        ],
                        [
                            {
                                "titulo": l.titulo,
                                "autor": l.autor,
                                "copias_disponibles": l.copias_disponibles,
                                "numero_copias": l.numero_copias,
                            }
                            for l in bajo_stock
                        ],
                    ),
                    construir_tabla(
                        "Multas pendientes",
                        columnas_multa[:2] + [_col("nombre_usuario", "Usuario")] + columnas_multa[2:],
                        [m.model_dump() for m in multas],
                    ),
                ],
            )

        todos = prestamo_service.get_by_usuario(usuario.id)
        activos = [p for p in todos if p.estado in ("ACTIVO", "VENCIDO")]
        multas = [m for m in multa_service.get_by_usuario(usuario.id) if m.estado == "PENDIENTE"]
        por_vencer = []
        for p in activos:
            dias = _dias_restantes(p.fecha_devolucion_esperada, ahora)
            if p.estado != "VENCIDO" and dias is not None and 0 <= dias <= DIAS_POR_VENCER:
                por_vencer.append(p)
        return self._reporte(
            "dashboard",
            "Mi resumen de actividad",
            usuario,
            subtitulo="Préstamos en curso y multas pendientes del usuario en sesión",
            indicadores=[
                _ind("Libros prestados ahora", len(activos)),
                _ind(f"Por vencer (próximos {DIAS_POR_VENCER} días)", len(por_vencer)),
                _ind("Vencidos", sum(1 for p in activos if p.estado == "VENCIDO")),
                _ind("Préstamos históricos", len(todos)),
                _ind("Multas pendientes", len(multas)),
                _ind("Monto a pagar", _suma(m.monto for m in multas), "moneda"),
            ],
            tablas=[
                construir_tabla(
                    "Mis préstamos activos",
                    [
                        _col("titulo", "Libro"),
                        _col("autor", "Autor"),
                        _col("fecha_prestamo", "Prestado", "fecha"),
                        _col("fecha_devolucion_esperada", "Devolución", "fecha"),
                        _col("estado", "Estado"),
                        _col("dias_restantes", "Días restantes", "entero"),
                    ],
                    [fila_prestamo(p) for p in activos],
                ),
                construir_tabla("Mis multas pendientes", columnas_multa, [m.model_dump() for m in multas]),
            ],
        )
