import { useState } from "react";
import { askQuestion } from "../api";

export default function ChatBox({ documentId }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]); // { role: "user"|"assistant", text, sources? }
  const [isAsking, setIsAsking] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setQuestion("");
    setIsAsking(true);

    try {
      const result = await askQuestion(trimmed, documentId);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message}`, sources: [] },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty">Upload a PDF, then ask a question about it.</p>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`chat-message ${message.role}`}>
            <p>{message.text}</p>
            {message.sources && message.sources.length > 0 && (
              <div className="sources">
                <strong>Sources:</strong>
                <ul>
                  {message.sources.map((source) => (
                    <li key={source.chunk_id}>
                      {source.filename}
                      {source.page ? ` (page ${source.page})` : ""} — "
                      {source.excerpt.slice(0, 120)}..."
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {isAsking && <p className="chat-message assistant pending">Thinking...</p>}
      </div>

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about the document..."
          disabled={isAsking}
        />
        <button type="submit" disabled={isAsking || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  );
}
