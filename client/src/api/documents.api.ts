import client from './client';
import type { Document } from '../types';

export interface DocumentUpdatePayload {
  title?: string;
  content?: string;
  /** The `updated_at` this client last saw; the server returns 409 if it's stale. */
  expected_updated_at?: string;
}

export async function getDocuments(): Promise<Document[]> {
  const { data } = await client.get<Document[]>('/documents');
  return data;
}

export async function getDocument(id: string): Promise<Document> {
  const { data } = await client.get<Document>(`/documents/${id}`);
  return data;
}

export async function createDocument(title: string): Promise<Document> {
  const { data } = await client.post<Document>('/documents', { title });
  return data;
}

export async function updateDocument(id: string, payload: DocumentUpdatePayload): Promise<Document> {
  const { data } = await client.put<Document>(`/documents/${id}`, payload);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await client.delete(`/documents/${id}`);
}
