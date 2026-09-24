import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  cancelRun,
  createResearch,
  getEvaluation,
  getEvents,
  getHealth,
  getIterations,
  getPapers,
  getResearchRun,
  getResult,
  getThemes,
  listResearchRuns,
  subscribeEvents,
} from './services/api';
import {
  AgentEvent,
  EvaluationData,
  Paper,
  ResearchConfigInput,
  ResearchIteration,
  ResearchResultData,
  ResearchRun,
  Theme,
} from './types';

import { Navbar } from './components/Navbar';
import { ResearchForm } from './components/ResearchForm';
import { DashboardHeader } from './components/DashboardHeader';
import { LiveProgress } from './components/LiveProgress';
import { AgentTimeline } from './components/AgentTimeline';
import { PaperExplorer } from './components/PaperExplorer';
import { ThemeSynthesis } from './components/ThemeSynthesis';
import { ReflectionView } from './components/ReflectionView';
import { FinalReview } from './components/FinalReview';
import { EvaluationView } from './components/EvaluationView';
import { HistoryDrawer } from './components/HistoryDrawer';

import {
  Activity,
  Award,
  BookOpen,
  FileCheck2,
  Layers,
  Search,
  Sliders,
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<ResearchRun | null>(null);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [iterations, setIterations] = useState<ResearchIteration[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [result, setResult] = useState<ResearchResultData | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationData | null>(null);

  const [activeTab, setActiveTab] = useState<
    'progress' | 'papers' | 'themes' | 'reflection' | 'review' | 'evaluation'
  >('progress');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [isMockMode, setIsMockMode] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pollTimerRef = useRef<any>(null);

  // Initial load
  useEffect(() => {
    getHealth()
      .then((h) => setIsMockMode(h.is_mock_mode))
      .catch(() => {});

    loadRunsList();

    // Check query param for run_id
    const params = new URLSearchParams(window.location.search);
    const runParam = params.get('run');
    if (runParam) {
      loadRunDetails(runParam);
    }
  }, []);

  const loadRunsList = async () => {
    try {
      const pastRuns = await listResearchRuns();
      setRuns(pastRuns);
      return pastRuns;
    } catch (e) {
      console.error(e);
      return [];
    }
  };

  const loadRunDetails = useCallback(async (runId: string) => {
    try {
      setActiveRunId(runId);
      const run = await getResearchRun(runId);
      setActiveRun(run);

      // Fetch all associated entities
      const [itData, pData, tData, eData] = await Promise.all([
        getIterations(runId).catch(() => []),
        getPapers(runId).catch(() => []),
        getThemes(runId).catch(() => []),
        getEvents(runId).catch(() => []),
      ]);
      setIterations(itData);
      setPapers(pData);
      setThemes(tData);
      setEvents(eData);

      if (run.status === 'completed') {
        const [resData, evalData] = await Promise.all([
          getResult(runId).catch(() => null),
          getEvaluation(runId).catch(() => null),
        ]);
        if (resData) setResult(resData);
        if (evalData) setEvaluation(evalData);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Error loading run');
    }
  }, []);

  // Polling & SSE stream for active running run
  useEffect(() => {
    if (!activeRunId || !activeRun || activeRun.status !== 'running') {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      return;
    }

    // Subscribe to SSE
    const unsubscribe = subscribeEvents(
      activeRunId,
      (evt) => {
        if (evt.event_type && evt.message) {
          setEvents((prev) => {
            if (prev.some((e) => e.id === evt.id)) return prev;
            return [...prev, evt as AgentEvent];
          });
        }
        if (evt.event_type === 'research.completed' || evt.status === 'completed') {
          loadRunDetails(activeRunId);
          loadRunsList();
        }
      },
      (err) => {
        // Fallback silently to polling
      }
    );

    // Reliable background polling
    pollTimerRef.current = setInterval(async () => {
      try {
        const updated = await getResearchRun(activeRunId);
        setActiveRun(updated);

        const [pData, tData, eData, itData] = await Promise.all([
          getPapers(activeRunId),
          getThemes(activeRunId),
          getEvents(activeRunId),
          getIterations(activeRunId),
        ]);
        setPapers(pData);
        setThemes(tData);
        setEvents(eData);
        setIterations(itData);

        if (updated.status === 'completed' || updated.status === 'failed') {
          if (pollTimerRef.current) clearInterval(pollTimerRef.current);
          if (updated.status === 'completed') {
            const [resData, evalData] = await Promise.all([
              getResult(activeRunId),
              getEvaluation(activeRunId),
            ]);
            setResult(resData);
            setEvaluation(evalData);
            // Default to final review if complete
            setActiveTab('review');
          }
          loadRunsList();
        }
      } catch (e) {
        console.error('Polling error', e);
      }
    }, 1500);

    return () => {
      unsubscribe();
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [activeRunId, activeRun?.status, loadRunDetails]);

  const handleStartResearch = async (question: string, config: ResearchConfigInput) => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const created = await createResearch(question, config);
      setActiveRun(created);
      setActiveRunId(created.id);
      setEvents([]);
      setPapers([]);
      setThemes([]);
      setIterations([]);
      setResult(null);
      setEvaluation(null);
      setActiveTab('progress');

      // Update URL
      const url = new URL(window.location.href);
      url.searchParams.set('run', created.id);
      window.history.pushState({}, '', url.toString());

      await loadRunsList();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to initialize research session');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancelRun = async () => {
    if (!activeRunId) return;
    try {
      await cancelRun(activeRunId);
      await loadRunDetails(activeRunId);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewResearch = () => {
    setActiveRunId(null);
    setActiveRun(null);
    setResult(null);
    const url = new URL(window.location.href);
    url.searchParams.delete('run');
    window.history.pushState({}, '', url.toString());
  };

  const handleSelectPastRun = (runId: string) => {
    loadRunDetails(runId);
    const url = new URL(window.location.href);
    url.searchParams.set('run', runId);
    window.history.pushState({}, '', url.toString());
  };

  return (
    <div className="app-container">
      <Navbar
        onNewResearch={handleNewResearch}
        onOpenHistory={() => setIsHistoryOpen(true)}
        isMockMode={isMockMode}
      />

      <main className="main-content">
        {errorMsg && (
          <div
            style={{
              padding: '1rem',
              backgroundColor: 'var(--danger-bg)',
              border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--danger)',
              marginBottom: '1.5rem',
            }}
          >
            {errorMsg}
          </div>
        )}

        {!activeRun ? (
          <ResearchForm onSubmit={handleStartResearch} isLoading={isSubmitting} />
        ) : (
          <div>
            <DashboardHeader run={activeRun} onCancel={handleCancelRun} />

            <nav className="tabs-nav">
              <button
                className={`tab-btn ${activeTab === 'progress' ? 'active' : ''}`}
                onClick={() => setActiveTab('progress')}
              >
                <Activity size={16} />
                <span>Agent Progress & Trace</span>
                <span className="tab-count">{events.length}</span>
              </button>

              <button
                className={`tab-btn ${activeTab === 'papers' ? 'active' : ''}`}
                onClick={() => setActiveTab('papers')}
              >
                <Search size={16} />
                <span>Literature & Papers</span>
                <span className="tab-count">{papers.length}</span>
              </button>

              <button
                className={`tab-btn ${activeTab === 'themes' ? 'active' : ''}`}
                onClick={() => setActiveTab('themes')}
              >
                <Layers size={16} />
                <span>Thematic Synthesis</span>
                <span className="tab-count">{themes.length}</span>
              </button>

              <button
                className={`tab-btn ${activeTab === 'reflection' ? 'active' : ''}`}
                onClick={() => setActiveTab('reflection')}
              >
                <Sliders size={16} />
                <span>Critic & Gaps</span>
              </button>

              <button
                className={`tab-btn ${activeTab === 'review' ? 'active' : ''}`}
                onClick={() => setActiveTab('review')}
              >
                <BookOpen size={16} />
                <span>Final Literature Review</span>
              </button>

              <button
                className={`tab-btn ${activeTab === 'evaluation' ? 'active' : ''}`}
                onClick={() => setActiveTab('evaluation')}
              >
                <Award size={16} />
                <span>Evaluation Metrics</span>
              </button>
            </nav>

            <div style={{ marginTop: '1.5rem' }}>
              {activeTab === 'progress' && (
                <div>
                  <LiveProgress events={events} isRunning={activeRun.status === 'running'} />
                  <AgentTimeline events={events} />
                </div>
              )}

              {activeTab === 'papers' && <PaperExplorer papers={papers} />}

              {activeTab === 'themes' && (
                <ThemeSynthesis themes={themes} synthesis={result?.synthesis} />
              )}

              {activeTab === 'reflection' && (
                <ReflectionView reflection={result?.reflection || (iterations[iterations.length - 1]?.reflection as any)} />
              )}

              {activeTab === 'review' && (
                <FinalReview result={result || undefined} papers={papers} />
              )}

              {activeTab === 'evaluation' && <EvaluationView evaluation={evaluation || undefined} />}
            </div>
          </div>
        )}
      </main>

      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        runs={runs}
        activeRunId={activeRunId || undefined}
        onSelectRun={handleSelectPastRun}
      />
    </div>
  );
};

export default App;
