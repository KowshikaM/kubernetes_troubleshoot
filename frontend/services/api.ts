import axios from "axios";

import type { HealthResponse } from "@/types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

export const apiClient = axios.create({
  baseURL: baseUrl,
  timeout: 10_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}
