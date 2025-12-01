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

    useEffect(() => {
        saveSettings();
    }, [settings]);

    return (
        <div className="bg-gray-800 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2 mb-4">
                <Settings className="text-blue-400" size={20} />
                <h3 className="text-white font-bold">Global Trading Settings</h3>
            </div>

            <div className="space-y-4">
                {/* Trading Mode Selection */}
                <div>
                    <label className="text-gray-300 text-sm mb-2 block">Trading Mode</label>
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            onClick={() => setSettings({ ...settings, mode: 'NOTIFY_ONLY' })}
                            className={`p-3 rounded-lg flex flex-col items-center gap-2 transition ${settings.mode === 'NOTIFY_ONLY'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            <Bell size={20} />
                            <span className="text-xs font-medium">Notify Only</span>
                        </button>

                        <button
                            onClick={() => setSettings({ ...settings, mode: 'AUTO_BUY' })}
                            className={`p-3 rounded-lg flex flex-col items-center gap-2 transition ${settings.mode === 'AUTO_BUY'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            <ShoppingCart size={20} />
                            <span className="text-xs font-medium">Auto Buy</span>
                        </button>

                        <button
                            onClick={() => setSettings({ ...settings, mode: 'BOTH' })}
                            className={`p-3 rounded-lg flex flex-col items-center gap-2 transition ${settings.mode === 'BOTH'
                                ? 'bg-purple-600 text-white'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                                }`}
                        >
                            <CheckCircle size={20} />
                            <span className="text-xs font-medium">Both</span>
                        </button>
                    </div>
                </div>

                {/* Lot Size Configuration */}
                <div>
                    <button
                        onClick={() => setShowLotSizes(!showLotSizes)}
                        className="w-full flex items-center justify-between text-gray-300 text-sm mb-2"
                    >
                        <span className="font-medium">Lot Size Configuration</span>
                        <span className="text-xs text-gray-500">{showLotSizes ? '▼' : '▶'}</span>
                    </button>

                    {showLotSizes && (
                        <div className="space-y-2 bg-gray-700 p-3 rounded-lg">
                            {Object.entries(settings.lotSizes).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between">
                                    <label className="text-gray-300 text-xs uppercase">{key}</label>
                                    <input
                                        type="number"
                                        min="1"
                                        value={value}
                                        onChange={(e) => setSettings({
                                            ...settings,
                                            lotSizes: { ...settings.lotSizes, [key]: parseInt(e.target.value) || 1 }
                                        })}
                                        className="w-20 bg-gray-800 text-white px-2 py-1 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                                    />
                                </div>
                            ))}
                            <p className="text-xs text-gray-400 mt-2 italic">Default: 1 lot per F&O contract</p>
                        </div>
                    )}
                </div>

                {/* Safety Toggle */}
                {settings.mode !== 'NOTIFY_ONLY' && (
                    <div className="flex items-center justify-between">
                        <label className="text-gray-300 text-sm">Require Confirmation</label>
                        <button
                            onClick={() => setSettings({ ...settings, requireConfirmation: !settings.requireConfirmation })}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${settings.requireConfirmation ? 'bg-blue-600' : 'bg-gray-600'
                                }`}
                        >
                            <span
                                className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${settings.requireConfirmation ? 'translate-x-6' : 'translate-x-1'
                                    }`}
                            />
                        </button>
                    </div>
                )}

                {/* Status Indicator */}
                <div className="text-xs text-gray-400 flex items-center gap-2">
                    {isSaving ? (
                        <>
                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                            Saving...
                        </>
                    ) : (
                        <>
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            Settings saved
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
