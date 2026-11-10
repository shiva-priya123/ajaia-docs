export const APP_NAME = 'Ajaia Docs';
export const TOKEN_KEY = 'ajaia_token';
export const AUTO_SAVE_DELAY_MS = 1500;
export const DEFAULT_DOC_TITLE = 'Untitled document';
export const TITLE_MAX_LENGTH = 255;

/** Keep in sync with server/app/upload (SUPPORTED_EXTENSIONS, MAX_UPLOAD_BYTES). */
export const IMPORT_EXTENSIONS = ['.txt', '.md', '.docx'] as const;
export const IMPORT_MAX_BYTES = 5 * 1024 * 1024;

export const DEMO_PASSWORD = 'password123';
export const DEMO_ACCOUNTS = [
  { name: 'Alice', email: 'alice@example.com' },
  { name: 'Bob', email: 'bob@example.com' },
  { name: 'Charlie', email: 'charlie@example.com' },
] as const;
