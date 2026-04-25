"use client";

import { useEffect, useState } from "react";

// Mock data types to match FastAPI
type Order = {
  order_id: string;
  phase: string;
  status: string;
  amount_usdc: number;
  created_at: string;
  tx_hash?: string;
  card?: {
    number: string;
    cvv: string;
    expiry: string;
  };
};

type SystemStatus = {
  status: string;
  frozen: boolean;
  consecutive_failures: number;
  contract: string;
};

export default function Dashboard() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [simAmount, setSimAmount] = useState("0.01");
  const [viewAll, setViewAll] = useState(false);

  const wallet = "0xDC48211759e415eF86b6858C65532A63D60AEF3C"; // Hardcoded for demo

  const rawApiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const API_BASE = rawApiBase.endsWith('/') ? rawApiBase.slice(0, -1) : rawApiBase;

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch Status
        const statusRes = await fetch(`${API_BASE}/status`);
        if (statusRes.ok) {
          setSystemStatus(await statusRes.json());
        }

        // Fetch Orders
        const ordersRes = await fetch(`${API_BASE}/v1/orders/?limit=10`, {
          headers: {
            "X-Agent-Wallet": wallet,
          },
        });
        if (ordersRes.ok) {
          const data = await ordersRes.json();
          setOrders(data.orders);
        }
      } catch (error) {
        console.error("Failed to fetch data", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const totalSpent = orders.reduce((acc, order) => {
    if (order.status === "delivered" || order.status === "processing" || order.status === "ordering") {
      return acc + order.amount_usdc;
    }
    return acc;
  }, 0);

  const getPhaseBadge = (phase: string) => {
    switch (phase) {
      case "ready": return "badge-success";
      case "awaiting_payment": return "badge-warning";
      case "processing": return "badge-info";
      case "failed": case "rejected": case "expired": return "badge-danger";
      default: return "badge-info";
    }
  };

  const handleDownloadCSV = () => {
    const headers = ["Order ID", "Date", "Amount (USDC)", "Phase", "Tx Hash"];
    const rows = orders.map(o => [
      o.order_id,
      new Date(o.created_at).toLocaleString(),
      o.amount_usdc.toString(),
      o.phase,
      o.tx_hash || ""
    ]);
    
    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "arccards_orders.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="container flex justify-center items-center" style={{ minHeight: '80vh' }}>
        <div style={{ width: 40, height: 40, border: '3px solid rgba(255,255,255,0.1)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const displayOrders = viewAll ? orders : orders.slice(0, 5);

  return (
    <div className="container animate-fade-in">
      <div className="flex justify-between items-center" style={{ marginBottom: '2rem' }}>
        <div>
          <h1>Fleet Overview</h1>
          <p style={{ color: 'rgba(255,255,255,0.6)' }}>Manage your AI agents&apos; virtual card usage on Arc Network.</p>
        </div>
        <div className="flex gap-4">
          <button className="btn btn-secondary" onClick={handleDownloadCSV}>Download CSV</button>
          <button className="btn btn-primary" onClick={() => setShowOrderModal(true)}>Simulate Agent</button>
          <button className="btn btn-primary" onClick={() => setShowPolicyModal(true)}>+ New Policy</button>
        </div>
      </div>

      {systemStatus?.frozen && (
        <div className="glass" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)', padding: '1rem 1.5rem', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ color: 'var(--danger)', margin: 0, fontSize: '1.1rem' }}>System Frozen</h3>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.9rem', color: 'rgba(255,255,255,0.7)' }}>Circuit breaker triggered after {systemStatus.consecutive_failures} failures.</p>
          </div>
          <button className="btn" style={{ background: 'var(--danger)', color: 'white' }} onClick={() => alert('Unfreeze API endpoint not implemented yet.')}>Unfreeze System</button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-6" style={{ marginBottom: '3rem' }}>
        <div className="glass" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Total Spend (USDC)</h4>
          <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>${totalSpent.toFixed(2)}</div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--success)' }}>Live Updates</div>
        </div>
        
        <div className="glass" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Active Agents</h4>
          <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>1</div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'rgba(255,255,255,0.5)' }}>Using wallet ...AEF3C</div>
        </div>

        <div className="glass" style={{ padding: '1.5rem' }}>
          <h4 style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Arc Contract</h4>
          <div style={{ fontSize: '1.2rem', fontWeight: 500, wordBreak: 'break-all', fontFamily: 'monospace', color: 'var(--primary)' }}>
            {systemStatus?.contract ? `${systemStatus.contract.slice(0,12)}...${systemStatus.contract.slice(-4)}` : "Loading..."}
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--success)' }}>Connected & Listening</div>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="glass" style={{ padding: '1.5rem' }}>
        <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ margin: 0 }}>Recent Agent Orders</h3>
          <button className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }} onClick={() => setViewAll(!viewAll)}>
            {viewAll ? "View Less" : "View All"}
          </button>
        </div>
        
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Phase</th>
                <th>Arc Tx Hash</th>
              </tr>
            </thead>
            <tbody>
              {displayOrders.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'rgba(255,255,255,0.5)' }}>
                    No orders found. Run the E2E test script to generate some.
                  </td>
                </tr>
              ) : (
                displayOrders.map((order) => (
                  <tr key={order.order_id}>
                    <td style={{ fontFamily: 'monospace', color: 'rgba(255,255,255,0.8)' }}>
                      {order.order_id.split('-')[0]}...
                    </td>
                    <td style={{ color: 'rgba(255,255,255,0.6)' }}>
                      {new Date(order.created_at).toLocaleString()}
                    </td>
                    <td style={{ fontWeight: 600 }}>${order.amount_usdc.toFixed(2)}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <span className={`badge ${getPhaseBadge(order.phase)}`}>
                          {order.phase.replace('_', ' ')}
                        </span>
                        {order.phase === "awaiting_payment" && (
                          <button 
                            className="btn btn-primary" 
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                            onClick={async () => {
                              try {
                                const res = await fetch(`${API_BASE}/v1/orders/${order.order_id}/pay`, {
                                  method: "POST"
                                });
                                if (res.ok) alert('Payment sent on-chain! Watch the status update.');
                                else alert('Error sending payment.');
                              } catch (e) {
                                alert('Network error');
                              }
                            }}
                          >
                            Pay On-Chain
                          </button>
                        )}
                        {order.phase === "ready" && order.card && (
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', borderColor: 'var(--success)', color: 'var(--success)' }}
                            onClick={() => alert(`Visa Card Generated!\n\nPAN: ${order.card?.number}\nCVV: ${order.card?.cvv}\nExp: ${order.card?.expiry}`)}
                          >
                            View Card
                          </button>
                        )}
                      </div>
                    </td>
                    <td>
                      {order.tx_hash ? (
                        <a href={`https://testnet.arcscan.app/tx/${order.tx_hash}`} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none', fontFamily: 'monospace' }}>
                          {order.tx_hash.slice(0, 10)}...
                        </a>
                      ) : (
                        <span style={{ color: 'rgba(255,255,255,0.3)' }}>-</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Policy Modal */}
      {showPolicyModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass animate-fade-in" style={{ padding: '2rem', width: '100%', maxWidth: '400px' }}>
            <h3>Create New Policy</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>Set spend limits for your AI agents.</p>
            
            <div className="flex-col gap-4" style={{ display: 'flex' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Policy Name</label>
                <input type="text" placeholder="e.g. Default Agent Limit" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Daily Limit (USDC)</label>
                <input type="number" defaultValue="50" />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Per-Order Limit (USDC)</label>
                <input type="number" defaultValue="25" />
              </div>
              
              <div className="flex gap-4" style={{ marginTop: '1rem' }}>
                <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowPolicyModal(false)}>Cancel</button>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => { alert('Policy saved! (Demo)'); setShowPolicyModal(false); }}>Save Policy</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simulate Order Modal */}
      {showOrderModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass animate-fade-in" style={{ padding: '2rem', width: '100%', maxWidth: '400px' }}>
            <h3>Simulate Agent Order</h3>
            <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>Create a new order. The backend will trigger Lithic.</p>
            
            <div className="flex-col gap-4" style={{ display: 'flex' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem' }}>Amount (USDC)</label>
                <input 
                  type="number" 
                  step="0.01"
                  value={simAmount}
                  onChange={(e) => setSimAmount(e.target.value)}
                />
              </div>
              
              <div className="flex gap-4" style={{ marginTop: '1rem' }}>
                <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setShowOrderModal(false)}>Cancel</button>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={async () => {
                  try {
                    const res = await fetch(`${API_BASE}/v1/orders/`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        "X-Agent-Wallet": wallet
                      },
                      body: JSON.stringify({ amount_usdc: parseFloat(simAmount) })
                    });
                    if (res.ok) {
                      setShowOrderModal(false);
                      // Optional: We can just let the table auto-update
                    } else {
                      const err = await res.json();
                      alert(`Error: ${err.detail || "Failed to create order"}`);
                    }
                  } catch (e) {
                    alert("Network error");
                  }
                }}>Submit Order</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
