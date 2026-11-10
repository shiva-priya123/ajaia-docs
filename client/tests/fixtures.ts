import type { Document, User } from '../src/types';

export const alice: User = { id: 'u-alice', name: 'Alice', email: 'alice@example.com' };

const doc = (text: string) =>
  JSON.stringify({ type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text }] }] });

export function makeDoc(overrides: Partial<Document> = {}): Document {
  return {
    id: 'd-1',
    title: 'Project Roadmap',
    content: doc('Milestones for the quarter'),
    owner_id: alice.id,
    owner_name: 'Alice',
    role: 'owner',
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
    ...overrides,
  };
}
