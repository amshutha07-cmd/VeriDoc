/* Evidence Atelier direction: editorial legal-research workbench, ivory paper, ink-black type, oxidized-copper provenance markers, asymmetric persistent rail. */
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import CorpusRegistry from "./pages/CorpusRegistry";
import KnowledgeGraph from "./pages/KnowledgeGraph";
import IngestionJobs from "./pages/IngestionJobs";
import Evaluation from "./pages/Evaluation";
import NotFound from "./pages/NotFound";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/corpus" component={CorpusRegistry} />
      <Route path="/graph" component={KnowledgeGraph} />
      <Route path="/ingestion" component={IngestionJobs} />
      <Route path="/evaluation" component={Evaluation} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster position="bottom-right" richColors toastOptions={{ classNames: { toast: "!bg-[#1e2625] !text-[#f8f5ef] !border-[#b96845]", description: "!text-[#d9d1c4]" } }} />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
