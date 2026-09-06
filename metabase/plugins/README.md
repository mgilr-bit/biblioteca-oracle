# Plugins JDBC para Metabase

Metabase **no incluye el driver JDBC de Oracle** (por licenciamiento). Sin el
driver, al configurar la conexión a Oracle en la UI verás un error del tipo:

> `Expecting exception ... driver for type oracle not found`

**Solución:** colocar aquí los JAR del driver Thin de Oracle (Oracle JDBC) y
reiniciar el servicio `metabase`:

```bash
# 1. Descargar el driver (ej. ojdbc11.jar desde Maven Central):
#    https://central.sonatype.com/artifact/com.oracle.database.jdbc/ojdbc11
#    y, recomendado, también orai18n.jar (soporte de charset/acentos):
#    https://central.sonatype.com/artifact/com.oracle.database.nls/orai18n
#
# 2. Colocar los .jar aquí (este directorio):
metabase/plugins/ojdbc11.jar
metabase/plugins/orai18n.jar

# 3. Levantar / reiniciar:
docker compose up -d --force-recreate metabase
```

> Los JAR no se versionan en el repo (licencia de Oracle). El `docker-compose`
> monta `./metabase/plugins` como `/plugins` (solo lectura) y configura
> `MB_PLUGINS_DIR=/plugins` para que Metabase los cargue al arrancar.

## Conexión desde la UI de Metabase (http://localhost:3000)

1. Primer arranque: crea la cuenta de administrador local de Metabase.
2. **Add a database / Datos → Agregar base de datos** con:
   - **Tipo:** Oracle
   - **Host:** `db` (nombre del contenedor dentro de la red de Docker; desde
     tu máquina también sirve `localhost`)
   - **Puerto:** `1521`
   - **Nombre de base de datos:** `XEPDB1` (service name)
   - **Usuario:** `metabase_user`
   - **Contraseña:** `MetabaseAnalytics123`
   - **No** marques "Connect using Oracle SID": `XEPDB1` es un *service name*,
     no un SID.
   - **Opciones avanzadas:** ID de esquema `biblioteca_user` si quieres acotar
     qué esquema explora Metabase.

## Qué consultar

El usuario `metabase_user` (creado por `database/10_metabase_user.sql`) es de
solo lectura (`SELECT ANY TABLE`). Objetos útiles:

| Objeto | Qué contiene |
|---|---|
| `V_OLAP_PRESTAMOS_MENSUAL` | Serie mensual de préstamos (12 meses) |
| `V_OLAP_TOP_LIBROS` | Top 10 libros por préstamos |
| `V_OLAP_PRESTAMOS_GENERO` | Demanda agregada por género |
| `V_OLAP_MULTAS_MENSUAL` | Monto generado/recaudado y pendientes por mes |
| `MULTAS`, `LIBROS`, `PRESTAMOS`, `USUARIOS`, ... | Datos operativos (solo lectura) |

Las vistas materializadas se refrescan en el job diario `JOB_CRON_BIBLIOTECA`
(ver `database/09_cron_jobs.sql`) o con el mantenimiento del backend.

## Nota sobre entornos ya inicializados

`10_metabase_user.sql` se ejecuta en el **primer arranque** del contenedor de
Oracle (initdb). Si tu volumen de BD ya existe, ejecútalo una vez a mano:

```bash
docker compose exec db bash -lc "echo 'ALTER SESSION SET CONTAINER = XEPDB1;' > /tmp/u.sql"
docker compose cp database/10_metabase_user.sql db:/tmp/u2.sql
docker compose exec db bash -lc "cat /tmp/u2.sql >> /tmp/u.sql && sqlplus -S -L sys/oracle as sysdba @/tmp/u.sql"
```