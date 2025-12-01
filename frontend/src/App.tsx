import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import { useState, useEffect } from 'react';
import { TokenGrid } from './components/TokenGrid';
import { StrategyPanel } from './components/StrategyPanel';
import { GlobalSettings } from './components/GlobalSettings';
import { WelcomeSetup } from './components/WelcomeSetup';

function App() {
  const [setupComplete, setSetupComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

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
    <div className="h-screen w-screen bg-gray-950 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-700 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <h1 className="text-2xl font-bold text-white">Antigravity Trader</h1>
        <div className="text-sm text-green-400 font-medium">
          Market Status: <span className="font-bold">Open</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Grid Area */}
        <main className="flex-1 overflow-hidden">
          <TokenGrid />
        </main>

        {/* Right Sidebar */}
        <aside className="w-80 bg-gray-900 border-l border-gray-700 flex flex-col overflow-y-auto p-4">
          <GlobalSettings />
          <StrategyPanel />
        </aside>
      </div>
    </div>
  );
}

export default App;
