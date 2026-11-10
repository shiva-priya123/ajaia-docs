import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import DocumentCard from '../../src/components/dashboard/DocumentCard';
import { makeDoc } from '../fixtures';

const renderCard = (ui: React.ReactElement) => render(<MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>{ui}</MemoryRouter>);

describe('DocumentCard', () => {
  it('shows an owned document with a preview and a delete action', () => {
    renderCard(<DocumentCard document={makeDoc()} onDelete={vi.fn()} />);

    expect(screen.getByText('Project Roadmap')).toBeInTheDocument();
    expect(screen.getByText('Milestones for the quarter')).toBeInTheDocument();
    expect(screen.getByText('Owned by you')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete project roadmap/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open project roadmap/i })).toHaveAttribute('href', '/documents/d-1');
  });

  it('distinguishes a document shared with view-only access', () => {
    renderCard(
      <DocumentCard document={makeDoc({ role: 'viewer', owner_name: 'Bob', owner_id: 'u-bob' })} onDelete={vi.fn()} />,
    );

    expect(screen.getByText('Shared by Bob')).toBeInTheDocument();
    expect(screen.getByText('View only')).toBeInTheDocument();
    expect(screen.queryByText('Owned by you')).not.toBeInTheDocument();
    // Only owners can delete.
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
  });

  it('labels shared documents the user can edit', () => {
    renderCard(<DocumentCard document={makeDoc({ role: 'editor', owner_name: 'Bob' })} />);
    expect(screen.getByText('Can edit')).toBeInTheDocument();
  });

  it('asks for confirmation before deleting', async () => {
    const onDelete = vi.fn();
    const doc = makeDoc();
    renderCard(<DocumentCard document={doc} onDelete={onDelete} />);

    await userEvent.click(screen.getByRole('button', { name: /delete project roadmap/i }));
    expect(onDelete).not.toHaveBeenCalled();
    expect(screen.getByText('Delete for everyone?')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(onDelete).toHaveBeenCalledWith(doc);
  });

  it('handles empty or malformed content gracefully', () => {
    renderCard(<DocumentCard document={makeDoc({ content: 'not json' })} />);
    expect(screen.getByText('Empty document')).toBeInTheDocument();
  });
});
