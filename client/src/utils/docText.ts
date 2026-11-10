interface PMNode {
  type?: string;
  text?: string;
  content?: PMNode[];
}

/** Plain-text preview of a TipTap JSON document (for dashboard cards). */
export function extractPlainText(content: string | null, maxLength = 160): string {
  if (!content) return '';
  let root: PMNode;
  try {
    root = JSON.parse(content) as PMNode;
  } catch {
    return '';
  }
  const parts: string[] = [];
  let length = 0;
  const walk = (node: PMNode): void => {
    if (length > maxLength) return;
    if (node.type === 'text' && node.text) {
      parts.push(node.text);
      length += node.text.length;
      return;
    }
    node.content?.forEach(walk);
    // Separate block-level nodes with a space.
    if (node.type !== 'text' && node.type !== 'doc') {
      parts.push(' ');
      length += 1;
    }
  };
  walk(root);
  const text = parts.join('').replace(/\s+/g, ' ').trim();
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}…` : text;
}

/** Parse stored content for the editor, falling back to an empty document. */
export function parseDocContent(content: string | null): object {
  const empty = { type: 'doc', content: [{ type: 'paragraph' }] };
  if (!content) return empty;
  try {
    const parsed = JSON.parse(content) as { type?: string; content?: unknown[] };
    if (parsed?.type !== 'doc') return empty;
    // A doc must contain at least one block for ProseMirror.
    if (!Array.isArray(parsed.content) || parsed.content.length === 0) return empty;
    return parsed;
  } catch {
    return empty;
  }
}
