import { useState, useEffect } from 'react';
import { Settings, Bell, ShoppingCart, CheckCircle } from 'lucide-react';

type TradingMode = 'NOTIFY_ONLY' | 'AUTO_BUY' | 'BOTH';

interface LotSizes {
    nifty: number;
    banknifty: number;
    sensex: number;
    midcpnifty: number;
    finnifty: number;
    stock: number;
}

interface GlobalSettingsData {
    mode: TradingMode;
    lotSizes: LotSizes;
    requireConfirmation: boolean;
}

export const GlobalSettings = () => {
    const [settings, setSettings] = useState<GlobalSettingsData>({
        mode: 'NOTIFY_ONLY',
        lotSizes: {
            nifty: 75,
            banknifty: 35,
            sensex: 20,
            midcpnifty: 140,
            finnifty: 65,
            stock: 50,
        },
        requireConfirmation: true,
    });

    const [isSaving, setIsSaving] = useState(false);
    const [showLotSizes, setShowLotSizes] = useState(false);

    const saveSettings = async () => {
        setIsSaving(true);
        try {
            await fetch('http://127.0.0.1:8000/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            });
        } catch (err) {
            console.error("Failed to save settings", err);
        } finally {
            setIsSaving(false);
        }
    };

    const handleLogout = async () => {
        if (confirm('Are you sure you want to logout? You will need to re-enter your mStock credentials.')) {
            try {
                await fetch('http://127.0.0.1:8000/api/credentials', {
                    method: 'DELETE',
                });
                localStorage.removeItem('setupComplete');
                window.location.reload();
            } catch (err) {
                console.error("Failed to logout", err);
                alert('Logout failed. Please try again.');
            }
        }
    };

    useEffect(() => {
        saveSettings();
    }, [settings]);

    return (
        <div className="glass-panel rounded-xl p-5 mb-4">
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                    <Settings size={18} />
                </div>
                <h3 className="text-white font-semibold tracking-wide">Global Settings</h3>
            </div>

            <div className="space-y-6">
                {/* Trading Mode Selection */}
                <div>
                    <label className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-3 block">Trading Mode</label>
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            onClick={() => setSettings({ ...settings, mode: 'NOTIFY_ONLY' })}
                            className={`p-3 rounded-xl flex flex-col items-center gap-2 transition-all duration-200 border ${settings.mode === 'NOTIFY_ONLY'
                                ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-500/20'
                                : 'bg-gray-800/50 text-gray-400 border-white/5 hover:bg-gray-800 hover:text-gray-200'
                                }`}
                        >
                            <Bell size={18} />
                            <span className="text-[10px] font-semibold">Notify</span>
                        </button>

                        <button
                            onClick={() => setSettings({ ...settings, mode: 'AUTO_BUY' })}
                            className={`p-3 rounded-xl flex flex-col items-center gap-2 transition-all duration-200 border ${settings.mode === 'AUTO_BUY'
                                ? 'bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-500/20'
                                : 'bg-gray-800/50 text-gray-400 border-white/5 hover:bg-gray-800 hover:text-gray-200'
                                }`}
                        >
                            <ShoppingCart size={18} />
                            <span className="text-[10px] font-semibold">Auto Buy</span>
                        </button>

                        <button
                            onClick={() => setSettings({ ...settings, mode: 'BOTH' })}
                            className={`p-3 rounded-xl flex flex-col items-center gap-2 transition-all duration-200 border ${settings.mode === 'BOTH'
                                ? 'bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-500/20'
                                : 'bg-gray-800/50 text-gray-400 border-white/5 hover:bg-gray-800 hover:text-gray-200'
                                }`}
                        >
                            <CheckCircle size={18} />
                            <span className="text-[10px] font-semibold">Both</span>
                        </button>
                    </div>
                </div>

                {/* Lot Size Configuration */}
                <div className="bg-gray-800/30 rounded-xl border border-white/5 overflow-hidden">
                    <button
                        onClick={() => setShowLotSizes(!showLotSizes)}
                        className="w-full flex items-center justify-between p-3 text-gray-300 hover:bg-white/5 transition-colors"
                    >
                        <span className="text-sm font-medium">Lot Size Config</span>
                        <span className="text-xs text-gray-500 transform transition-transform duration-200" style={{ transform: showLotSizes ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                            ▼
                        </span>
                    </button>

                    {showLotSizes && (
                        <div className="p-3 pt-0 space-y-2 border-t border-white/5 mt-1">
                            {Object.entries(settings.lotSizes).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between py-1">
                                    <label className="text-gray-400 text-xs uppercase font-medium tracking-wide">{key}</label>
                                    <input
                                        type="number"
                                        min="1"
                                        step="1"
                                        value={value}
                                        onChange={(e) => {
                                            const val = parseInt(e.target.value) || 1;
                                            setSettings({
                                                ...settings,
                                                lotSizes: { ...settings.lotSizes, [key]: val }
                                            });
                                        }}
                                        onKeyDown={(e) => {
                                            if (!/^[0-9]$/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(e.key)) {
                                                e.preventDefault();
                                            }
                                        }}
                                        className="w-16 bg-gray-900 text-white px-2 py-1 rounded-md text-xs text-center border border-white/10 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Safety Toggle */}
                {settings.mode !== 'NOTIFY_ONLY' && (
                    <div className="flex items-center justify-between bg-gray-800/30 p-3 rounded-xl border border-white/5">
                        <label className="text-gray-300 text-sm font-medium">Confirmation</label>
                        <button
                            onClick={() => setSettings({ ...settings, requireConfirmation: !settings.requireConfirmation })}
                            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors duration-200 focus:outline-none ${settings.requireConfirmation ? 'bg-blue-600' : 'bg-gray-600'
                                }`}
                        >
                            <span
                                className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200 ${settings.requireConfirmation ? 'translate-x-5' : 'translate-x-1'
                                    }`}
                            />
                        </button>
                    </div>
                )}

                {/* Status Indicator */}
                <div className="flex items-center justify-end gap-2">
                    {isSaving ? (
                        <span className="text-[10px] text-yellow-500 flex items-center gap-1.5 bg-yellow-500/10 px-2 py-1 rounded-full">
                            <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" />
                            Saving...
                        </span>
                    ) : (
                        <span className="text-[10px] text-emerald-500 flex items-center gap-1.5 bg-emerald-500/10 px-2 py-1 rounded-full">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Saved
                        </span>
                    )}
                </div>

                {/* Logout Button */}
                <div className="pt-4 border-t border-white/5">
                    <button
                        onClick={handleLogout}
                        className="w-full px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 border border-red-500/20 hover:border-red-500/30 rounded-xl font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                            <polyline points="16 17 21 12 16 7" />
                            <line x1="21" y1="12" x2="9" y2="12" />
                        </svg>
                        Logout & Re-enter Credentials
                    </button>
                </div>
            </div>
        </div>
    );
};
