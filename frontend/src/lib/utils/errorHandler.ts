/**
 * API error handling utilities
 */
import axios, { AxiosError } from "axios";

export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;

    if (axiosError.response) {
      const status = axiosError.response.status;
      const data = axiosError.response.data as any;

      // Validation errors (422)
      if (status === 422) {
        if (Array.isArray(data.detail)) {
          return data.detail.map((err: any) => err.msg).join(", ");
        }
        return data.detail || "Validation error";
      }

      // Bad request (400)
      if (status === 400) {
        return data.detail || "Bad request";
      }

      // Server error (500)
      if (status === 500) {
        return data.detail || "Server error. Please try again later.";
      }

      // Other errors
      return data.detail || data.message || `Error ${status}`;
    }

    // Network error
    if (axiosError.request) {
      return "Cannot connect to server. Please check your connection.";
    }
  }

  // Generic error
  return error instanceof Error ? error.message : "An unexpected error occurred";
}

export function formatValidationErrors(errors: any[]): string {
  if (!Array.isArray(errors)) return "Validation failed";

  return errors
    .map((err) => {
      const field = err.loc?.join(".") || "field";
      return `${field}: ${err.msg}`;
    })
    .join("; ");
}
