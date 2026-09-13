import type { VerificationReport } from "../../types/application";

const STATUS_STYLES: Record<string, string> = {
  MATCHED: "text-green-700 bg-green-100",
  MISMATCH: "text-red-700 bg-red-100",
  MISSING: "text-slate-500 bg-slate-100",
};

export function VerificationChecks({ verification }: { verification: VerificationReport }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-slate-800">Cross-Document Verification</h3>
        <span className={`text-sm font-semibold px-3 py-1 rounded-full ${verification.overall_status === "CLEAN" ? "text-green-700 bg-green-100" : "text-red-700 bg-red-100"}`}>
          {verification.overall_status}
        </span>
      </div>

      <div className="space-y-2">
        {verification.checks.map((check) => (
          <div key={check.field_name} className="flex justify-between items-center text-sm border-b border-slate-100 pb-2 last:border-0">
            <span className="text-slate-700">{check.field_name}</span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded ${STATUS_STYLES[check.status]}`}>
              {check.status}
              {check.similarity_score !== null && ` (${check.similarity_score.toFixed(0)}%)`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}