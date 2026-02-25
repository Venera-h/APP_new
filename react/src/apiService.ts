import { PracticalWorkCreate, PracticalWorkOut, PracticalWorkUpdate, User, TokenResponse } from './types';

const API_BASE_URL = 'http://localhost:8001';
const AUTH_BASE_URL = 'http://localhost:8000';

class ApiService {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('token');
  }

  private async request<T>(url: string, options: RequestInit = {}): Promise<T> {
    console.log('Making request to:', `${API_BASE_URL}${url}`);
    console.log('Token exists:', !!this.token);
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
      console.log('Authorization header added');
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      console.error('Request failed:', response.status, response.statusText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Auth methods
  async register(user: User): Promise<TokenResponse> {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    });
    if (!response.ok) throw new Error('Registration failed');
    const data = await response.json();
    this.token = data.token;
    localStorage.setItem('token', data.token);
    return data;
  }

  async login(user: User): Promise<TokenResponse> {
    const response = await fetch(`${AUTH_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    });
    if (!response.ok) throw new Error('Login failed');
    const data = await response.json();
    this.token = data.token;
    localStorage.setItem('token', data.token);
    return data;
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('token');
  }

  // Works methods
  async getWorks(): Promise<PracticalWorkOut[]> {
    console.log('Getting works with token:', this.token ? 'exists' : 'missing');
    return this.request<PracticalWorkOut[]>('/api/works/');
  }

  async createWork(work: PracticalWorkCreate): Promise<PracticalWorkOut> {
    return this.request<PracticalWorkOut>('/api/works/', {
      method: 'POST',
      body: JSON.stringify(work),
    });
  }

  async updateWork(id: number, work: PracticalWorkUpdate): Promise<PracticalWorkOut> {
    return this.request<PracticalWorkOut>(`/api/works/${id}`, {
      method: 'PUT',
      body: JSON.stringify(work),
    });
  }

  async deleteWork(id: number): Promise<void> {
    await this.request(`/api/works/${id}`, {
      method: 'DELETE',
    });
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }
}

export const apiService = new ApiService();