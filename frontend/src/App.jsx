import { useState } from "react";
import UploadPDF from "./components/UploadPDF.jsx";
import ChatBox from "./components/ChatBox.jsx";
import DocumentList from "./components/DocumentList.jsx";

export default function App() {
  const [documentId, setDocumentId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploaded = (result) => {
    setDocumentId(result.document_id);
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="app-layout">
      <DocumentList
        selectedDocumentId={documentId}
        onSelect={setDocumentId}
        refreshKey={refreshKey}
      />

      <div className="app-shell">
        <header>
          <h1>RAG on Azure</h1>
          <p className="subtitle">Upload a PDF and ask questions about it.</p>
        </header>

        <UploadPDF onUploaded={handleUploaded} />

        <ChatBox documentId={documentId} />
      </div>
    </div>
  );
}
