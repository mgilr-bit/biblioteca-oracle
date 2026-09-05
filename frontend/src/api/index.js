import { http } from './client'

export const authAPI = {
  login: (email, password) => http.post('/auth/login', { email, password }),
  register: (nombre, email, password, rol) =>
    http.post('/auth/register', { nombre, email, password, rol }),
  me: () => http.get('/auth/me'),
  logout: () => http.post('/auth/logout')
}

export const librosAPI = {
  getAll: async (page = 1, perPage = 100) => {
    const data = await http.get(`/libros/?page=${page}&per_page=${perPage}`)
    return data.libros !== undefined ? data : { libros: data, total: data.length }
  },
  getById: (id) => http.get(`/libros/${id}`),
  getGeneros: () => http.get('/libros/generos'),
  search: (params) => http.get(`/libros/search?${new URLSearchParams(params).toString()}`),
  create: (libro) => http.post('/libros/', libro),
  update: (id, libro) => http.put(`/libros/${id}`, libro),
  delete: (id) => http.delete(`/libros/${id}`),
  getBajoStock: () => http.get('/libros/bajo-stock'),
  getEstadisticas: () => http.get('/libros/estadisticas'),
  exportCSV: () => http.getBlob('/libros/export/csv')
}

export const notificacionesAPI = {
  getAll: () => http.get('/notificaciones/'),
  getNoLeidas: () => http.get('/notificaciones/no-leidas/count'),
  marcarLeida: (id) => http.put(`/notificaciones/${id}/leida`),
  marcarTodasLeidas: () => http.put('/notificaciones/marcar-todas-leidas')
}

export const reservasAPI = {
  getAll: () => http.get('/reservas/'),
  getByUsuario: (idUsuario) => http.get(`/reservas/usuario/${idUsuario}`),
  getCola: (idLibro) => http.get(`/reservas/cola/${idLibro}`),
  create: (reserva) => http.post('/reservas/', reserva),
  cancelar: (id) => http.put(`/reservas/${id}/cancelar`)
}

export const ejemplaresAPI = {
  getAll: async (page = 1, perPage = 100, filters = {}) => {
    const params = new URLSearchParams({ page, per_page: perPage })
    if (filters.id_libro) params.append('id_libro', filters.id_libro)
    if (filters.estado) params.append('estado', filters.estado)
    const data = await http.get(`/ejemplares/?${params.toString()}`)
    return data.ejemplares !== undefined ? data : { ejemplares: data, total: data.length }
  },
  getEstados: () => http.get('/ejemplares/estados'),
  getPorLibro: (idLibro) => http.get(`/ejemplares/por-libro/${idLibro}`),
  getById: (id) => http.get(`/ejemplares/${id}`),
  create: (ejemplar) => http.post('/ejemplares/', ejemplar),
  update: (id, ejemplar) => http.put(`/ejemplares/${id}`, ejemplar),
  changeEstado: (id, estado) => http.put(`/ejemplares/${id}/estado`, { estado }),
  delete: (id) => http.delete(`/ejemplares/${id}`)
}

export const editorialesAPI = {
  getAll: async (page = 1, perPage = 100) => {
    const data = await http.get(`/editoriales/?page=${page}&per_page=${perPage}`)
    return data.editoriales !== undefined ? data : { editoriales: data, total: data.length }
  },
  getTodas: () => http.get('/editoriales/todas'),
  getById: (id) => http.get(`/editoriales/${id}`),
  create: (editorial) => http.post('/editoriales/', editorial),
  update: (id, editorial) => http.put(`/editoriales/${id}`, editorial),
  delete: (id) => http.delete(`/editoriales/${id}`)
}

export const prestamosAPI = {
  getAll: () => http.get('/prestamos/'),
  getActivos: () => http.get('/prestamos/activos'),
  getVencidos: () => http.get('/prestamos/vencidos'),
  getByUsuario: (idUsuario) => http.get(`/prestamos/usuario/${idUsuario}`),
  create: (prestamo) => http.post('/prestamos/', prestamo),
  devolver: (id) => http.put(`/prestamos/${id}/devolver`)
}

export const usuariosAPI = {
  getAll: () => http.get('/usuarios/'),
  getById: (id) => http.get(`/usuarios/${id}`),
  createAdmin: (userData) => http.post('/usuarios/admin', userData),
  update: (id, userData) => http.put(`/usuarios/${id}`, userData),
  toggleEstado: (id, activo) => http.patch(`/usuarios/${id}/estado`, { activo }),
  delete: (id) => http.delete(`/usuarios/${id}`)
}
