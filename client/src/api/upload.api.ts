import client from './client';
import type { UploadResponse } from '../types';

/** Import a .txt/.md/.docx file as a new document. */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  // Let the browser set the multipart boundary.
  const { data } = await client.post<UploadResponse>('/upload', formData);
  return data;
}
