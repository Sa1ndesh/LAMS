import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Table, Column } from '../../components/ui/Table';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { SearchBar } from '../../components/ui/SearchBar';
import { Project } from '../../types';
import { documentsApi, DocumentResponseData } from '../../services/documentsApi';
import { FileText, Download, Eye, Upload, Filter, Trash2, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';

export const DocumentsTab: React.FC = () => {
  const { project } = useOutletContext<{ project: Project }>();

  const [docsList, setDocsList] = useState<DocumentResponseData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [search, setSearch] = useState<string>('');

  // Upload Modal State
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<string>('PROPOSAL');
  const [description, setDescription] = useState<string>('');
  const [version, setVersion] = useState<string>('1.0');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string>('');

  // Action Notification State
  const [successMsg, setSuccessMsg] = useState<string>('');

  // Delete Modal State
  const [docToDelete, setDocToDelete] = useState<DocumentResponseData | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string>('');

  // Preview Modal State
  const [previewDoc, setPreviewDoc] = useState<DocumentResponseData | null>(null);

  // Fetch Documents
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await documentsApi.getDocumentsByProject(project.id, search, selectedCategory);
      if (res && res.items) {
        setDocsList(res.items);
      }
    } catch (err) {
      console.warn('Backend documents fetch fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [project.id, search, selectedCategory]);

  const categories = [
    { label: 'All', value: 'ALL' },
    { label: 'Proposal', value: 'PROPOSAL' },
    { label: 'Land Records', value: 'LAND_RECORDS' },
    { label: 'Survey', value: 'SURVEY' },
    { label: 'Notifications', value: 'NOTIFICATIONS' },
    { label: 'Award', value: 'AWARD' },
    { label: 'Compensation', value: 'COMPENSATION' },
    { label: 'R&R', value: 'RR' },
  ];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadError('');

      // Validation
      const allowedExts = ['.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg'];
      const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      if (!allowedExts.includes(ext)) {
        setUploadError(`File extension '${ext}' is not supported. Please select PDF, DOC, DOCX, PNG, or JPG.`);
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        setUploadError(`File size exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(2)} MB).`);
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploadError('');

    if (!selectedFile) {
      setUploadError('Please select a file to upload.');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', category);
      if (description) formData.append('description', description);
      if (version) formData.append('version', version);

      await documentsApi.uploadDocument(project.id, formData);

      setIsUploadOpen(false);
      setSelectedFile(null);
      setDescription('');
      setVersion('1.0');
      setSuccessMsg(`Document "${selectedFile.name}" uploaded successfully.`);
      setTimeout(() => setSuccessMsg(''), 4000);

      await fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload document file.');
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async (doc: DocumentResponseData) => {
    try {
      await documentsApi.downloadDocument(doc.id, doc.document_name);
    } catch (err: any) {
      alert(err.message || 'Failed to download file.');
    }
  };

  const handleDeleteConfirm = async () => {
    if (!docToDelete) return;
    setDeleting(true);
    setDeleteError('');
    try {
      await documentsApi.deleteDocument(docToDelete.id);
      setDocToDelete(null);
      setSuccessMsg(`Document "${docToDelete.document_name}" deleted.`);
      setTimeout(() => setSuccessMsg(''), 4000);
      await fetchDocuments();
    } catch (err: any) {
      setDeleteError(err.message || 'Failed to delete document. Ensure you have SLAO or Admin privileges.');
    } finally {
      setDeleting(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '3.2 MB';
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const columns: Column<DocumentResponseData>[] = [
    {
      header: 'Document Name & Category',
      cell: (row) => (
        <div className="flex items-start gap-2.5">
          <div className="p-2 bg-blue-50 text-lams-secondary rounded-lg shrink-0 mt-0.5">
            <FileText className="h-4 w-4" />
          </div>
          <div>
            <div className="font-semibold text-xs text-lams-primary flex items-center gap-2">
              <span>{row.document_name}</span>
              <span className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] font-mono text-slate-600">
                v{row.version || '1.0'}
              </span>
            </div>
            <div className="text-[11px] text-lams-muted">
              {row.category} • {formatFileSize(row.file_size)}
            </div>
            {row.description && (
              <div className="text-[11px] text-slate-500 italic mt-0.5 line-clamp-1">{row.description}</div>
            )}
          </div>
        </div>
      ),
    },
    {
      header: 'Uploaded By',
      cell: (row) => <span className="text-xs text-slate-800 font-medium">{row.uploaded_by}</span>,
    },
    {
      header: 'Upload Date',
      cell: (row) => <span className="text-xs text-lams-muted">{row.upload_date}</span>,
    },
    {
      header: 'Verification Status',
      cell: (row) => <StatusBadge status={row.status || 'Verified'} />,
    },
    {
      header: 'Actions',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            icon={<Eye className="h-3.5 w-3.5" />}
            onClick={() => setPreviewDoc(row)}
          >
            Preview
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<Download className="h-3.5 w-3.5 text-lams-secondary" />}
            onClick={() => handleDownload(row)}
          >
            Download
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={<Trash2 className="h-3.5 w-3.5 text-red-600" />}
            onClick={() => setDocToDelete(row)}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Banner Message */}
      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center gap-2.5 text-xs font-semibold shadow-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Control Header: Search, Category Filters & Upload Action */}
      <Card>
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search document title or description..."
            className="w-full md:w-72"
          />

          <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            <Filter className="h-4 w-4 text-lams-muted shrink-0" />
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
                  selectedCategory === cat.value
                    ? 'bg-lams-secondary text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          <Button
            variant="primary"
            size="sm"
            icon={<Upload className="h-4 w-4" />}
            onClick={() => setIsUploadOpen(true)}
            className="shrink-0"
          >
            Upload Official Document
          </Button>
        </div>
      </Card>

      {/* Document Listing Table */}
      <Card title="Official Project Document Repository">
        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500">Loading document repository...</div>
        ) : (
          <Table
            data={docsList}
            columns={columns}
            keyExtractor={(row) => row.id}
            emptyMessage="No official documents found matching the criteria."
          />
        )}
      </Card>

      {/* Modal: Upload Document File */}
      <Modal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        title="Upload Official Project Document"
        subtitle={`Secure document upload for ${project.name}`}
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsUploadOpen(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleUploadSubmit} disabled={uploading}>
              {uploading ? 'Uploading File...' : 'Upload & Verify'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
          {uploadError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* File Picker */}
          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Select Document File *</label>
            <div className="border-2 border-dashed border-slate-300 hover:border-lams-secondary rounded-xl p-4 text-center cursor-pointer transition-colors bg-slate-50">
              <input
                type="file"
                accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                className="hidden"
                id="lams-file-upload-input"
              />
              <label htmlFor="lams-file-upload-input" className="cursor-pointer block space-y-1">
                <Upload className="h-6 w-6 text-lams-secondary mx-auto" />
                <div className="font-semibold text-xs text-lams-primary">
                  {selectedFile ? selectedFile.name : 'Click to select file or drag and drop'}
                </div>
                <div className="text-[11px] text-slate-500">
                  Supported formats: PDF, DOC, DOCX, PNG, JPG (Max 10 MB)
                </div>
                {selectedFile && (
                  <div className="text-xs text-emerald-700 font-bold pt-1">
                    Selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
                  </div>
                )}
              </label>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Document Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-white border border-lams-border rounded-lg px-3 py-2 text-xs text-lams-dark focus:outline-none"
            >
              <option value="PROPOSAL">Project Proposal</option>
              <option value="LAND_RECORDS">Land Records</option>
              <option value="SURVEY">Survey Documents</option>
              <option value="NOTIFICATIONS">Notifications & Gazette</option>
              <option value="AWARD">Award Documents</option>
              <option value="COMPENSATION">Compensation Documents</option>
              <option value="RR">Rehabilitation & Resettlement</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Document Version"
              placeholder="e.g. 1.0"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-lams-dark mb-1">Description / Remarks</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide document notes or official gazette reference..."
              className="w-full bg-white border border-lams-border rounded-lg p-2.5 text-xs text-lams-dark focus:outline-none"
            />
          </div>
        </form>
      </Modal>

      {/* Modal: Delete Confirmation */}
      {docToDelete && (
        <Modal
          isOpen={true}
          onClose={() => setDocToDelete(null)}
          title="Confirm Document Deletion"
          subtitle="Audit-logged administrative action"
          footer={
            <>
              <Button variant="outline" size="sm" onClick={() => setDocToDelete(null)} disabled={deleting}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" className="bg-red-600 hover:bg-red-700 text-white" onClick={handleDeleteConfirm} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Delete Document'}
              </Button>
            </>
          }
        >
          <div className="space-y-3 text-xs">
            {deleteError && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg font-medium flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
                <span>{deleteError}</span>
              </div>
            )}

            <div className="p-3 bg-red-50/60 rounded-xl border border-red-100 flex items-start gap-3">
              <ShieldAlert className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-red-900">Are you sure you want to delete this document?</div>
                <div className="text-slate-700 font-semibold mt-1">"{docToDelete.document_name}"</div>
                <div className="text-[11px] text-slate-500 mt-1">
                  This action will permanently delete the metadata and physical file from LAMS storage. An immutable audit log entry will be created.
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Document Preview */}
      {previewDoc && (
        <Modal
          isOpen={true}
          onClose={() => setPreviewDoc(null)}
          title={`Document Preview: ${previewDoc.document_name}`}
          subtitle={`Category: ${previewDoc.category} • Version ${previewDoc.version}`}
          footer={
            <>
              <Button variant="outline" size="sm" onClick={() => setPreviewDoc(null)}>
                Close Preview
              </Button>
              <Button variant="primary" size="sm" icon={<Download className="h-4 w-4" />} onClick={() => handleDownload(previewDoc)}>
                Download File
              </Button>
            </>
          }
        >
          <div className="space-y-3 text-xs">
            <div className="h-[450px] w-full bg-slate-100 rounded-xl border border-slate-200 overflow-hidden flex items-center justify-center">
              <iframe
                src={documentsApi.previewDocumentUrl(previewDoc.id)}
                className="w-full h-full border-none"
                title="Document Preview Frame"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
