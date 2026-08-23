# Correcciones aplicadas en la migración a Vue

Este documento resume cada problema detectado en el frontend original
(HTML/CSS/JS puro) y cómo quedó resuelto en la versión Vue. Se agrupan por
severidad.

---

## 1. Seguridad

### 1.1 XSS por `innerHTML` con datos del backend sin escapar
**Antes:** en `dashboard.html`, `libros.html`, `prestamos.html` y
`usuarios.html`, los datos que devuelve la API (`TITULO`, `AUTOR`, `NOMBRE`,
`EMAIL`…) se insertaban directamente en `innerHTML` vía template strings. Si
el backend no sanea esos campos (o si alguien los edita directo en la base
de datos), un título de libro como `<img src=x onerror=alert(1)>` se
ejecuta como script en el navegador de cualquiera que abra la tabla.

**Ahora:** todas las vistas usan interpolación de Vue (`{{ }}`), que escapa
el contenido automáticamente por defecto. No hay un solo `innerHTML` con
datos dinámicos en todo el proyecto.

### 1.2 Inyección vía `onclick="fn(${JSON.stringify(obj)})"`
**Antes:** en `libros.html` y `usuarios.html`, el botón "Editar" incrustaba
un JSON completo dentro de un atributo `onclick`. Si un campo de texto
contenía una comilla simple, rompía el HTML generado; en el peor caso era
otro vector de inyección.

**Ahora:** los manejadores usan `@click="editLibro(libro)"` pasando el
objeto real de JavaScript, sin serializar nada al HTML.

### 1.3 Sesión en `localStorage` → ahora en cookie
**Pedido explícito:** se eliminó `localStorage` por completo. La sesión
(usuario + token) vive en la cookie `biblioteca_session`
(`src/utils/cookies.js`), gestionada por el store de Pinia
(`src/stores/auth.js`).

**Limitación que hay que conocer:** como el frontend es 100% estático (no
hay servidor propio que pueda emitir `Set-Cookie: HttpOnly`), esta cookie se
escribe desde JavaScript con `document.cookie`. Eso significa que, igual que
pasaba con `localStorage`, sigue siendo legible por un script si existiera
una vulnerabilidad XSS en la página (mitigado en gran parte por el punto 1.1
y 1.2, que eran las vías de XSS reales que tenía la app). Se fijó
`SameSite=Lax` y `Secure` quedó condicionado a HTTPS.

**Recomendación a futuro (no implementada aquí porque requiere cambios en
el backend):** que el endpoint `/auth/login` del backend fije la cookie de
sesión él mismo con `HttpOnly; Secure; SameSite=Strict`, y que el frontend
dependa de `credentials: 'include'` en cada fetch sin tocar el token en
ningún momento desde JS. Esa es la única forma de que el token quede
realmente fuera del alcance de un XSS.

### 1.4 Control de acceso a "Usuarios" solo visual
**Antes:** el link a `usuarios.html` se ocultaba con `display:none` para
lectores, pero la página seguía siendo accesible tecleando la URL
directamente; solo mostraba un `alert()` después de haber cargado y
redirigía con retraso.

**Ahora:** la ruta `/usuarios` tiene `meta: { requiresBibliotecario: true }`
y el *router guard* (`src/router/index.js`) la resuelve a `/` (dashboard)
antes de montar ningún componente si el rol no coincide. La UI (ocultar el
link) sigue existiendo, pero ya no es el único control.

*(Recordatorio: esto sigue siendo control de acceso de frontend. La
autorización real debe seguir validándose en cada endpoint del backend —
esto no cambia con la migración.)*

---

## 2. Bugs y deuda técnica

### 2.1 `API_URL` duplicada y hardcodeada
**Antes:** `const API_URL = 'http://localhost:5000/api'` estaba escrita dos
veces: una en `js/api.js` y otra copiada dentro de `exportarCSV()` en
`libros.html`. Cambiar de entorno (dev/staging/prod) implicaba editar
código en dos sitios y no olvidarse de ninguno.

**Ahora:** una sola variable de entorno `VITE_API_URL` (`.env`), leída una
vez en `src/api/client.js`. Se configura por despliegue sin tocar código
(incluye soporte para pasarla como `--build-arg` en Docker).

### 2.2 `js/main.js` y `pages/login.html` vacíos y sin usar
**Antes:** dos archivos de 0 bytes que no se referenciaban desde ningún
lado — el login real vivía en `index.html`. Ruido en el repositorio.

**Ahora:** no existen equivalentes; la estructura de Vue no tiene archivos
huérfanos.

### 2.3 Autenticación repetida copy-paste en cada página
**Antes:** `auth.requireAuth()` y la lógica de mostrar/ocultar el link de
"Usuarios" estaban copiadas al inicio del `<script>` de las 4 páginas
internas.

**Ahora:** un único *navigation guard* en `src/router/index.js` cubre la
autenticación para todas las rutas.

### 2.4 `nginx.conf` incompatible con navegación de una SPA
**Antes:** `try_files $uri $uri/ =404` funcionaba porque cada página era un
archivo `.html` físico. Al migrar a una SPA con Vue Router en modo
`history`, recargar la página estando en `/libros` habría devuelto 404 (no
existe ese archivo en disco).

**Ahora:** `try_files $uri $uri/ /index.html` — cualquier ruta desconocida
cae al `index.html` y Vue Router decide qué vista mostrar.

### 2.5 `Dockerfile` no compilaba nada
**Antes:** copiaba el HTML/CSS/JS tal cual a nginx, porque no había paso de
build.

**Ahora:** Dockerfile *multi-stage*: una etapa `node:20-alpine` instala
dependencias y corre `npm run build`, y solo el resultado (`dist/`) se copia
a la imagen final de `nginx:alpine`. La imagen final no lleva Node ni
`node_modules`.

---

## 3. Interfaz gráfica

**Antes:** Bootstrap 5 genérico (el mismo look que miles de proyectos
"admin panel" en internet), con `alert()`/`confirm()` nativos del navegador
para todo feedback al usuario, sin fuentes propias.

**Ahora:** sistema de diseño propio, claro y minimalista, pensado para el
dominio (biblioteca / ficha de catálogo):

- **Paleta clara:** fondo papel (`#faf9f6`), superficies blancas, tinta
  principal casi negra cálida, un acento azul-marino tipo "tinta de ledger"
  (`#2c3e58`) usado con moderación, y colores de estado (éxito, aviso,
  peligro, info) en tonos apagados en vez de los rojo/verde/amarillo puros
  de Bootstrap.
- **Tipografía:** `Source Serif 4` para títulos (evoca catálogo impreso),
  `Inter` para texto de interfaz, `IBM Plex Mono` para IDs, ISBN y códigos —
  como si fueran números de catálogo.
- **Elemento distintivo:** los estados (`ACTIVO`, `VENCIDO`, `Disponible`…)
  se muestran como "sellos" (`.stamp`): etiquetas en monoespaciada,
  mayúsculas, con borde y una leve rotación de -1°, evocando un sello de
  fecha de devolución de biblioteca real — en vez de las píldoras de color
  sólido genéricas de Bootstrap.
- **`alert()` / `confirm()` eliminados:** reemplazados por un sistema de
  *toasts* no bloqueante (`useToast`) y un diálogo de confirmación modal
  (`useConfirm`), consistentes con el resto de la interfaz.
- **Accesibilidad base:** foco visible (`:focus-visible`), respeto a
  `prefers-reduced-motion`, contraste AA en el texto sobre los fondos
  definidos.

---

## 4. Lo que se mantuvo igual a propósito

- La lógica de negocio y los endpoints de la API no cambiaron: mismos
  campos (`TITULO`, `AUTOR`, `ID_LIBRO`…), mismos flujos de préstamo/
  devolución, mismas reglas de rol (`BIBLIOTECARIO` vs `LECTOR`).
- El registro público sigue asignando siempre el rol `LECTOR` (igual que en
  el original, donde el campo era un `<input type="hidden">`).
