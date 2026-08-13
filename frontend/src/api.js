const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await safeErrorDetail(response);
    throw new Error(detail || `Upload failed (${response.status})`);
  }

  return response.json();
}

export async function askQuestion(question, documentId) {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, document_id: documentId || null }),
  });

  if (!response.ok) {
    const detail = await safeErrorDetail(response);
    throw new Error(detail || `Query failed (${response.status})`);
  }

  return response.json();
}

export async function listDocuments() {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  if (!response.ok) {
    const detail = await safeErrorDetail(response);
    throw new Error(detail || `Failed to load documents (${response.status})`);
  }
  return response.json();
}

async function safeErrorDetail(response) {
  try {
    const data = await response.json();
    return data.detail;
  } catch {
    return null;
  }
}
