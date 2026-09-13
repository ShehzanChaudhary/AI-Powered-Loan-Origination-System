import type { RiskAssessment } from "../../types/application";

const RISK_BAND_COLOR: Record<string, string> = {
  LOW: "text-green-700 bg-green-100",
  MEDIUM: "text-amber-700 bg-amber-100",
  HIGH: "text-red-700 bg-red-100",
};

export function RiskScorecard({ risk }: { risk: RiskAssessment }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-slate-800">Risk Scorecard</h3>
        <span className={`text-sm font-semibold px-3 py-1 rounded-full ${RISK_BAND_COLOR[risk.risk_band]}`}>
          {risk.risk_band} · {risk.total_score} pts
        </span>
      </div>

      <div className="space-y-2">
        {risk.factors.map((factor) => (
          <div key={factor.name} className="flex justify-between items-start text-sm border-b border-slate-100 pb-2 last:border-0">
            <div>
              <p className="font-medium text-slate-700">{factor.name}</p>
              <p className="text-slate-500 text-xs mt-0.5">{factor.detail}</p>
            </div>
            <span className={`font-semibold shrink-0 ml-3 ${factor.points >= 0 ? "text-green-600" : "text-red-600"}`}>
              {factor.points >= 0 ? "+" : ""}{factor.points}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}