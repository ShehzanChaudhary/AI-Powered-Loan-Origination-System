import type { CibilReport } from "../../types/application";

export function CreditReportSummary({ report }: { report: CibilReport }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-slate-800">Credit Bureau Report</h3>
        <span className="text-2xl font-bold text-indigo-600">{report.credit_score.score}</span>
      </div>

      <p className="text-xs text-slate-500 mb-4">{report.credit_score.score_factors.join(" · ")}</p>

      <h4 className="text-sm font-medium text-slate-700 mb-2">Credit Accounts</h4>
      <div className="space-y-2 mb-4">
        {report.credit_accounts.map((account) => (
          <div key={account.account_number} className="flex justify-between items-center text-sm border-b border-slate-100 pb-2 last:border-0">
            <div>
              <p className="text-slate-800">{account.lender} — {account.account_type}</p>
              <p className="text-xs text-slate-500">EMI ₹{account.emi?.toLocaleString()} · Balance ₹{account.current_balance?.toLocaleString()}</p>
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded ${account.account_status === "ACTIVE" ? "text-green-700 bg-green-100" : "text-slate-500 bg-slate-100"}`}>
              {account.account_status}
            </span>
          </div>
        ))}
      </div>

      {report.enquiries.length > 0 && (
        <p className="text-xs text-slate-500">
          {report.enquiries.length} recent enquiry(s) — last from {report.enquiries[report.enquiries.length - 1].lender}
        </p>
      )}
    </div>
  );
}