/**
 * API клиент для взаимодействия с Django REST API
 */

class API {
    constructor() {
        this.baseURL = '/api';
        this.token = localStorage.getItem('access_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders(),
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Токен истек, пробуем обновить
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Повторяем запрос с новым токеном
                    config.headers = this.getHeaders();
                    return await fetch(url, config);
                }
                throw new Error('Требуется авторизация');
            }

            // DELETE может вернуть 204 No Content без тела
            if (response.status === 204) {
                return null;
            }

            // Читаем тело ответа один раз
            const contentType = response.headers.get('content-type');
            let responseData = null;
            
            if (contentType && contentType.includes('application/json')) {
                const text = await response.text();
                if (text && text.trim()) {
                    try {
                        responseData = JSON.parse(text);
                    } catch (e) {
                        console.error('Ошибка парсинга JSON:', e, 'Текст:', text);
                        responseData = null;
                    }
                }
            }

            if (!response.ok) {
                // Если это ошибка, используем распарсенные данные или создаем объект ошибки
                const error = responseData || { error: `HTTP ${response.status}: ${response.statusText}` };
                throw new Error(error.detail || error.error || error.message || 'Ошибка API');
            }

            // Возвращаем данные (может быть null для пустых ответов)
            return responseData;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // === Авторизация ===
    async login(phone, password) {
        const response = await fetch(`${this.baseURL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка авторизации');
        }

        const data = await response.json();
        this.setToken(data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        return data;
    }

    async logout() {
        try {
            await this.request('/auth/logout/', { method: 'POST' });
        } catch (e) {
            console.error('Logout error:', e);
        } finally {
            this.clearToken();
        }
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;

        try {
            const response = await fetch(`${this.baseURL}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (!response.ok) return false;

            const data = await response.json();
            this.setToken(data.access);
            return true;
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }

    async getMe() {
        return await this.request('/auth/me/');
    }

    // === Транзакции ===
    async getTransactions(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/transactions/${queryString ? '?' + queryString : ''}`;
        return await this.request(endpoint);
    }

    async createTransaction(data) {
        return await this.request('/transactions/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateTransaction(id, data) {
        return await this.request(`/transactions/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteTransaction(id) {
        return await this.request(`/transactions/${id}/`, {
            method: 'DELETE',
        });
    }

    // === Справочники ===
    async getCategories() {
        return await this.request('/categories/');
    }

    async getProjects() {
        return await this.request('/projects/');
    }

    async getObjects(projectId = null) {
        const params = projectId ? { project: projectId } : {};
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/objects/${queryString ? '?' + queryString : ''}`);
    }

    async getStages(projectId = null) {
        const params = projectId ? { project: projectId } : {};
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/stages/${queryString ? '?' + queryString : ''}`);
    }

    async getEstimates(stageId = null) {
        const params = stageId ? { stage: stageId } : {};
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/estimates/${queryString ? '?' + queryString : ''}`);
    }

    async getContractors() {
        return await this.request('/contractors/');
    }

    // Проверка соединения
    async checkConnection() {
        try {
            await fetch('/api/auth/me/', {
                method: 'HEAD',
                headers: this.getHeaders(),
            });
            return true;
        } catch {
            return false;
        }
    }
}

// Глобальный экземпляр API
const api = new API();


