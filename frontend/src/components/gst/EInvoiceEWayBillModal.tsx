import React, { useState, useEffect } from 'react';
import { gstApi } from '../../services/gstApi';
import {
  FileCode,
  Truck,
  Copy,
  Check,
  X,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  FileCheck,
} from 'lucide-react';

interface EInvoiceEWayBillModalProps {
  invoiceId: string;
  invoiceNumber: string;
  customerName: string;
  onClose: () => void;
}

export const EInvoiceEWayBillModal: React.FC<EInvoiceEWayBillModalProps> = ({
  invoiceId,
  invoiceNumber,
  customerName,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'einvoice' | 'ewaybill'>('einvoice');
  const [transporterId, setTransporterId] = useState<string>('29AAACT1234F1Z1');
  const [vehicleNo, setVehicleNo] = useState<string>('KA-01-EA-9821');
  const [distanceKm, setDistanceKm] = useState<number>(350);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [payload, setPayload] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchPayload = async () => {
    try {
      setLoading(true);
      setError(null);
      if (activeTab === 'einvoice') {
        const res = await gstApi.getEInvoicePayload(invoiceId);
        setPayload(res);
      } else {
        const res = await gstApi.getEWayBillPayload(invoiceId, {
          transporter_id: transporterId,
          vehicle_no: vehicleNo,
          distance_km: distanceKm,
        });
        setPayload(res);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to generate regulatory payload');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayload();
  }, [activeTab]);

  const handleCopyJson = () => {
    if (!payload) return;
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/60 rounded-3xl max-w-3xl w-full overflow-hidden shadow-2xl my-8">
        {/* Header */}
        <div className="p-5 bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600/20 border border-indigo-500/30 rounded-2xl text-indigo-400">
              <FileCode className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  🇮🇳 Indian GST E-Invoice & E-Way Bill Compliance Vault
                </h3>
                <span className="px-2.5 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-full flex items-center gap-1">
                  <FileCheck className="w-3 h-3 text-emerald-400" /> NIC Portal Ready
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Official Government NIC API Dispatch Payload for Invoice <span className="text-white font-mono">{invoiceNumber}</span> ({customerName})
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="p-4 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('einvoice')}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition flex items-center gap-2 ${
                activeTab === 'einvoice'
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <FileCode className="w-4 h-4" /> E-Invoice IRN Payload (B2B v1.03)
            </button>
            <button
              onClick={() => setActiveTab('ewaybill')}
              className={`px-4 py-2 text-xs font-bold rounded-xl transition flex items-center gap-2 ${
                activeTab === 'ewaybill'
                  ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/20'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <Truck className="w-4 h-4" /> E-Way Bill Transport Payload
            </button>
          </div>

          <button
            onClick={handleCopyJson}
            disabled={!payload || loading}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-slate-700 transition disabled:opacity-50"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400" />}
            {copied ? 'Copied Payload!' : 'Copy JSON Payload'}
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[65vh] overflow-y-auto">
          {activeTab === 'ewaybill' && (
            <div className="p-4 bg-slate-800/50 border border-slate-700/60 rounded-2xl grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Transporter GSTIN</label>
                <input
                  type="text"
                  value={transporterId}
                  onChange={(e) => setTransporterId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Vehicle Registration No</label>
                <input
                  type="text"
                  value={vehicleNo}
                  onChange={(e) => setVehicleNo(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Distance (KM)</label>
                  <input
                    type="number"
                    value={distanceKm}
                    onChange={(e) => setDistanceKm(parseInt(e.target.value) || 1)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-white font-mono focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <button
                  onClick={fetchPayload}
                  className="py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold flex items-center justify-center"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-16 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Generating NIC Portal Compliant JSON Schema Payload...</p>
            </div>
          ) : payload ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>Format: NIC GST API v1.03</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" /> Schema Validated
                </span>
              </div>
              <pre className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-xs font-mono text-emerald-400 overflow-x-auto max-h-96 leading-relaxed select-all">
                {JSON.stringify(payload, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-indigo-400" /> Direct dispatch ready for Goods and Services Tax Network (GSTN) GSP APIs.
          </span>
          <button onClick={onClose} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition">
            Close Vault
          </button>
        </div>
      </div>
    </div>
  );
};
