import { useEffect, useState } from 'react';

type SelectionItem = { token: string; autobuy: boolean; quantity: number };

export const AutoBuySelector = () => {
  const [items, setItems] = useState<SelectionItem[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  const loadSelection = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/autobuy/selection');
      const data = await res.json();
      setItems(data.selection || []);
    } catch (e) {
      console.error('Failed to load auto-buy selection', e);
    }
  };

  const saveSelection = async () => {
    setIsSaving(true);
    try {
      await fetch('http://127.0.0.1:8000/api/autobuy/selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(items),
      });
    } catch (e) {
      console.error('Failed to save auto-buy selection', e);
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    loadSelection();
  }, []);

  const toggleItem = (idx: number) => {
    const updated = [...items];
    updated[idx].autobuy = !updated[idx].autobuy;
    setItems(updated);
  };

  const setQty = (idx: number, q: number) => {
    const updated = [...items];
    updated[idx].quantity = Math.max(1, Math.floor(q || 1));
    setItems(updated);
  };

  return (
    <div className="glass-panel rounded-xl p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">⚙️</div>
        <h3 className="text-white font-semibold tracking-wide">Auto-Buy Selection</h3>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <div className="text-xs text-gray-400">No tokens configured yet.</div>
        ) : (
          items.map((it, idx) => (
            <div key={it.token} className="flex items-center justify-between bg-gray-800/40 border border-white/5 rounded-lg px-3 py-2">
              <div className="flex-1">
                <div className="text-sm text-white">{it.token}</div>
                <div className="text-[11px] text-gray-400">Quantity</div>
              </div>
              <input
                type="number"
                min={1}
                value={it.quantity}
                onChange={(e) => setQty(idx, parseInt(e.target.value))}
                className="w-16 bg-gray-900 text-white px-2 py-1 rounded-md text-xs text-center border border-white/10"
              />
              <button
                onClick={() => toggleItem(idx)}
                className={`ml-3 px-3 py-1 rounded-md text-xs font-medium border ${it.autobuy ? 'bg-emerald-600 text-white border-emerald-500' : 'bg-gray-700 text-gray-200 border-white/10'}`}
              >
                {it.autobuy ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          ))
        )}
      </div>

      <div className="flex items-center justify-end gap-2 mt-3">
        <button
          onClick={saveSelection}
          className="px-3 py-1.5 rounded-md text-xs font-medium bg-blue-600 text-white border border-blue-500"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </div>
    </div>
  );
};
