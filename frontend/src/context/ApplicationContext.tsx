import { createContext, useContext, useState, type ReactNode } from "react";
import type { ApplicationResponse } from "../types/application";

interface ApplicationContextValue {
  result: ApplicationResponse | null;
  setResult: (result: ApplicationResponse) => void;
}

const ApplicationContext = createContext<ApplicationContextValue | undefined>(undefined);

export function ApplicationProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<ApplicationResponse | null>(null);

  return (
    <ApplicationContext.Provider value={{ result, setResult }}>
      {children}
    </ApplicationContext.Provider>
  );
}

export function useApplication() {
  const context = useContext(ApplicationContext);
  if (!context) {
    throw new Error("useApplication must be used within an ApplicationProvider");
  }
  return context;
}