// API Configuration
const API_URL = 'http://localhost:5000/api';

// Utilidad para obtener el token
function getToken() {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    return user?.token || null;
}

// Utilidad para obtener headers con autenticaci�n
function getAuthHeaders() {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json'
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
}

// Utilidad para manejar respuestas
async function handleResponse(response) {
    if (response.status === 401) {
        // Token inv�lido o expirado
        localStorage.removeItem('user');
        window.location.href = '/index.html';
        throw new Error('Sesi�n expirada');
    }

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || 'Error en la solicitud');
    }

    return data;
}

// API de Autenticaci�n
const authAPI = {
    login: async (email, password) => {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        return handleResponse(response);
    },

    register: async (nombre, email, password, rol) => {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, email, password, rol })
        });
        return handleResponse(response);
    }
};

// API de Libros
const librosAPI = {
    getAll: async (page = 1, perPage = 100) => {
        const response = await fetch(`${API_URL}/libros/?page=${page}&per_page=${perPage}`, {
            headers: getAuthHeaders()
        });
        const data = await handleResponse(response);
        // Si viene con metadata de paginación, retornar todo, sino solo los libros
        return data.libros !== undefined ? data : { libros: data, total: data.length };
    },

    getById: async (id) => {
        const response = await fetch(`${API_URL}/libros/${id}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getGeneros: async () => {
        const response = await fetch(`${API_URL}/libros/generos`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    search: async (params) => {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${API_URL}/libros/search?${queryString}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    create: async (libro) => {
        const response = await fetch(`${API_URL}/libros/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(libro)
        });
        return handleResponse(response);
    },

    update: async (id, libro) => {
        const response = await fetch(`${API_URL}/libros/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(libro)
        });
        return handleResponse(response);
    },

    delete: async (id) => {
        const response = await fetch(`${API_URL}/libros/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getBajoStock: async () => {
        const response = await fetch(`${API_URL}/libros/bajo-stock`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    }
};

// API de Pr�stamos
const prestamosAPI = {
    getAll: async () => {
        const response = await fetch(`${API_URL}/prestamos/`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getActivos: async () => {
        const response = await fetch(`${API_URL}/prestamos/activos`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getVencidos: async () => {
        const response = await fetch(`${API_URL}/prestamos/vencidos`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getByUsuario: async (idUsuario) => {
        const response = await fetch(`${API_URL}/prestamos/usuario/${idUsuario}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    create: async (prestamo) => {
        const response = await fetch(`${API_URL}/prestamos/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(prestamo)
        });
        return handleResponse(response);
    },

    devolver: async (id) => {
        const response = await fetch(`${API_URL}/prestamos/${id}/devolver`, {
            method: 'PUT',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    }
};

// API de Usuarios
const usuariosAPI = {
    getAll: async () => {
        const response = await fetch(`${API_URL}/usuarios/`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    getById: async (id) => {
        const response = await fetch(`${API_URL}/usuarios/${id}`, {
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    },

    createAdmin: async (userData) => {
        const response = await fetch(`${API_URL}/usuarios/admin`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(userData)
        });
        return handleResponse(response);
    },

    update: async (id, userData) => {
        const response = await fetch(`${API_URL}/usuarios/${id}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(userData)
        });
        return handleResponse(response);
    },

    toggleEstado: async (id, nuevoEstado) => {
        const response = await fetch(`${API_URL}/usuarios/${id}/estado`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify({ activo: nuevoEstado })
        });
        return handleResponse(response);
    },

    delete: async (id) => {
        const response = await fetch(`${API_URL}/usuarios/${id}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        return handleResponse(response);
    }
};

// Utilidades de autenticaci�n
const auth = {
    isAuthenticated: () => {
        return getToken() !== null;
    },

    getUser: () => {
        return JSON.parse(localStorage.getItem('user') || 'null');
    },

    logout: () => {
        localStorage.removeItem('user');
        window.location.href = '/index.html';
    },

    requireAuth: () => {
        if (!auth.isAuthenticated()) {
            window.location.href = '/index.html';
        }
    },

    hasRole: (role) => {
        const user = auth.getUser();
        return user?.rol === role;
    },

    isBibliotecario: () => {
        return auth.hasRole('BIBLIOTECARIO');
    }
};
