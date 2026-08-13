import { useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "../api";

export default function DocumentList({ selectedDocumentId, onSelect, refreshKey, onDeleted }) {
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((err) => setError(err.message));
  }, [refreshKey]);

  const handleDelete = async (event, doc) => {
    event.stopPropagation(); // don't trigger onSelect
    if (!window.confirm(`Delete "${doc.filename}"? This removes it from search and storage.`)) {
      return;
    }

    setDeletingId(doc.document_id);
    setError(null);
    try {
      await deleteDocument(doc.document_id);
      setDocuments((prev) => prev.filter((d) => d.document_id !== doc.document_id));
      if (selectedDocumentId === doc.document_id) {
        onSelect(null);
      }
      onDeleted?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside className="document-sidebar">
      <h2>Documents</h2>
      {error && <p className="upload-status error">{error}</p>}
      {documents.length === 0 && !error && (
        <p className="sidebar-empty">No documents uploaded yet.</p>
      )}
      <ul>
        <li
          className={!selectedDocumentId ? "active" : ""}
          onClick={() => onSelect(null)}
        >
          All documents
        </li>
        {documents.map((doc) => (
          <li
            key={doc.document_id}
            className={selectedDocumentId === doc.document_id ? "active" : ""}
            onClick={() => onSelect(doc.document_id)}
            title={doc.filename}
          >
            <span className="doc-name">{doc.filename}</span>
            <span className="chunk-count">{doc.chunk_count}</span>
            <button
              type="button"
              className="delete-doc-button"
              title="Delete document"
              onClick={(e) => handleDelete(e, doc)}
              disabled={deletingId === doc.document_id}
            >
              {deletingId === doc.document_id ? "…" : "✕"}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
