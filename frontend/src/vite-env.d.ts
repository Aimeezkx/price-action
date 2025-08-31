/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_RETRY_MAX_ATTEMPTS: string
  readonly VITE_RETRY_BASE_DELAY: string
  readonly VITE_RETRY_MAX_DELAY: string
  readonly VITE_RETRY_BACKOFF_FACTOR: string
  readonly VITE_RETRY_JITTER_ENABLED: string
  readonly VITE_RETRY_JITTER_FACTOR: string
  readonly VITE_RETRY_TIMEOUT_MS: string
  readonly VITE_RETRY_STATUS_CODES: string
  readonly VITE_RETRY_ERROR_TYPES: string
  readonly VITE_CIRCUIT_BREAKER_ENABLED: string
  readonly VITE_CIRCUIT_BREAKER_THRESHOLD: string
  readonly VITE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT: string
  readonly VITE_CIRCUIT_BREAKER_MONITORING_WINDOW: string
  readonly VITE_DEBUG: string
  readonly DEV: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}