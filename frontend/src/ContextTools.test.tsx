import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ContextTools } from './ContextTools';
import { render } from './test/render-with-providers';

const mockExportContexts = vi.fn();
const mockImportContexts = vi.fn();

vi.mock('./api', () => ({
  contextAPI: {
    exportContexts: (...args: unknown[]) => mockExportContexts(...args),
    importContexts: (...args: unknown[]) => mockImportContexts(...args),
  },
}));

describe('ContextTools', () => {
  const onFiltersChange = vi.fn();
  const onRefresh = vi.fn();
  const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL');
  const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL');
  const anchorClickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});

  beforeEach(() => {
    vi.clearAllMocks();
    createObjectURLSpy.mockReturnValue('blob:mock-url');
  });

  it('renders search and filter controls', () => {
    render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    expect(screen.getByPlaceholderText(/search contexts/i)).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Tags')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getAllByRole('combobox')).toHaveLength(2);
  });

  it('updates search filter', async () => {
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.type(screen.getByPlaceholderText(/search contexts/i), 'python');

    expect(onFiltersChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: 'python' })
    );
  });

  it('updates type filter', async () => {
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    const typeSelect = screen.getAllByRole('combobox')[0];
    await user.selectOptions(typeSelect, 'goal');

    expect(onFiltersChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ type: 'goal' })
    );
  });

  it('updates tags filter', async () => {
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.type(screen.getByPlaceholderText(/comma-separated tags/i), 'ts,react');

    expect(onFiltersChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ tags: 'ts,react' })
    );
  });

  it('updates status filter', async () => {
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    const statusSelect = screen.getAllByRole('combobox')[1];
    await user.selectOptions(statusSelect, 'active');

    expect(onFiltersChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ status: 'active' })
    );
  });

  it('clears all filters when clear button is clicked', async () => {
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    await user.type(screen.getByPlaceholderText(/search contexts/i), 'abc');
    const typeSelect = screen.getAllByRole('combobox')[0];
    await user.selectOptions(typeSelect, 'fact');
    await user.click(screen.getByRole('button', { name: /clear filters/i }));

    expect(onFiltersChange).toHaveBeenLastCalledWith({
      search: '',
      type: '',
      tags: '',
      status: '',
    });
    expect(screen.getByPlaceholderText(/search contexts/i)).toHaveValue('');
  });

  it('exports contexts as JSON', async () => {
    mockExportContexts.mockResolvedValue(new Blob(['{}'], { type: 'application/json' }));

    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.click(screen.getByRole('button', { name: /export as json/i }));

    await waitFor(() => {
      expect(mockExportContexts).toHaveBeenCalledWith('json');
    });
    expect(anchorClickSpy).toHaveBeenCalled();
    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalled();
  });

  it('exports contexts as CSV', async () => {
    mockExportContexts.mockResolvedValue(new Blob(['id,type'], { type: 'text/csv' }));

    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.click(screen.getByRole('button', { name: /export as csv/i }));

    await waitFor(() => {
      expect(mockExportContexts).toHaveBeenCalledWith('csv');
    });
    expect(anchorClickSpy).toHaveBeenCalled();
  });

  it('shows success alert after successful export', async () => {
    mockExportContexts.mockResolvedValue(new Blob(['{}'], { type: 'application/json' }));

    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.click(screen.getByRole('button', { name: /export as json/i }));

    await waitFor(() => {
      expect(screen.getByText(/exported contexts as json/i)).toBeInTheDocument();
    });
  });

  it('shows export error alert on failure', async () => {
    mockExportContexts.mockRejectedValue(new Error('boom'));

    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    await user.click(screen.getByRole('button', { name: /export as json/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to export contexts/i)).toBeInTheDocument();
    });
  });

  it('imports valid json file and refreshes contexts', async () => {
    mockImportContexts.mockResolvedValue({ imported: 2, skipped: 1, errors: [], total_errors: 0 });
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['{}'], 'contexts.json', { type: 'application/json' });
    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(mockImportContexts).toHaveBeenCalledWith(file, false);
      expect(onRefresh).toHaveBeenCalled();
    });
    expect(screen.getByText(/imported 2 contexts, skipped 1/i)).toBeInTheDocument();
  });

  it('shows import success without skipped count when zero skipped', async () => {
    mockImportContexts.mockResolvedValue({ imported: 3, skipped: 0, errors: [], total_errors: 0 });
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(['{}'], 'contexts.json', { type: 'application/json' }));

    await waitFor(() => {
      expect(screen.getByText(/imported 3 contexts$/i)).toBeInTheDocument();
    });
  });

  it('rejects non-json files', async () => {
    render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const invalidFile = new File(['txt'], 'contexts.txt', { type: 'text/plain' });
    fireEvent.change(fileInput, { target: { files: [invalidFile] } });

    expect(mockImportContexts).not.toHaveBeenCalled();
    expect(screen.getByText(/only json files are supported/i)).toBeInTheDocument();
  });

  it('shows backend detail message on import failure', async () => {
    mockImportContexts.mockRejectedValue({ response: { data: { detail: 'bad payload' } } });
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(['{}'], 'contexts.json', { type: 'application/json' }));

    await waitFor(() => {
      expect(screen.getByText('bad payload')).toBeInTheDocument();
    });
  });

  it('shows generic import failure when detail is absent', async () => {
    mockImportContexts.mockRejectedValue(new Error('failed'));
    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(['{}'], 'contexts.json', { type: 'application/json' }));

    await waitFor(() => {
      expect(screen.getByText(/failed to import contexts/i)).toBeInTheDocument();
    });
  });

  it('disables import input while importing', async () => {
    let resolveImport: ((value: unknown) => void) | null = null;
    mockImportContexts.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveImport = resolve;
        })
    );

    const { user } = render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(['{}'], 'contexts.json', { type: 'application/json' }));

    await waitFor(() => {
      expect(screen.getByText(/importing/i)).toBeInTheDocument();
      expect(fileInput).toBeDisabled();
    });

    resolveImport?.({ imported: 1, skipped: 0, errors: [], total_errors: 0 });
  });

  it('handles empty file selection gracefully', async () => {
    render(<ContextTools onFiltersChange={onFiltersChange} onRefresh={onRefresh} />);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

    await waitFor(() => {
      expect(fileInput).toBeInTheDocument();
    });

    const event = new Event('change', { bubbles: true });
    Object.defineProperty(fileInput, 'files', { value: [], configurable: true });
    fileInput.dispatchEvent(event);

    expect(mockImportContexts).not.toHaveBeenCalled();
  });
});
