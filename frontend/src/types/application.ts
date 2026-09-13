export interface DocumentInfo {
  file_name: string;
  document_type: string;
  status: string;
  fields: Record<string, unknown> | null;
}

export interface VerificationCheck {
  field_name: string;
  status: "MATCHED" | "MISMATCH" | "MISSING";
  values_found: Record<string, string | null>;
  similarity_score: number | null;
  note: string | null;
}

export interface VerificationReport {
  checks: VerificationCheck[];
  overall_status: "CLEAN" | "FLAGGED";
}

export interface CreditAccount {
  lender: string;
  account_number: string;
  account_type: string;
  ownership: string;
  sanctioned_amount: number | null;
  credit_limit: number | null;
  current_balance: number | null;
  overdue_amount: number | null;
  emi: number | null;
  interest_rate: number | null;
  open_date: string | null;
  close_date: string | null;
  last_payment_date: string | null;
  account_status: "ACTIVE" | "CLOSED" | "WRITTEN_OFF" | "SETTLED";
  written_off_amount: number | null;
  settlement_amount: number | null;
  payment_history: string[];
}

export interface CreditEnquiry {
  date: string;
  lender: string;
  purpose: string;
  amount: number | null;
}

export interface CibilReport {
  personal_information: {
    name: string | null;
    dob: string | null;
    gender: string | null;
    pan: string | null;
    phone: string | null;
    email: string | null;
    addresses: string[];
  };
  credit_score: {
    score: number;
    score_factors: string[];
  };
  credit_accounts: CreditAccount[];
  enquiries: CreditEnquiry[];
  employment_information: {
    occupation: string | null;
    income: number | null;
    income_frequency: string | null;
  };
  disputes: {
    dispute_id: string;
    date: string;
    information: string;
    status: string;
  }[];
}

export interface RiskFactor {
  name: string;
  points: number;
  detail: string;
}

export interface RiskAssessment {
  total_score: number;
  risk_band: "LOW" | "MEDIUM" | "HIGH";
  factors: RiskFactor[];
}

export interface FinalDecision {
  decision: "APPROVED" | "REJECTED" | "MANUAL_REVIEW";
  reasons: string[];
  justification: string | null;
}

export interface ApplicationResponse {
  application_id: string;
  status: string;
  file_name: string;
  documents: DocumentInfo[];
  verification: VerificationReport | null;
  credit_report: CibilReport | null;
  risk_assessment: RiskAssessment | null;
  final_decision: FinalDecision | null;
}