# Análisis de Base de Datos - Sistema de Biblioteca

## 📊 Estado Actual

### ✅ Fortalezas

#### 1. **Diseño de Tablas**
- ✅ Uso de `NUMBER GENERATED ALWAYS AS IDENTITY` (recomendado en Oracle 12c+)
- ✅ Constraints bien definidos (CHECK, UNIQUE, NOT NULL)
- ✅ Foreign Keys con `ON DELETE CASCADE` apropiado
- ✅ Valores DEFAULT lógicos
- ✅ Uso de TABLESPACE personalizado

#### 2. **Triggers Implementados**
- ✅ `trg_prestamo_insert`: Actualiza copias disponibles al crear préstamo
- ✅ `trg_prestamo_devolucion`: Restaura copias al devolver
- ✅ `trg_validar_disponibilidad`: Previene préstamos sin disponibilidad

#### 3. **Índices Existentes**
```sql
-- Libros
idx_libros_titulo
idx_libros_autor
idx_libros_genero

-- Préstamos
idx_prestamos_usuario
idx_prestamos_estado
idx_prestamos_libro
idx_prestamos_fecha_estado

-- Usuarios
idx_usuarios_email
```

#### 4. **Integridad Referencial**
- ✅ Todas las relaciones tienen FK definidas
- ✅ Cascadas apropiadas en eliminaciones
- ✅ Validaciones de datos mediante CHECK constraints

---

## 🔧 Mejoras Recomendadas

### **Prioridad ALTA** (Implementar ahora)

#### 1. **Índice en ISBN**
```sql
CREATE INDEX idx_libros_isbn ON libros(isbn);
```
**Razón:** Mejora búsquedas por ISBN que agregaste recientemente

#### 2. **Índice Compuesto Usuario-Estado**
```sql
CREATE INDEX idx_prestamos_usuario_estado ON prestamos(id_usuario, estado);
```
**Razón:** Optimiza consultas del dashboard de lectores (mis préstamos activos/vencidos)

#### 3. **Índice en Fecha de Préstamo**
```sql
CREATE INDEX idx_prestamos_fecha ON prestamos(fecha_prestamo);
```
**Razón:** Mejora el filtrado por fecha que acabas de implementar

#### 4. **Restricción de Unicidad**
```sql
CREATE UNIQUE INDEX idx_prestamo_unico
ON prestamos(id_usuario, id_libro)
WHERE estado = 'ACTIVO';
```
**Razón:** Previene que un usuario tenga el mismo libro prestado múltiples veces

---

### **Prioridad MEDIA** (Considerar para próxima versión)

#### 5. **Tabla de Auditoría**
Registra todos los cambios en préstamos para trazabilidad:
- Quién realizó la acción
- Cuándo se realizó
- Qué cambió (estado anterior → estado nuevo)

**Beneficios:**
- Historial completo de operaciones
- Resolución de disputas
- Análisis de uso del sistema

#### 6. **Vistas Útiles**

**a) Libros Más Populares**
```sql
CREATE OR REPLACE VIEW v_libros_populares AS
SELECT l.titulo, l.autor, COUNT(p.id_prestamo) as total_prestamos
FROM libros l
LEFT JOIN prestamos p ON l.id_libro = p.id_libro
GROUP BY l.id_libro, l.titulo, l.autor
ORDER BY total_prestamos DESC;
```

**b) Usuarios Morosos**
```sql
CREATE OR REPLACE VIEW v_usuarios_morosos AS
SELECT u.nombre, COUNT(p.id_prestamo) as prestamos_vencidos
FROM usuarios u
INNER JOIN prestamos p ON u.id_usuario = p.id_usuario
WHERE p.estado = 'ACTIVO' AND p.fecha_devolucion_esperada < SYSDATE
GROUP BY u.id_usuario, u.nombre;
```

#### 7. **Procedimiento para Actualizar Vencidos**
```sql
CREATE OR REPLACE PROCEDURE actualizar_prestamos_vencidos IS
BEGIN
    UPDATE prestamos
    SET estado = 'VENCIDO'
    WHERE estado = 'ACTIVO'
      AND fecha_devolucion_esperada < SYSDATE;
    COMMIT;
END;
```

---

### **Prioridad BAJA** (Funcionalidades futuras)

#### 8. **Sistema de Multas**
Tabla para registrar multas por retrasos:
- Cálculo automático basado en días de retraso
- Estados: PENDIENTE, PAGADA, CONDONADA
- Integración con préstamos

#### 9. **Sistema de Reservas**
Permitir reservar libros no disponibles:
- Usuario reserva libro prestado
- Notificación cuando esté disponible
- Expiración automática de reservas

#### 10. **Job Automático**
Oracle Scheduler para actualizar préstamos vencidos diariamente:
- Ejecuta a las 00:00
- Actualiza estado de ACTIVO a VENCIDO
- No requiere intervención manual

#### 11. **Columnas Adicionales**
- `libros.descripcion` - Sinopsis del libro
- `libros.imagen_url` - Cover del libro
- `usuarios.telefono` - Contacto alternativo
- `usuarios.direccion` - Para envío de recordatorios

---

## 📈 Métricas de Rendimiento Actuales

### Consultas Más Frecuentes:
1. **Dashboard Bibliotecario**
   - `SELECT COUNT(*) FROM libros` → Rápido (tabla pequeña)
   - `SELECT SUM(copias_disponibles) FROM libros` → Rápido
   - Mejora: Podría crearse una tabla de estadísticas materializada

2. **Dashboard Lector**
   - `SELECT * FROM prestamos WHERE id_usuario = ?` → Rápido (índice)
   - `SELECT * FROM prestamos WHERE estado = 'ACTIVO'` → Rápido (índice)

3. **Gestión de Libros**
   - `SELECT * FROM libros LIMIT 50` → Rápido
   - `SELECT * FROM libros WHERE titulo LIKE ?` → Rápido (índice)
   - `SELECT * FROM libros WHERE isbn = ?` → **MEJORABLE** (sin índice)

4. **Filtros de Préstamos**
   - Por fecha → **MEJORABLE** (sin índice en fecha_prestamo)
   - Por usuario y estado → **MEJORABLE** (índices separados)

---

## 🎯 Plan de Implementación Sugerido

### Fase 1: Mejoras Inmediatas (5 minutos)
```bash
# Ejecutar en Oracle
sqlplus usuario/password@XE @database/08_mejoras_recomendadas.sql
```

Esto agregará:
- ✅ Índice en ISBN
- ✅ Índice compuesto usuario-estado
- ✅ Índice en fecha de préstamo
- ✅ Restricción de unicidad en préstamos activos

### Fase 2: Funcionalidades Avanzadas (Opcional)
Si decides implementar auditoría, multas, o reservas, están disponibles en el archivo `08_mejoras_recomendadas.sql`.

Solo necesitas descomentar las secciones relevantes.

---

## 💡 Recomendaciones Adicionales

### 1. **Backup Regular**
```bash
# Exportar base de datos
exp usuario/password@XE file=backup.dmp full=y

# O usar Data Pump (más rápido)
expdp usuario/password@XE directory=DATA_PUMP_DIR dumpfile=backup.dmp full=y
```

### 2. **Monitoreo de Rendimiento**
```sql
-- Ver consultas lentas
SELECT sql_text, executions, elapsed_time
FROM v$sql
WHERE elapsed_time > 1000000
ORDER BY elapsed_time DESC;

-- Ver índices no utilizados
SELECT index_name, table_name
FROM user_indexes
WHERE index_name NOT IN (
    SELECT index_name FROM v$object_usage WHERE used = 'YES'
);
```

### 3. **Optimización de Tablas**
```sql
-- Recopilar estadísticas (mejora el optimizador)
EXEC DBMS_STATS.GATHER_TABLE_STATS('USUARIO', 'LIBROS');
EXEC DBMS_STATS.GATHER_TABLE_STATS('USUARIO', 'PRESTAMOS');
EXEC DBMS_STATS.GATHER_TABLE_STATS('USUARIO', 'USUARIOS');
```

---

## 📝 Conclusión

### Estado Actual: **BUENO** ⭐⭐⭐⭐☆ (4/5)

**Fortalezas:**
- Diseño normalizado y limpio
- Integridad referencial completa
- Triggers funcionales
- Índices básicos en su lugar

**Áreas de Mejora:**
- Falta índice en ISBN (nueva funcionalidad)
- Falta índice en fecha_prestamo (filtros recientes)
- Sin auditoría de cambios
- Sin funcionalidades avanzadas (multas, reservas)

### Recomendación:
**Ejecutar las mejoras de Prioridad ALTA** del archivo `08_mejoras_recomendadas.sql` para optimizar el rendimiento de las funcionalidades recién agregadas (búsqueda por ISBN, filtros por fecha).

Las mejoras de prioridad media y baja pueden implementarse gradualmente según las necesidades del negocio.
