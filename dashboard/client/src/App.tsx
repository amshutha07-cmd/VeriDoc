/* VeriDoc Nexus: one shell (header, upload and guide dialogs) around five pages. */
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import AppShell from "./components/AppShell";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { UploadProvider } from "./contexts/UploadContext";
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
      <ThemeProvider defaultTheme="dark">
        <TooltipProvider>
          <Toaster
            position="bottom-right"
            toastOptions={{
              classNames: {
                toast: "!rounded-none !border !border-edge !bg-panel !text-fg",
                description: "!text-mute",
                success: "!border-lime",
                error: "!border-coral",
              },
            }}
          />
          <UploadProvider>
            <AppShell>
              <Router />
            </AppShell>
          </UploadProvider>
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
