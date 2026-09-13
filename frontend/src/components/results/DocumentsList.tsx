import { useState } from "react";
import type { DocumentInfo } from "../../types/application";

function DocumentCard({ document }: { document: DocumentInfo }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-slate-200 rounded-lg">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex justify-between items-center px-4 py-3 text-left"
      >
        <div>
          <p className="font-medium text-slate-800">{document.document_type}</p>
          <p className="text-xs text-slate-500">{document.file_name}</p>
        </div>
        <span className="text-slate-400 text-sm">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-3">
          {document.fields ? (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              {Object.entries(document.fields).map(([key, value]) => (
                <div key={key}>
                  <dt className="text-slate-500 text-xs">{key.replace(/_/g, " ")}</dt>
                  <dd className="text-slate-800">{value === null || value === "" ? "—" : String(value)}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-slate-400">No fields extracted for this document.</p>
          )}
        </div>
      )}
    </div>
  );
}

export function DocumentsList({ documents }: { documents: DocumentInfo[] }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h3 className="font-semibold text-slate-800 mb-4">Documents ({documents.length})</h3>
      <div className="space-y-2">
        {documents.map((doc) => (
          <DocumentCard key={doc.file_name} document={doc} />
        ))}
      </div>
    </div>
  );
}