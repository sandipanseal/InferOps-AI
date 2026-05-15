"use client";

import { useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost, apiUploadFile } from "@/lib/api";

type DocumentRow = {
  document_id?: string;
  document_name: string;
  filename?: string;
  source_type?: string;
  chunks: number;
};

type MatchRow = {
  document_id?: string;
  document_name: string;
  filename?: string;
  source_type?: string;
  chunk_index: number;
  chunk_text: string;
  score: number;
};

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [documentName, setDocumentName] = useState("deployment_runbook");
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [selectedDocument, setSelectedDocument] = useState("");
  const [matches, setMatches] = useState<MatchRow[]>([]);
  const [status, setStatus] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMode, setUploadMode] = useState<"file" | "text">("file");
  const [loading, setLoading] = useState(false);

  async function loadDocuments() {
    try {
      const data = await apiGet("/v1/rag/documents");
      setDocuments(data);
    } catch (e: any) {
      setStatus(`Failed to load documents: ${e.message}`);
    }
  }

  async function uploadTextDocument() {
    if (!documentName.trim() || !text.trim()) {
      setStatus("Please provide a document name and text.");
      return;
    }

    setLoading(true);
    setStatus("Uploading text, chunking, embedding, and storing in Qdrant...");

    try {
      const data: any = await apiPost("/v1/rag/upload-text", {
        document_name: documentName.trim(),
        text,
      });

      setStatus(
        `Uploaded ${data.document_name}. Created ${data.chunks_created} chunks and indexed ${data.characters_indexed} characters.`
      );

      setText("");
      await loadDocuments();
    } catch (e: any) {
      setStatus(`Upload failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function uploadFileDocument() {
    if (!selectedFile) {
      setStatus("Please select a PDF, DOCX, TXT, or MD file first.");
      return;
    }

    setLoading(true);
    setStatus("Uploading file, extracting text, chunking, embedding, and storing in Qdrant...");

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("document_name", documentName.trim() || selectedFile.name);

      const data: any = await apiUploadFile("/v1/rag/upload-file", formData);

      setStatus(
        `Uploaded ${data.filename}. Extracted ${data.extracted_characters} characters and created ${data.chunks_created} chunks.`
      );

      setSelectedFile(null);
      await loadDocuments();
    } catch (e: any) {
      setStatus(`Upload failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function queryKnowledge() {
    if (!query.trim()) {
      setStatus("Please enter a question.");
      return;
    }

    setLoading(true);
    setStatus("Searching uploaded documents...");

    try {
      const data: any = await apiPost("/v1/rag/query", {
        query,
        top_k: 5,
        document_name: selectedDocument || null,
      });

      setMatches(data.matches);
      setStatus(`Found ${data.matches.length} relevant chunks.`);
    } catch (e: any) {
      setStatus(`Search failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function deleteDocument(documentNameToDelete: string) {
    setLoading(true);
    setStatus(`Deleting ${documentNameToDelete}...`);

    try {
      await apiDelete(`/v1/rag/documents/${encodeURIComponent(documentNameToDelete)}`);
      setStatus(`Deleted ${documentNameToDelete}.`);
      setMatches([]);
      await loadDocuments();
    } catch (e: any) {
      setStatus(`Delete failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function clearKnowledgeBase() {
    setLoading(true);
    setStatus("Clearing knowledge base...");

    try {
      await apiDelete("/v1/rag/clear");
      setStatus("Knowledge base cleared.");
      setMatches([]);
      setDocuments([]);
    } catch (e: any) {
      setStatus(`Clear failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold">Knowledge Base</h2>
          <p className="mt-2 text-slate-600">
            Upload PDF, DOCX, TXT, and Markdown documents into Qdrant for document-grounded RAG answers.
          </p>
        </div>

        <button
          onClick={clearKnowledgeBase}
          disabled={loading || documents.length === 0}
          className="rounded-xl border bg-white px-4 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
        >
          Clear KB
        </button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-8">
        <div className="rounded-2xl bg-white border shadow-sm p-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Upload Knowledge</h3>

            <div className="flex rounded-xl border overflow-hidden text-sm">
              <button
                onClick={() => setUploadMode("file")}
                className={`px-4 py-2 ${
                  uploadMode === "file"
                    ? "bg-slate-950 text-white"
                    : "bg-white text-slate-700"
                }`}
              >
                File
              </button>

              <button
                onClick={() => setUploadMode("text")}
                className={`px-4 py-2 ${
                  uploadMode === "text"
                    ? "bg-slate-950 text-white"
                    : "bg-white text-slate-700"
                }`}
              >
                Text
              </button>
            </div>
          </div>

          <label className="block mt-4 text-sm font-medium">Document name</label>
          <input
            className="mt-1 w-full rounded-xl border p-3 text-sm"
            value={documentName}
            onChange={(e) => setDocumentName(e.target.value)}
            placeholder="deployment_runbook"
          />

          {uploadMode === "file" && (
            <>
              <label className="block mt-4 text-sm font-medium">
                Upload PDF, DOCX, TXT, or MD
              </label>

              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                className="mt-1 w-full rounded-xl border p-3 text-sm"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
              />

              {selectedFile && (
                <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm">
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-slate-500">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              )}

              <button
                onClick={uploadFileDocument}
                disabled={!selectedFile || loading}
                className="mt-4 rounded-xl bg-slate-950 text-white px-5 py-2 disabled:opacity-50"
              >
                {loading ? "Processing..." : "Upload File to Vector DB"}
              </button>
            </>
          )}

          {uploadMode === "text" && (
            <>
              <label className="block mt-4 text-sm font-medium">Text</label>
              <textarea
                className="mt-1 w-full h-64 rounded-xl border p-3 text-sm"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste a deployment runbook, model policy, incident response guide, or architecture note..."
              />

              <button
                onClick={uploadTextDocument}
                disabled={!documentName.trim() || !text.trim() || loading}
                className="mt-4 rounded-xl bg-slate-950 text-white px-5 py-2 disabled:opacity-50"
              >
                {loading ? "Processing..." : "Upload Text to Vector DB"}
              </button>
            </>
          )}

          {status && (
            <p className="mt-4 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
              {status}
            </p>
          )}
        </div>

        <div className="rounded-2xl bg-white border shadow-sm p-5">
          <h3 className="text-lg font-semibold">Ask Uploaded Documents</h3>

          <label className="block mt-4 text-sm font-medium">
            Restrict search to one document
          </label>

          <select
            className="mt-1 w-full rounded-xl border p-3 text-sm"
            value={selectedDocument}
            onChange={(e) => setSelectedDocument(e.target.value)}
          >
            <option value="">All uploaded documents</option>
            {documents.map((doc) => (
              <option key={doc.document_name} value={doc.document_name}>
                {doc.document_name}
              </option>
            ))}
          </select>

          <label className="block mt-4 text-sm font-medium">Question</label>
          <input
            className="mt-1 w-full rounded-xl border p-3 text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask: What is the rollback procedure?"
          />

          <button
            onClick={queryKnowledge}
            disabled={!query.trim() || loading}
            className="mt-4 rounded-xl bg-slate-950 text-white px-5 py-2 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search Document"}
          </button>

          <div className="mt-5 space-y-3">
            {matches.map((match, idx) => (
              <div key={idx} className="rounded-xl bg-slate-50 p-4 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold">{match.document_name}</p>
                    <p className="text-xs text-slate-500">
                      {match.filename} | chunk {match.chunk_index}
                    </p>
                  </div>

                  <p className="text-xs text-slate-500">score: {match.score}</p>
                </div>

                <p className="mt-3 text-slate-700 whitespace-pre-wrap">
                  {match.chunk_text}
                </p>
              </div>
            ))}

            {matches.length === 0 && (
              <p className="text-sm text-slate-500">
                No matches yet. Upload a document and ask a question.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-2xl bg-white border shadow-sm p-5 mt-8">
        <h3 className="text-lg font-semibold">Uploaded Documents</h3>

        <table className="w-full text-sm mt-4">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-3">Document</th>
              <th className="p-3">Filename</th>
              <th className="p-3">Source</th>
              <th className="p-3">Chunks</th>
              <th className="p-3">Action</th>
            </tr>
          </thead>

          <tbody>
            {documents.map((doc) => (
              <tr key={doc.document_name} className="border-t">
                <td className="p-3 font-medium">{doc.document_name}</td>
                <td className="p-3">{doc.filename ?? "-"}</td>
                <td className="p-3">{doc.source_type ?? "-"}</td>
                <td className="p-3">{doc.chunks}</td>
                <td className="p-3">
                  <button
                    onClick={() => deleteDocument(doc.document_name)}
                    disabled={loading}
                    className="rounded-lg border px-3 py-1 text-xs hover:bg-slate-50 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}

            {documents.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-slate-500">
                  No documents uploaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}