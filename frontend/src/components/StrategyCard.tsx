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
        <div className={cn("rounded-lg border transition-all", isActive ? "border-primary bg-primary/5" : "border-border bg-card")}>
            <div className="p-4 flex items-start justify-between">
                <div className="flex-1">
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={isActive}
                            onChange={(e) => onToggle(e.target.checked)}
                            className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        />
                        <h3 className="font-medium text-sm">{title}</h3>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 ml-6">{description}</p>
                </div>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="text-muted-foreground hover:text-foreground"
                >
                    <Settings size={16} />
                </button>
            </div>

            {expanded && (
                <div className="px-4 pb-4 ml-6 space-y-3">
                    <div className="flex items-center gap-2 text-xs">
                        <button
                            onClick={() => onConfigChange({ ...config, mode: 'AUTO' })}
                            className={cn("flex items-center gap-1 px-2 py-1 rounded border", config.mode === 'AUTO' ? "bg-primary text-primary-foreground border-primary" : "bg-background border-border")}
                        >
                            <Zap size={12} /> Auto Buy
                        </button>
                        <button
                            onClick={() => onConfigChange({ ...config, mode: 'NOTIFY' })}
                            className={cn("flex items-center gap-1 px-2 py-1 rounded border", config.mode === 'NOTIFY' ? "bg-primary text-primary-foreground border-primary" : "bg-background border-border")}
                        >
                            <AlertCircle size={12} /> Notify Only
                        </button>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                            <label className="block text-muted-foreground mb-1">Quantity</label>
                            <input
                                type="number"
                                value={config.quantity}
                                onChange={(e) => onConfigChange({ ...config, quantity: Number(e.target.value) })}
                                className="w-full bg-background border border-border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-muted-foreground mb-1">Target %</label>
                            <input
                                type="number"
                                value={config.target}
                                onChange={(e) => onConfigChange({ ...config, target: Number(e.target.value) })}
                                className="w-full bg-background border border-border rounded px-2 py-1"
                            />
                        </div>
                        <div>
                            <label className="block text-muted-foreground mb-1">Stop Loss</label>
                            <input
                                type="number"
                                value={config.stopLoss}
                                onChange={(e) => onConfigChange({ ...config, stopLoss: Number(e.target.value) })}
                                className="w-full bg-background border border-border rounded px-2 py-1"
                            />
                        </div>
                        <div className="flex items-center pt-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={config.trailingStop}
                                    onChange={(e) => onConfigChange({ ...config, trailingStop: e.target.checked })}
                                    className="rounded border-gray-300"
                                />
                                <span>Trailing SL</span>
                            </label>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
