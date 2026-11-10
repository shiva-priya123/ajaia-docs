import { IMPORT_EXTENSIONS, IMPORT_MAX_BYTES } from './constants';

/** Client-side pre-check so users get instant feedback; the server re-validates. */
export function validateImportFile(file: File): string | null {
  const name = file.name.toLowerCase();
  const ext = name.includes('.') ? name.slice(name.lastIndexOf('.')) : '';
  if (!(IMPORT_EXTENSIONS as readonly string[]).includes(ext)) {
    return `“${file.name}” isn't supported. You can import ${IMPORT_EXTENSIONS.join(', ')} files.`;
  }
  if (file.size === 0) return `“${file.name}” is empty.`;
  if (file.size > IMPORT_MAX_BYTES) {
    return `“${file.name}” is larger than ${IMPORT_MAX_BYTES / (1024 * 1024)} MB.`;
  }
  return null;
}
