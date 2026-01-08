/**
 * Context tools component with search, filter, import/export
 */
import React, { useState } from 'react';
import { contextAPI } from './api';
import { ContextStatus, ContextType } from './types';

interface ContextToolsProps {
  onFiltersChange: (filters: {
    search: string;
    type: string;
    tags: string;
    status: string;
  }) => void;
  onRefresh: () => void;
}

export function ContextTools({ onFiltersChange, onRefresh }: ContextToolsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterTags, setFilterTags] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [importing, setImporting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    onFiltersChange({
      search: value,
      type: filterType,
      tags: filterTags,
      status: filterStatus,
    });
  };

  const handleFilterChange = (field: string, value: string) => {
    const newFilters = {
      search: searchTerm,
      type: filterType,
      tags: filterTags,
      status: filterStatus,
      [field]: value,
    };
    
    if (field === 'type') setFilterType(value);
    if (field === 'tags') setFilterTags(value);
    if (field === 'status') setFilterStatus(value);
    
    onFiltersChange(newFilters);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setFilterType('');
    setFilterTags('');
    setFilterStatus('');
    onFiltersChange({ search: '', type: '', tags: '', status: '' });
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await contextAPI.exportContexts(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contexts_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSuccess(`Exported contexts as ${format.toUpperCase()}`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(`Failed to export contexts`);
      setTimeout(() => setError(null), 3000);
      console.error(err);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setError('Only JSON files are supported');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setImporting(true);
      const result = await contextAPI.importContexts(file, false);
      
      setSuccess(
        `Imported ${result.imported} contexts` +
        (result.skipped > 0 ? `, skipped ${result.skipped}` : '')
      );
      setTimeout(() => setSuccess(null), 5000);
      
      onRefresh();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to import contexts';
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
      console.error(err);
    } finally {
      setImporting(false);
      // Reset file input
      event.target.value = '';
    }
  };

  return (
    <div className="context-tools">
      {success && <div className="alert alert-success">{success}</div>}
      {error && <div className="alert alert-error">{error}</div>}
      
      <div className="tools-section">
        <h3>🔍 Search & Filter</h3>
        
        <div className="form-group">
          <input
            type="text"
            className="search-input"
            placeholder="Search contexts..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
        </div>

        <div className="filter-row">
          <div className="form-group">
            <label>Type</label>
            <select
              value={filterType}
              onChange={(e) => handleFilterChange('type', e.target.value)}
            >
              <option value="">All Types</option>
              <option value={ContextType.PREFERENCE}>Preference</option>
              <option value={ContextType.GOAL}>Goal</option>
              <option value={ContextType.DECISION}>Decision</option>
              <option value={ContextType.FACT}>Fact</option>
            </select>
          </div>

          <div className="form-group">
            <label>Tags</label>
            <input
              type="text"
              placeholder="Comma-separated tags"
              value={filterTags}
              onChange={(e) => handleFilterChange('tags', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Status</label>
            <select
              value={filterStatus}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All</option>
              <option value={ContextStatus.ACTIVE}>Active</option>
              <option value={ContextStatus.SUPERSEDED}>Superseded</option>
            </select>
          </div>

          <div className="form-group">
            <label>&nbsp;</label>
            <button 
              className="button button-small"
              onClick={handleClearFilters}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="tools-section">
        <h3>📤 Import / Export</h3>
        
        <div className="button-group">
          <button 
            className="button button-secondary"
            onClick={() => handleExport('json')}
          >
            Export as JSON
          </button>
          
          <button 
            className="button button-secondary"
            onClick={() => handleExport('csv')}
          >
            Export as CSV
          </button>
          
          <label className="button button-secondary file-upload-button">
            {importing ? 'Importing...' : 'Import from JSON'}
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              disabled={importing}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>
    </div>
  );
}
