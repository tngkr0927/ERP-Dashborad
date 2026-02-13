import { useState, useEffect } from "react";
import DashboardLayout from "./layouts/DashboardLayout";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import AnalyzePage from "./pages/AnalyzePage";

type Page = "dashboard" | "upload" | "analyze";

function getPageFromHash(): Page {
  const hash = window.location.hash.replace("#", "");
  if (hash === "upload") return "upload";
  if (hash === "analyze") return "analyze";
  return "dashboard";
}

export default function App() {
  const [page, setPage] = useState<Page>(getPageFromHash);

  useEffect(() => {
    const onHashChange = () => setPage(getPageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <DashboardLayout>
      {page === "dashboard" && <DashboardPage />}
      {page === "upload" && <UploadPage />}
      {page === "analyze" && <AnalyzePage />}
    </DashboardLayout>
  );
}
