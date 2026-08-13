import { useRef, useState } from "react";
import { uploadPdf } from "../api";

export default function UploadPDF({ onUploaded }) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadedFilename, setUploadedFilename] = useState(null);
  const [alreadyIndexed, setAlreadyIndexed] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    try {
      const result = await uploadPdf(file);
      setUploadedFilename(result.filename);
      setAlreadyIndexed(result.already_indexed);
      onUploaded(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div className="upload-panel">
      <label className="upload-button">
        {isUploading ? "Uploading..." : "Upload PDF"}
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={isUploading}
          hidden
        />
      </label>
      {uploadedFilename && !error && (
        <p className="upload-status success">
          {alreadyIndexed
            ? `Already indexed: ${uploadedFilename} (skipped re-processing)`
            : `Indexed: ${uploadedFilename}`}
        </p>
      )}
      {error && <p className="upload-status error">{error}</p>}
    </div>
  );
}
