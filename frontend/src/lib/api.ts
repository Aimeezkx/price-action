import { performanceMonitor } from './performance';

// API client configuration
const API_BASE_URL = '/api';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const startTime = performance.now();
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const endTime = performance.now();
      const duration = endTime - startTime;

      // Track API call performance
      performanceMonitor.trackAPICall(endpoint, duration, response.status);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Track failed API calls
      performanceMonitor.trackAPICall(endpoint, duration, 0);
      throw error;
    }
  }

  // Document endpoints
  async getDocuments() {
    return this.request('/documents');
  }

  async getDocument(id: string) {
    return this.request(`/documents/${id}`);
  }

  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/ingest', {
      method: 'POST',
      headers: {}, // Let browser set Content-Type for FormData
      body: formData,
    });
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