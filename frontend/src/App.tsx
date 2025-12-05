import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { useState, useEffect } from 'react';
import { TokenGrid } from './components/TokenGrid';
import { StrategyPanel } from './components/StrategyPanel';
// Removed CandlesPanel from default UI to streamline feature set
// import { CandlesPanel } from './components/CandlesPanel';
import { GlobalSettings } from './components/GlobalSettings';
import { WelcomeSetup } from './components/WelcomeSetup';
import { useNotificationService } from './hooks/useNotificationService';
import { ThemeToggle } from './components/ThemeToggle';
import { AutoBuySelector } from './components/AutoBuySelector';

function App() {
  const [setupComplete, setSetupComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [tokens, setTokens] = useState([]);
  // Simplify: remove per-symbol candles panel for now
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [tradingMode, setTradingMode] = useState('NOTIFY_ONLY');

  // Fetch token data
  useEffect(() => {
    if (!setupComplete) return;

    const fetchData = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/tokens');
        const data = await res.json();
        setTokens(data);
        // Auto-select first symbol if none selected
        if (!selectedSymbol && Array.isArray(data) && data.length > 0) {
          setSelectedSymbol(data[0]?.symbol ?? '');
        }
      } catch (err) {
        console.error("Failed to fetch token data", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, [setupComplete]);

  // Enable desktop notifications
  useNotificationService({ tokens, tradingMode });

  useEffect(() => {
    // Check if setup was completed before
    const completed = localStorage.getItem('setup_complete');
    setSetupComplete(completed === 'true');
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!setupComplete) {
    return <WelcomeSetup onComplete={() => setSetupComplete(true)} />;
  }

  return (
    <div className="h-screen w-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-gray-900 via-gray-950 to-black flex flex-col overflow-hidden text-gray-100">
      {/* Header */}
      <header className="glass-panel z-10 px-6 py-4 flex items-center justify-between flex-shrink-0 border-b-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
            <span className="text-lg font-bold">A</span>
          </div>
          <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            Antigravity Trader
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">Market Open</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        {/* Grid Area */}
        <main className="flex-1 overflow-hidden rounded-2xl glass-panel border-0 flex flex-col">
          <TokenGrid tokens={tokens} />
          {/* Candles view removed to reduce UI complexity as requested */}
        </main>

        {/* Right Sidebar */}
        <aside className="w-80 flex flex-col gap-4 overflow-y-auto pr-1">
          <GlobalSettings onModeChange={setTradingMode} />
          <AutoBuySelector />
          <StrategyPanel />
        </aside>
      </div>
      
    </div>
  );
}

export default App;
