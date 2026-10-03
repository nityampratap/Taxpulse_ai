export interface ApiErrorBody {
  code: string
  message: string
  details?: unknown
}

export interface ApiResponseError {
  error: ApiErrorBody
}

export class ApiClientError extends Error {
  public code: string
  public status: number
  public details?: unknown

  constructor(status: number, errorBody: ApiErrorBody) {
    super(errorBody.message || `API Error: ${status}`)
    this.name = 'ApiClientError'
    this.status = status
    this.code = errorBody.code || 'UNKNOWN_ERROR'
    this.details = errorBody.details
  }
}

const BASE_URL =
  (import.meta.env.VITE_API_URL as string) ||
  (import.meta.env.VITE_API_BASE_URL as string) ||
  'http://localhost:8000/api/v1'

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`
  
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorData: ApiResponseError
    try {
      errorData = (await response.json()) as ApiResponseError
    } catch {
      errorData = {
        error: {
          code: `HTTP_${response.status}`,
          message: response.statusText || 'An unexpected network error occurred.',
        },
      }
    }
    throw new ApiClientError(response.status, errorData.error)
  }

  // Handle empty 204 responses
  if (response.status === 204) {
    return {} as T
  }

  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
}
