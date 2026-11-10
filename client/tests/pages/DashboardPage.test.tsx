import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as documentsApi from '../../src/api/documents.api';
import * as uploadApi from '../../src/api/upload.api';
import { AuthContext, type AuthContextValue } from '../../src/contexts/AuthContext';
import DashboardPage from '../../src/pages/DashboardPage';
import { alice, makeDoc } from '../fixtures';

vi.mock('../../src/api/documents.api');
vi.mock('../../src/api/upload.api');

const auth: AuthContextValue = { user: alice, loading: false, login: vi.fn(), logout: vi.fn() };

function EditorStub() {
  const { id } = useParams();
  return <p>Editor for {id}</p>;
}

function renderDashboard() {
  return render(
    <AuthContext.Provider value={auth}>
      <MemoryRouter initialEntries={['/']} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/documents/:id" element={<EditorStub />} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(documentsApi.getDocuments).mockResolvedValue([
      makeDoc({ id: 'own-1', title: 'My Plan', updated_at: '2026-10-02T10:00:00Z' }),
      makeDoc({ id: 'shr-1', title: "Bob's Notes", role: 'viewer', owner_id: 'u-bob', owner_name: 'Bob' }),
    ]);
  });

  it('separates owned documents from documents shared with me', async () => {
    renderDashboard();

    const ownedTab = await screen.findByRole('tab', { name: /my documents/i });
    expect(within(ownedTab).getByText('1')).toBeInTheDocument();
    expect(await screen.findByText('My Plan')).toBeInTheDocument();
    expect(screen.queryByText("Bob's Notes")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('tab', { name: /shared with me/i }));
    expect(screen.getByText("Bob's Notes")).toBeInTheDocument();
    expect(screen.getByText('Shared by Bob')).toBeInTheDocument();
    expect(screen.queryByText('My Plan')).not.toBeInTheDocument();
  });

  it('creates a new document and opens it', async () => {
    vi.mocked(documentsApi.createDocument).mockResolvedValue(makeDoc({ id: 'new-1', title: 'Untitled document' }));
    renderDashboard();

    await userEvent.click(await screen.findByRole('button', { name: /new document/i }));
    expect(documentsApi.createDocument).toHaveBeenCalledWith('Untitled document');
    expect(await screen.findByText('Editor for new-1')).toBeInTheDocument();
  });

  it('rejects unsupported file types before uploading', async () => {
    const user = userEvent.setup({ applyAccept: false });
    renderDashboard();
    await screen.findByText('My Plan');

    const pdf = new File(['%PDF'], 'report.pdf', { type: 'application/pdf' });
    await user.upload(screen.getByTestId('import-input'), pdf);

    expect(await screen.findByRole('alert')).toHaveTextContent(/isn't supported.*\.txt, \.md, \.docx/i);
    expect(uploadApi.uploadFile).not.toHaveBeenCalled();
  });

  it('imports a supported file and opens the new document', async () => {
    vi.mocked(uploadApi.uploadFile).mockResolvedValue({
      document_id: 'imp-1',
      title: 'notes',
      message: 'ok',
    });
    const user = userEvent.setup();
    renderDashboard();
    await screen.findByText('My Plan');

    const md = new File(['# Hello'], 'notes.md', { type: 'text/markdown' });
    await user.upload(screen.getByTestId('import-input'), md);

    expect(uploadApi.uploadFile).toHaveBeenCalledWith(md);
    expect(await screen.findByText('Editor for imp-1')).toBeInTheDocument();
  });

  it('shows a retryable error when documents fail to load', async () => {
    vi.mocked(documentsApi.getDocuments).mockRejectedValueOnce(new Error('Network down'));
    renderDashboard();
    expect(await screen.findByRole('alert')).toHaveTextContent('Network down');
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('My Plan')).toBeInTheDocument();
  });
});
