
import { TokenGrid } from './TokenGrid';
import { StrategyPanel } from './StrategyPanel';

export const Dashboard = () => {
    return (
        <div className="h-screen w-full flex flex-col bg-background text-foreground overflow-hidden">
            {/* Header */}
            <header className="h-14 border-b border-border flex items-center px-4 justify-between bg-card/50 backdrop-blur">
                <div className="font-bold text-lg tracking-tight text-primary">
                    Antigravity <span className="text-accent-foreground">Trader</span>
                </div>
                <div className="text-sm text-muted-foreground">
                    Market Status: <span className="text-green-500">Open</span>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 flex overflow-hidden">
                {/* Left Panel: Token Grid */}
                <div className="flex-1 border-r border-border flex flex-col">
                    <TokenGrid />
                </div>

                {/* Right Panel: Controls */}
                <div className="w-[400px] flex flex-col bg-card/20 backdrop-blur">
                    <div className="flex-1 p-4 border-b border-border overflow-auto">
                        <h2 className="font-semibold mb-4">Strategy Configuration</h2>
                        <StrategyPanel />
                    </div>
                    <div className="h-1/3 p-4 overflow-auto">
                        <h2 className="font-semibold mb-4">Active Orders</h2>
                        <div className="text-sm text-muted-foreground">No active orders</div>
                    </div>
                </div>
            </main>

            {/* Bottom Status Bar */}
            <footer className="h-8 border-t border-border flex items-center px-4 text-xs text-muted-foreground bg-card">
                System Ready
            </footer>
        </div>
    );
};
