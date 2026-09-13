import { useNavigate } from "react-router-dom";
import { useApplication } from "../context/ApplicationContext";
import { useAuth } from "../context/AuthContext";
import { DecisionBanner } from "../components/results/DecisionBanner";
import { RiskScorecard } from "../components/results/RiskScorecard";
import { VerificationChecks } from "../components/results/VerificationChecks";
import { DocumentsList } from "../components/results/DocumentsList";
import { CreditReportSummary } from "../components/results/CreditReportSummary";

export function ResultsPage() {
  const { result } = useApplication();
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center gap-4">
        <p className="text-slate-500">No application data available.</p>
        <button
          onClick={() => navigate("/upload")}
          className="text-indigo-600 hover:underline"
        >
          Go back to Upload
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-lg font-semibold text-slate-800">Application {result.application_id}</h1>
          <p className="text-sm text-slate-500">{result.file_name}</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/upload")}
            className="text-sm text-indigo-600 hover:underline"
          >
            New Application
          </button>
          <span className="text-sm text-slate-500">{role}</span>
          <button onClick={logout} className="text-sm text-indigo-600 hover:underline">
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {result.final_decision && <DecisionBanner decision={result.final_decision} />}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {result.risk_assessment && <RiskScorecard risk={result.risk_assessment} />}
          {result.verification && <VerificationChecks verification={result.verification} />}
        </div>

        <DocumentsList documents={result.documents} />

        {result.credit_report && <CreditReportSummary report={result.credit_report} />}
      </main>
    </div>
  );
}