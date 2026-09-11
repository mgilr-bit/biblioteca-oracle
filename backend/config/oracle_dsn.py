"""Arma el connect string (DSN) de Oracle a partir de variables de entorno.

Dos modos, elegidos automaticamente:

* **Nube (Oracle Autonomous Database, TLS de una via)**: define `DB_DSN` con
  el descriptor completo que da la consola de OCI en *Database Connection ->
  Connection Strings -> TLS*, por ejemplo::

      DB_DSN=(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)
      (port=1521)(host=adb.mx-queretaro-1.oraclecloud.com))(connect_data=
      (service_name=xxxx_biblioteca_low.adb.oraclecloud.com))
      (security=(ssl_server_dn_match=yes)))

  No hace falta wallet: basta con que la IP del cliente este en la ACL de la
  base y que en OCI el *mutual TLS* este como "not required".

* **Local (Oracle XE)**: si `DB_DSN` no esta definida se arma un Easy Connect
  `host:puerto/servicio` con `DB_HOST` / `DB_PORT` / `DB_SERVICE`.
"""
import os


def get_dsn() -> str:
    """Devuelve el DSN a pasar a `oracledb` / SQLAlchemy (`connect_args`)."""
    dsn = os.getenv("DB_DSN")
    if dsn and dsn.strip():
        return dsn.strip()

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "1521")
    service = os.getenv("DB_SERVICE", "XEPDB1")
    return f"{host}:{port}/{service}"
