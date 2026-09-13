import { apiClient } from "./client";
import type { ApplicationResponse } from "../types/application";

export async function uploadApplication(file: File): Promise<ApplicationResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<ApplicationResponse>(
    "/api/v1/applications/upload",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );

  return response.data;
}