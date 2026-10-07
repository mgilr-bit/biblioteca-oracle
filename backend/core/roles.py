"""Roles que operan a nombre de terceros.

Los servicios que aceptan un `id_usuario` en el body (préstamos, reservas)
deben distinguir entre quien gestiona a otros y quien solo opera consigo
mismo. Casbin no sirve para ese corte: las políticas de `create` de
LECTOR/PROFESOR llevan `owner_only=false` justamente porque es el servicio
—no el gate de ruta— el que fuerza el id propio. Se centraliza acá para no
repetir el literal y para que ADMIN no vuelva a quedarse fuera.
"""
#: Roles que pueden registrar un préstamo/reserva a nombre de otro usuario.
ROLES_GESTION = ("BIBLIOTECARIO", "ADMIN")


def puede_operar_por_terceros(rol: str) -> bool:
    return rol in ROLES_GESTION
