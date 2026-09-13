import type { FinalDecision } from "../../types/application";

const DECISION_STYLES: Record<string, string> = {
  APPROVED: "bg-green-50 border-green-300 text-green-800",
  REJECTED: "bg-red-50 border-red-300 text-red-800",
  MANUAL_REVIEW: "bg-amber-50 border-amber-300 text-amber-800",
};

export function DecisionBanner({ decision }: { decision: FinalDecision }) {
  return (
    <div className={`rounded-xl border-2 p-6 ${DECISION_STYLES[decision.decision]}`}>
      <h2 className="text-2xl font-bold mb-2">{decision.decision.replace("_", " ")}</h2>

      <ul className="text-sm space-y-1 mb-3">
        {decision.reasons.map((reason, i) => (
          <li key={i}>• {reason}</li>
        ))}
      </ul>

      {decision.justification && (
        <p className="text-sm leading-relaxed border-t border-current/20 pt-3 mt-3">
          {decision.justification}
        </p>
      )}
    </div>
  );
}