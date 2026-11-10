import client from './client';
import type { Permission, Share } from '../types';

export async function getShares(documentId: string): Promise<Share[]> {
  const { data } = await client.get<Share[]>(`/documents/${documentId}/shares`);
  return data;
}

export async function createShare(documentId: string, userId: string, permission: Permission): Promise<Share> {
  const { data } = await client.post<Share>(`/documents/${documentId}/shares`, {
    user_id: userId,
    permission,
  });
  return data;
}

export async function updateShare(documentId: string, shareId: string, permission: Permission): Promise<Share> {
  const { data } = await client.patch<Share>(`/documents/${documentId}/shares/${shareId}`, { permission });
  return data;
}

export async function deleteShare(documentId: string, shareId: string): Promise<void> {
  await client.delete(`/documents/${documentId}/shares/${shareId}`);
}
