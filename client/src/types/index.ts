export interface User {
  id: string;
  name: string;
  email: string;
}

export type Role = 'owner' | 'editor' | 'viewer';
export type Permission = 'viewer' | 'editor';

export interface Document {
  id: string;
  title: string;
  /** TipTap JSON, serialised as a string by the API. */
  content: string | null;
  owner_id: string;
  owner_name: string;
  role: Role;
  created_at: string;
  updated_at: string;
}

export interface Share {
  id: string;
  document_id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  permission: Permission;
  created_at: string;
}

export interface UploadResponse {
  document_id: string;
  title: string;
  message: string;
}
