// API client for iOS app - connects to same backend as web app
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8000/api'  // Development
  : 'https://your-api-domain.com/api';  // Production

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async getAuthToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('auth_token');
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = await this.getAuthToken();
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Document endpoints
  async getDocuments() {
    return this.request('/documents');
  }

  async getDocument(id: string) {
    return this.request(`/documents/${id}`);
  }

  async uploadDocument(fileUri: string, fileName: string, fileType: string) {
    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      name: fileName,
      type: fileType,
    } as any);

    const token = await this.getAuthToken();
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`);
    }

    return response.json();
  }

  // Chapter endpoints
  async getChapters(documentId: string) {
    return this.request(`/doc/${documentId}/toc`);
  }

  async getChapterFigures(chapterId: string) {
    return this.request(`/chapter/${chapterId}/fig`);
  }

  async getChapterKnowledge(chapterId: string, params?: {
    knowledge_type?: string;
    limit?: number;
    offset?: number;
  }) {
    const query = params ? `?${new URLSearchParams(params as Record<string, string>)}` : '';
    return this.request(`/chapter/${chapterId}/k${query}`);
  }

  // Card endpoints
  async getCards(params?: Record<string, string>) {
    const query = params ? `?${new URLSearchParams(params)}` : '';
    return this.request(`/cards${query}`);
  }

  async generateCards(documentId: string) {
    return this.request('/card/gen', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId }),
    });
  }

  // Review endpoints
  async getTodayReview() {
    return this.request('/review/today');
  }

  async gradeCard(cardId: string, grade: number) {
    return this.request('/review/grade', {
      method: 'POST',
      body: JSON.stringify({ card_id: cardId, grade }),
    });
  }

  // Search endpoints
  async search(query: string, filters?: Record<string, string>) {
    const params = new URLSearchParams({ q: query, ...filters });
    return this.request(`/search?${params}`);
  }

  // Export endpoints
  async exportCsv(format: 'anki' | 'notion' = 'anki') {
    return this.request(`/export/csv?format=${format}`);
  }

  async exportJsonl() {
    return this.request('/export/jsonl');
  }
}

export const apiClient = new ApiClient();