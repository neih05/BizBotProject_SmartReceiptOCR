import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { Wallet, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';
import { departments, weeklyChartData, categoryPieData, formatCurrency } from '../mockData';

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#6366f1', '#8b5cf6'];

const Overview = () => {
  const [chartTab, setChartTab] = useState('week');
  const [stats, setStats] = useState({
    total_spent_week: 0,
    pending_invoices: 0,
    approved_month_count: 0,
    approved_month_value: 0,
    budget_warnings: 0
  });

  useEffect(() => {
    fetch('http://localhost:8000/api/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-navy-900">Tổng quan</h2>
        <div className="text-sm text-slate-500">
          Cập nhật lần cuối: {new Date().toLocaleString('vi-VN')}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Tổng chi tiêu</p>
              <h3 className="text-2xl font-bold text-navy-900">{formatCurrency(stats.total_spent_week)}</h3>
            </div>
            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
              <Wallet className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-medium text-slate-500 mt-4 flex items-center">
            Toàn bộ hệ thống
          </p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Hóa đơn chờ xử lý</p>
              <h3 className="text-2xl font-bold text-navy-900">{stats.pending_invoices}</h3>
            </div>
            <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-medium text-amber-600 mt-4">Cần xử lý ngay</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Đã hạch toán tháng này</p>
              <h3 className="text-2xl font-bold text-navy-900">{stats.approved_month_count}</h3>
            </div>
            <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-medium text-slate-500 mt-4">Tổng giá trị: {formatCurrency(stats.approved_month_value)}</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm font-medium text-slate-500 mb-1">Cảnh báo vượt ngân sách</p>
              <h3 className="text-2xl font-bold text-red-600">{stats.budget_warnings}</h3>
            </div>
            <div className="p-3 bg-red-50 text-red-600 rounded-lg">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs font-medium text-slate-500 mt-4">Phòng ban</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bar Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-navy-900">Chi tiêu theo thời gian</h3>
            <div className="flex space-x-2">
              {['week', 'month', 'quarter'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setChartTab(tab)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    chartTab === tab 
                      ? 'bg-navy-900 text-white' 
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tab === 'week' ? 'Tuần' : tab === 'month' ? 'Tháng' : 'Quý'}
                </button>
              ))}
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyChartData} margin={{ top: 10, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{fill: '#64748b'}}
                  tickFormatter={(value) => `${value / 1000000}M`}
                />
                <RechartsTooltip 
                  formatter={(value) => formatCurrency(value)}
                  cursor={{fill: '#f8fafc'}}
                />
                <Legend iconType="circle" />
                <Bar dataKey="Tiếp khách" stackId="a" fill="#3b82f6" radius={[0, 0, 4, 4]} />
                <Bar dataKey="Văn phòng phẩm" stackId="a" fill="#f59e0b" />
                <Bar dataKey="Di chuyển" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-100">
          <h3 className="text-lg font-bold text-navy-900 mb-6">Phân loại chi phí</h3>
          <div className="h-60 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoryPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-2xl font-bold text-navy-900">100%</p>
                <p className="text-xs text-slate-500">Tổng chi</p>
              </div>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {categoryPieData.map((item, index) => (
              <div key={index} className="flex items-center text-xs">
                <span className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: COLORS[index % COLORS.length]}}></span>
                <span className="text-slate-600 truncate">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budget Warnings Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="text-lg font-bold text-navy-900">Cảnh báo ngân sách phòng ban (Mô phỏng)</h3>
        </div>
        <div className="p-6">
          <div className="space-y-6">
            {departments.map((dept, idx) => {
              const percent = (dept.spent / dept.budget) * 100;
              let barColor = 'bg-emerald-500';
              if (percent > 90) barColor = 'bg-red-500';
              else if (percent > 75) barColor = 'bg-amber-500';

              return (
                <div key={idx}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-navy-900">{dept.name}</span>
                    <span className="text-slate-500">
                      <span className="font-medium text-slate-900">{formatCurrency(dept.spent)}</span> / {formatCurrency(dept.budget)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5">
                    <div className={`${barColor} h-2.5 rounded-full`} style={{ width: `${Math.min(percent, 100)}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
