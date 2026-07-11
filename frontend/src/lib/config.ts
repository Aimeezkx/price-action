/**
 * Configuration management for API connectivity
 * Handles environment-specific settings and fallback URLs
 */

export interface ApiConfig {
  baseUrl: string;
  fallbackUrl?: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  healthCheckInterval: number;
  healthCheckTimeout: number;
}

export interface EnvironmentConfig {
  isDevelopment: boolean;
  isProduction: boolean;
  debug: boolean;
  environment: string;
}

class ConfigManager {
  private static instance: ConfigManager;
  private apiConfig: ApiConfig;
  private envConfig: EnvironmentConfig;

  private constructor() {
    this.apiConfig = this.loadApiConfig();
    this.envConfig = this.loadEnvironmentConfig();
  }

  public static getInstance(): ConfigManager {
    if (!ConfigManager.instance) {
      ConfigManager.instance = new ConfigManager();
    }
    return ConfigManager.instance;
  }

  private loadApiConfig(): ApiConfig {
    // Use relative paths in development to leverage Vite proxy
    const isDev = import.meta.env.DEV;
    const baseUrl = isDev
      ? '' // Relative path for Vite proxy in development
      : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');

    return {
      baseUrl,
      fallbackUrl: import.meta.env.VITE_API_FALLBACK_URL || 'http://127.0.0.1:8000',
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
      retryAttempts: parseInt(import.meta.env.VITE_RETRY_ATTEMPTS || '3'),
      retryDelay: parseInt(import.meta.env.VITE_RETRY_DELAY || '1000'),
      healthCheckInterval: parseInt(import.meta.env.VITE_HEALTH_CHECK_INTERVAL || '30000'),
      healthCheckTimeout: parseInt(import.meta.env.VITE_HEALTH_CHECK_TIMEOUT || '5000'),
    };
  }

  private loadEnvironmentConfig(): EnvironmentConfig {
    const environment = import.meta.env.VITE_ENVIRONMENT || 'development';
    return {
      isDevelopment: environment === 'development',
      isProduction: environment === 'production',
      debug: import.meta.env.VITE_DEBUG === 'true',
      environment,
    };
  }

  public getApiConfig(): ApiConfig {
    return { ...this.apiConfig };
  }

  public getEnvironmentConfig(): EnvironmentConfig {
    return { ...this.envConfig };
  }

  public isLocalDevelopment(): boolean {
    return this.envConfig.isDevelopment &&
           (this.apiConfig.baseUrl.includes('localhost') ||
            this.apiConfig.baseUrl.includes('127.0.0.1'));
  }

  public getHealthCheckUrl(): string {
    return `${this.apiConfig.baseUrl}/api/health`;
  }

  public getFallbackHealthCheckUrl(): string {
    return this.apiConfig.fallbackUrl ? `${this.apiConfig.fallbackUrl}/api/health` : '';
  }

  public getApiEndpoint(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    // Ensure API prefix for relative paths
    const apiPath = cleanPath.startsWith('/api') ? cleanPath : `/api${cleanPath}`;
    return `${this.apiConfig.baseUrl}${apiPath}`;
  }

  public getFallbackApiEndpoint(path: string): string {
    if (!this.apiConfig.fallbackUrl) return '';
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const apiPath = cleanPath.startsWith('/api') ? cleanPath : `/api${cleanPath}`;
    return `${this.apiConfig.fallbackUrl}${apiPath}`;
  }

  public logConfiguration(): void {
    if (this.envConfig.debug) {
      console.group('🔧 Configuration Manager');
      console.log('Environment:', this.envConfig.environment);
      console.log('API Base URL:', this.apiConfig.baseUrl);
      console.log('API Fallback URL:', this.apiConfig.fallbackUrl);
      console.log('Timeout:', this.apiConfig.timeout);
      console.log('Retry Attempts:', this.apiConfig.retryAttempts);
      console.log('Health Check URL:', this.getHealthCheckUrl());
      console.log('Is Local Development:', this.isLocalDevelopment());
      console.groupEnd();
    }
  }
}

// Export singleton instance
export const configManager = ConfigManager.getInstance();

// Export convenience functions
export const getApiConfig = () => configManager.getApiConfig();
export const getEnvironmentConfig = () => configManager.getEnvironmentConfig();
export const isLocalDevelopment = () => configManager.isLocalDevelopment();
export const getHealthCheckUrl = () => configManager.getHealthCheckUrl();
export const getApiEndpoint = (path: string) => configManager.getApiEndpoint(path);

// Initialize configuration logging in development
if (configManager.getEnvironmentConfig().debug) {
  configManager.logConfiguration();
}