import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  X,
  Search,
  RotateCw,
  Clock,
  FileText,
  AlertCircle,
  PlusCircle,
  ExternalLink,
  Eye,
  ShieldCheck,
} from 'lucide-react';
import {
  selectComplaintList,
  selectComplaintListLoading,
  selectComplaintListError,
  selectComplaintListTotal,
  selectSelectedComplaintId,
  selectDetailLoading,
} from '../../store/selectors';
import { fetchComplaintsThunk, selectComplaintThunk, clearWorkspaceThunk } from '../../store/thunks';

export function ComplaintHistoryDrawer({ isOpen, onClose }) {
  const dispatch = useDispatch();

  const complaintList = useSelector(selectComplaintList);
  const isLoading = useSelector(selectComplaintListLoading);
  const error = useSelector(selectComplaintListError);
  const totalCount = useSelector(selectComplaintListTotal);
  const selectedComplaintId = useSelector(selectSelectedComplaintId);
  const detailLoading = useSelector(selectDetailLoading);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL' | 'DRAFT' | 'COMMITTED'

  // Fetch / refetch when filters change or drawer opens
  useEffect(() => {
    if (isOpen) {
      const statusParam = statusFilter === 'ALL' ? null : statusFilter;
      dispatch(fetchComplaintsThunk({ status: statusParam, search: searchTerm }));
    }
  }, [dispatch, isOpen, statusFilter, searchTerm]);

  const handleRefresh = () => {
    const statusParam = statusFilter === 'ALL' ? null : statusFilter;
    dispatch(fetchComplaintsThunk({ status: statusParam, search: searchTerm }));
  };

  const handleSelectComplaint = (complaintId) => {
    if (complaintId === selectedComplaintId && !detailLoading) {
      onClose();
      return;
    }

    dispatch(selectComplaintThunk(complaintId));

    // Synchronize URL query parameter without page reload
    const url = new URL(window.location);
    url.searchParams.set('complaintId', complaintId);
    window.history.replaceState({}, '', url.toString());

    onClose();
  };

  const handleNewComplaint = () => {
    dispatch(clearWorkspaceThunk());
    const url = new URL(window.location);
    url.searchParams.delete('complaintId');
    window.history.replaceState({}, '', url.pathname);
    onClose();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recently';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="history-drawer-overlay" onClick={onClose}>
      <aside className="history-drawer-panel" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-title-group">
            <div className="drawer-icon-box">
              <FileText size={20} className="drawer-icon" />
            </div>
            <div>
              <h2 className="drawer-title">Complaint History</h2>
              <span className="drawer-subtitle">
                {totalCount} {totalCount === 1 ? 'record' : 'records'} in MySQL
              </span>
            </div>
          </div>
          <div className="drawer-header-actions">
            <button
              type="button"
              className="drawer-icon-btn"
              onClick={handleRefresh}
              disabled={isLoading}
              title="Refresh Complaint List"
            >
              <RotateCw size={17} className={isLoading ? 'spin-icon' : ''} />
            </button>
            <button
              type="button"
              className="drawer-icon-btn close-btn"
              onClick={onClose}
              title="Close Panel"
            >
              <X size={19} />
            </button>
          </div>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="drawer-toolbar">
          <div className="search-box-wrapper">
            <Search size={15} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Search customer, product, batch..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearchTerm('')}
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>

          <div className="filter-pills-row">
            <button
              type="button"
              className={`filter-pill ${statusFilter === 'ALL' ? 'active' : ''}`}
              onClick={() => setStatusFilter('ALL')}
            >
              All
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === 'DRAFT' ? 'active' : ''}`}
              onClick={() => setStatusFilter('DRAFT')}
            >
              Drafts
            </button>
            <button
              type="button"
              className={`filter-pill ${statusFilter === 'COMMITTED' ? 'active' : ''}`}
              onClick={() => setStatusFilter('COMMITTED')}
            >
              Committed
            </button>
          </div>
        </div>

        {/* Drawer Content Body */}
        <div className="drawer-body">
          {/* Loading Skeleton */}
          {isLoading && complaintList.length === 0 && (
            <div className="history-skeleton-list">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="history-skeleton-card">
                  <div className="skeleton-line skeleton-title" />
                  <div className="skeleton-line skeleton-subtitle" />
                  <div className="skeleton-line skeleton-meta" />
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {!isLoading && error && (
            <div className="history-error-card">
              <AlertCircle size={24} className="error-icon" />
              <p className="error-title">Unable to load complaint history</p>
              <p className="error-desc">{error}</p>
              <button type="button" className="retry-btn" onClick={handleRefresh}>
                <RotateCw size={14} />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* Empty State */}
          {!isLoading && !error && complaintList.length === 0 && (
            <div className="history-empty-state">
              <div className="empty-icon-circle">
                <FileText size={32} />
              </div>
              <h3 className="empty-heading">No complaints found</h3>
              <p className="empty-caption">
                {searchTerm || statusFilter !== 'ALL'
                  ? 'No matching complaints found for the applied filter.'
                  : 'No saved complaint records in MySQL. Create your first complaint using the AIVOA Copilot.'}
              </p>
              <button type="button" className="create-new-complaint-btn" onClick={handleNewComplaint}>
                <PlusCircle size={16} />
                <span>Create New Complaint</span>
              </button>
            </div>
          )}

          {/* Complaint Card List */}
          {!error && complaintList.length > 0 && (
            <div className="history-card-list">
              {complaintList.map((item) => {
                const isSelected = item.id === selectedComplaintId;
                const isCommitted = item.status === 'COMMITTED';

                return (
                  <div
                    key={item.id}
                    className={`history-card ${isSelected ? 'is-active' : ''} ${
                      isCommitted ? 'is-committed' : 'is-draft'
                    }`}
                    onClick={() => handleSelectComplaint(item.id)}
                  >
                    {/* Top Row: Customer Name & Status Badge */}
                    <div className="card-top-row">
                      <div className="card-customer">
                        <h4>{item.customer_name || 'Unnamed Customer'}</h4>
                        {isSelected && <span className="active-badge">ACTIVE</span>}
                      </div>
                      <span className={`status-pill pill-${item.status ? item.status.toLowerCase() : 'draft'}`}>
                        {item.status || 'DRAFT'}
                      </span>
                    </div>

                    {/* Middle Row: Product and Batch Info */}
                    <div className="card-product-info">
                      <p className="product-title">
                        {item.product_name || 'No product specified'}
                        {item.strength_grade ? ` • ${item.strength_grade}` : ''}
                      </p>
                      <div className="product-batch-qty">
                        {item.batch_number && (
                          <span className="batch-tag">
                            Batch: <strong>{item.batch_number}</strong>
                          </span>
                        )}
                        {item.affected_quantity && (
                          <span className="qty-tag">
                            Qty: <strong>{item.affected_quantity}</strong>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* QMS Reference if committed */}
                    {isCommitted && item.qms_reference_number && (
                      <div className="card-qms-row">
                        <ShieldCheck size={13} className="qms-icon" />
                        <span className="qms-ref-text">{item.qms_reference_number}</span>
                      </div>
                    )}

                    {/* Bottom Row: Timestamp and Action Button */}
                    <div className="card-bottom-row">
                      <span className="card-timestamp">
                        <Clock size={12} />
                        {formatDate(item.updated_at || item.created_at)}
                      </span>

                      <button
                        type="button"
                        className={`card-action-btn ${isCommitted ? 'btn-view' : 'btn-open'}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectComplaint(item.id);
                        }}
                      >
                        {isCommitted ? (
                          <>
                            <Eye size={13} />
                            <span>View</span>
                          </>
                        ) : (
                          <>
                            <ExternalLink size={13} />
                            <span>Open</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="drawer-footer">
          <button type="button" className="drawer-new-btn" onClick={handleNewComplaint}>
            <PlusCircle size={16} />
            <span>New Complaint Workspace</span>
          </button>
        </div>
      </aside>
    </div>
  );
}

export default ComplaintHistoryDrawer;
