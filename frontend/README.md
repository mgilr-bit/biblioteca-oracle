# Biblioteca — Frontend (Vue 3)

Migración del frontend original en HTML/CSS/JS puro a **Vue 3 + Vite + Pinia
+ Vue Router**. Ver `CORRECCIONES.md` para el detalle de todos los bugs y
riesgos corregidos durante la migración.

## Requisitos

- Node.js 18+ y npm

## Puesta en marcha

```bash
npm install
cp .env.example .env      # ajusta VITE_API_URL si tu backend no está en localhost:5000
npm run dev                # http://localhost:5173
```

## Build de producción

```bash
npm run build               # genera ./dist
npm run preview             # sirve ./dist localmente para probarlo
```

## Docker

```bash
docker build -t biblioteca-frontend --build-arg VITE_API_URL=https://tu-api.com/api .
docker run -p 8080:80 biblioteca-frontend
```

## Estructura

```
src/
├── api/            Cliente HTTP + endpoints agrupados por dominio
├── assets/         Tokens de diseño (paleta, tipografía) y componentes CSS
├── components/     Navbar, Modal, Paginación, Toasts, Confirmación
├── composables/     useToast, useConfirm (reemplazan alert/confirm)
├── router/          Rutas + guards de autenticación y rol
├── stores/           Pinia — sesión de usuario (basada en cookie, no localStorage)
├── utils/cookies.js Helper de cookies que reemplaza localStorage
└── views/            Login, Dashboard, Libros, Préstamos, Usuarios
```

## Notas de seguridad sobre las cookies

Este frontend ya **no usa `localStorage`**: la sesión (usuario + token) se
guarda en una cookie (`biblioteca_session`) gestionada desde `src/utils/cookies.js`.
Como el frontend es estático y no controla las cabeceras HTTP del login, esta
cookie se escribe desde JavaScript y por tanto **no es `httpOnly`** — sigue
siendo legible por un script si hubiera una vulnerabilidad XSS, igual que
pasaba con localStorage. Ver el punto de seguridad #1 en `CORRECCIONES.md`
para la recomendación de migrar esto a una cookie de sesión emitida por el
backend con `HttpOnly; Secure; SameSite=Strict`.
