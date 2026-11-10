import { act, renderHook } from '@testing-library/react';
import { AxiosError, type AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as documentsApi from '../../src/api/documents.api';
import { useAutoSave } from '../../src/hooks/useAutoSave';
import { makeDoc } from '../fixtures';

vi.mock('../../src/api/documents.api');

const DELAY = 1000;
const setup = (enabled = true) =>
  renderHook(() => useAutoSave({ documentId: 'd-1', initialVersion: 'v1', enabled, delayMs: DELAY }));

describe('useAutoSave', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('debounces edits into a single save carrying the base version', async () => {
    vi.mocked(documentsApi.updateDocument).mockResolvedValue(makeDoc({ updated_at: 'v2' }));
    const { result } = setup();

    act(() => {
      result.current.queue({ title: 'Draft' });
      result.current.queue({ content: '{"type":"doc"}' });
    });
    expect(result.current.status).toBe('pending');
    expect(documentsApi.updateDocument).not.toHaveBeenCalled();

    await act(() => vi.advanceTimersByTimeAsync(DELAY));

    expect(documentsApi.updateDocument).toHaveBeenCalledTimes(1);
    expect(documentsApi.updateDocument).toHaveBeenCalledWith('d-1', {
      title: 'Draft',
      content: '{"type":"doc"}',
      expected_updated_at: 'v1',
    });
    expect(result.current.status).toBe('saved');

    // The next save is based on the version the server just returned.
    act(() => result.current.queue({ title: 'Final' }));
    await act(() => vi.advanceTimersByTimeAsync(DELAY));
    expect(documentsApi.updateDocument).toHaveBeenLastCalledWith('d-1', { title: 'Final', expected_updated_at: 'v2' });
  });

  it('stops and reports a conflict instead of overwriting newer changes', async () => {
    const conflict = new AxiosError('Conflict', 'ERR_BAD_REQUEST', undefined, undefined, {
      status: 409,
      data: { detail: 'This document was changed by someone else.' },
    } as AxiosResponse);
    vi.mocked(documentsApi.updateDocument).mockRejectedValueOnce(conflict);
    const { result } = setup();

    act(() => result.current.queue({ content: 'mine' }));
    await act(() => vi.advanceTimersByTimeAsync(DELAY));
    expect(result.current.status).toBe('conflict');
    expect(result.current.error).toMatch(/changed by someone else/);

    // Further typing does not trigger saves while the conflict is unresolved.
    act(() => result.current.queue({ content: 'mine, more' }));
    await act(() => vi.advanceTimersByTimeAsync(DELAY * 3));
    expect(documentsApi.updateDocument).toHaveBeenCalledTimes(1);

    // "Keep mine" force-saves the latest content without a version check.
    vi.mocked(documentsApi.updateDocument).mockResolvedValueOnce(makeDoc({ updated_at: 'v3' }));
    await act(() => result.current.overwrite());
    expect(documentsApi.updateDocument).toHaveBeenLastCalledWith('d-1', { content: 'mine, more' });
    expect(result.current.status).toBe('saved');
  });

  it('keeps unsaved changes after a failure so Retry resends them', async () => {
    vi.mocked(documentsApi.updateDocument)
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(makeDoc({ updated_at: 'v2' }));
    const { result } = setup();

    act(() => result.current.queue({ title: 'Keep me' }));
    await act(() => vi.advanceTimersByTimeAsync(DELAY));
    expect(result.current.status).toBe('error');

    await act(() => result.current.flush());
    expect(documentsApi.updateDocument).toHaveBeenLastCalledWith('d-1', { title: 'Keep me', expected_updated_at: 'v1' });
    expect(result.current.status).toBe('saved');
  });

  it('never saves for read-only users', async () => {
    const { result } = setup(false);
    act(() => result.current.queue({ content: 'x' }));
    await act(() => vi.advanceTimersByTimeAsync(DELAY * 2));
    expect(documentsApi.updateDocument).not.toHaveBeenCalled();
    expect(result.current.status).toBe('idle');
  });
});
