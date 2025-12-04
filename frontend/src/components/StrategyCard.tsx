import { useState } from 'react';
import { Settings, AlertCircle, Zap } from 'lucide-react';
import { cn } from '../lib/utils';

interface StrategyConfig {
    mode: 'AUTO' | 'NOTIFY';
    quantity: number;
    stopLoss: number;
    target: number;
    trailingStop: boolean;
}

interface StrategyCardProps {
    title: string;
    description: string;
    isActive: boolean;
    onToggle: (active: boolean) => void;
    config: StrategyConfig;
    onConfigChange: (config: StrategyConfig) => void;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
    title,
    description,
    isActive,
    onToggle,
    config,
    onConfigChange,
}) => {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className={cn("glass-panel rounded-xl border-0 transition-all", isActive ? "bg-blue-500/10 shadow-lg shadow-blue-500/10" : "")}>
            <div className="p-4 flex items-start justify-between gap-3">
                <div className="flex-1">
                    <div className="flex items-center gap-3">
                        <input
                            type="checkbox"
                            checked={isActive}
                            onChange={(e) => onToggle(e.target.checked)}
                            className="h-4 w-4 rounded border-white/20 bg-gray-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-gray-900 cursor-pointer"
                        />
                        <h3 className="font-medium text-sm text-gray-200">{title}</h3>
                    </div>
                    <p className="text-xs text-gray-400 mt-2 ml-7 leading-relaxed">{description}</p>
                </div>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-gray-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-white/5"
                >
                    <Settings size={16} />
                </button>
            </div>

            {expanded && (
                <div className="px-4 pb-4 ml-7 space-y-4 border-t border-white/5 pt-4">
                    <div className="flex items-center gap-2 text-xs">
                        <button
                            onClick={() => onConfigChange({ ...config, mode: 'AUTO' })}
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all duration-200",
                                config.mode === 'AUTO'
                                    ? "bg-emerald-600 hover:bg-emerald-700 text-white border-emerald-500 shadow-lg shadow-emerald-500/20"
                                    : "bg-gray-800/50 text-gray-300 border-white/10 hover:bg-gray-800 hover:border-white/20 hover:text-white"
                            )}
                        >
                            <Zap size={12} /> Auto Buy
                        </button>
                        <button
                            onClick={() => onConfigChange({ ...config, mode: 'NOTIFY' })}
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all duration-200",
                                config.mode === 'NOTIFY'
                                    ? "bg-blue-600 hover:bg-blue-700 text-white border-blue-500 shadow-lg shadow-blue-500/20"
                                    : "bg-gray-800/50 text-gray-300 border-white/10 hover:bg-gray-800 hover:border-white/20 hover:text-white"
                            )}
                        >
                            <AlertCircle size={12} /> Notify Only
                        </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                            <label className="block text-gray-400 mb-1.5 font-medium">Quantity</label>
                            <input
                                type="number"
                                min="0"
                                step="1"
                                value={config.quantity}
                                onChange={(e) => {
                                    const val = Math.max(0, parseInt(e.target.value) || 0);
                                    onConfigChange({ ...config, quantity: val });
                                }}
                                className="w-full bg-gray-900 text-white border border-white/10 rounded-lg px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1.5 font-medium">Target %</label>
                            <input
                                type="number"
                                min="0"
                                step="0.1"
                                value={config.target}
                                onChange={(e) => {
                                    const val = Math.max(0, parseFloat(e.target.value) || 0);
                                    onConfigChange({ ...config, target: val });
                                }}
                                className="w-full bg-gray-900 text-white border border-white/10 rounded-lg px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1.5 font-medium">Stop Loss %</label>
                            <input
                                type="number"
                                min="0"
                                step="0.1"
                                value={config.stopLoss}
                                onChange={(e) => {
                                    const val = Math.max(0, parseFloat(e.target.value) || 0);
                                    onConfigChange({ ...config, stopLoss: val });
                                }}
                                className="w-full bg-gray-900 text-white border border-white/10 rounded-lg px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                            />
                        </div>
                        <div className="flex items-end pb-2">
                            <label className="flex items-center gap-2 cursor-pointer text-gray-300 hover:text-white transition-colors">
                                <input
                                    type="checkbox"
                                    checked={config.trailingStop}
                                    onChange={(e) => onConfigChange({ ...config, trailingStop: e.target.checked })}
                                    className="h-4 w-4 rounded border-white/20 bg-gray-800 text-blue-600 cursor-pointer"
                                />
                                <span className="font-medium">Trailing SL</span>
                            </label>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
