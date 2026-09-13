import { useState, type ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { uploadApplication } from "../api/application";
import { useApplication } from "../context/ApplicationContext";
import { useAuth } from "../context/AuthContext";

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { setResult } = useApplication();
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    setError(null);
  }

  async function handleSubmit() {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    try {
      const result = await uploadApplication(file);
      setResult(result);
      navigate(`/results/${result.application_id}`);
    } catch {
      setError("Failed to process the application. Please check the file and try again.");
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center">
        <h1 className="text-lg font-semibold text-slate-800">Loan Origination System</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">{role}</span>
          <button onClick={logout} className="text-sm text-indigo-600 hover:underline">
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-xl mx-auto mt-16 px-4">
        <div className="bg-white rounded-xl shadow-md p-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-1">Upload Application</h2>
          <p className="text-slate-500 mb-6">
            Upload a ZIP file containing the applicant's documents (Aadhaar, PAN, salary slip, bank
            statement, ITR, loan application form, existing loan history).
          </p>

          <label className="block border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-indigo-400 transition">
            <input type="file" accept=".zip" onChange={handleFileChange} className="hidden" />
            <p className="text-slate-600">
              {file ? file.name : "Click to select a ZIP file"}
            </p>
          </label>

          {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={!file || isProcessing}
            className="w-full mt-6 bg-indigo-600 text-white rounded-lg py-2.5 font-medium hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            {isProcessing ? "Processing application..." : "Submit Application"}
          </button>

          {isProcessing && (
            <p className="text-sm text-slate-500 text-center mt-3">
              This can take up to a minute — extracting documents, verifying details, checking credit
              bureau, and scoring risk.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}