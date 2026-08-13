import { useEffect, useState } from "react";
import { listDocuments } from "../api";

export default function DocumentList({ selectedDocumentId, onSelect, refreshKey }) {
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((err) => setError(err.message));
  }, [refreshKey]);

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
            {doc.filename}
            <span className="chunk-count">{doc.chunk_count}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
