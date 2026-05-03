import React, { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, Filter, Calendar } from 'lucide-react';
import { formatCurrency, departments } from '../mockData';
import { apiClient } from '../apiClient';

const Export = () => {
  const [invoices, setInvoices] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filter, setFilter] = useState({
    dateRange: 'Tháng này',
    startDate: '',
    endDate: '',
    department: 'Tất cả phòng ban',
    status: 'Tất cả trạng thái',
    maxAmount: 100000000,
    senders: []
  });

  useEffect(() => {
    apiClient('/invoices')
      .then(res => res.json())
      .then(data => setInvoices(data))
      .catch(err => console.error(err));
      
    apiClient('/employees')
      .then(res => res.json())
      .then(data => setEmployees(data))
      .catch(err => console.error(err));
  }, []);

  const handleExport = async (type) => {
    try {
      const endpoint = type === 'Excel' ? '/export-excel' : '/export';
      const extension = type === 'Excel' ? 'xlsx' : 'csv';
      
      const queryParams = new URLSearchParams({
        dateRange: filter.dateRange,
        startDate: filter.startDate,
        endDate: filter.endDate,
        department: filter.department,
        status: filter.status,
        maxAmount: filter.maxAmount,
        senders: filter.senders.join(',')
      }).toString();
      
      const response = await apiClient(`${endpoint}?${queryParams}`);
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bao_cao_chi_phi_${new Date().getTime()}.${extension}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Lỗi khi tải file:', error);
      alert('Có lỗi xảy ra khi xuất báo cáo.');
    }
  };

  const getFilteredInvoices = () => {
    return invoices.filter(inv => {
      // Status filter
      let invStatusStr = inv.status === 'approved' ? 'Đã hạch toán' : (inv.status === 'pending' ? 'Chờ xử lý' : 'Tất cả trạng thái');
      if (filter.status !== 'Tất cả trạng thái' && invStatusStr !== filter.status) return false;
      
      // Amount filter
      if ((inv.total_amount || 0) > filter.maxAmount) return false;
      
      // Department filter
      let invDept = inv.ocr?.department || 'Tất cả phòng ban';
      if (filter.department !== 'Tất cả phòng ban' && invDept !== filter.department) return false;
      
      // Senders filter
      if (filter.senders.length > 0) {
        if (!filter.senders.includes((inv.user_id || '').toString())) return false;
      }
      
      // Date range filter is too complex for simple local preview without a date library, 
      // but we will do basic filtering for Excel/CSV backend.
      return true;
    });
  };

  const filteredInvoices = getFilteredInvoices();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Xuất Báo cáo</h2>
          <p className="text-sm text-slate-500 mt-1">Trích xuất dữ liệu hóa đơn ra Excel/CSV</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        <h3 className="font-bold text-navy-900 mb-4 flex items-center">
          <Filter className="w-4 h-4 mr-2" /> Bộ lọc nâng cao
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Khoảng thời gian</label>
            <div className="relative">
              <Calendar className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <select 
                value={filter.dateRange} 
                onChange={e => setFilter({...filter, dateRange: e.target.value})}
                className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white"
              >
                <option>Hôm nay</option>
                <option>Tuần này</option>
                <option>Tháng này</option>
                <option>Quý này</option>
                <option>Tùy chọn...</option>
              </select>
            </div>
            {filter.dateRange === 'Tùy chọn...' && (
              <div className="flex items-center space-x-2 mt-2">
                <input type="date" value={filter.startDate} onChange={e => setFilter({...filter, startDate: e.target.value})} className="w-1/2 px-2 py-1.5 border border-slate-200 rounded text-sm focus:ring-1 focus:ring-blue-500" />
                <span className="text-slate-400">-</span>
                <input type="date" value={filter.endDate} onChange={e => setFilter({...filter, endDate: e.target.value})} className="w-1/2 px-2 py-1.5 border border-slate-200 rounded text-sm focus:ring-1 focus:ring-blue-500" />
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Phòng ban</label>
            <select 
              value={filter.department} 
              onChange={e => setFilter({...filter, department: e.target.value})}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white"
            >
              <option>Tất cả phòng ban</option>
              {departments.map(d => <option key={d.name}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Trạng thái</label>
            <select 
              value={filter.status} 
              onChange={e => setFilter({...filter, status: e.target.value})}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white"
            >
              <option>Tất cả trạng thái</option>
              <option>Đã hạch toán</option>
              <option>Chờ xử lý</option>
              <option>Bị từ chối</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Khoảng tiền: Tối đa {formatCurrency(filter.maxAmount)}</label>
            <input 
              type="range" 
              className="w-full" 
              min="0" 
              max="100000000" 
              step="1000000"
              value={filter.maxAmount}
              onChange={e => setFilter({...filter, maxAmount: Number(e.target.value)})}
            />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0đ</span>
              <span>100M+</span>
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-2">Người gửi (Có thể chọn nhiều)</label>
            <div className="p-3 border border-slate-200 rounded-lg bg-slate-50 max-h-32 overflow-y-auto grid grid-cols-2 gap-2">
              {employees.length === 0 ? (
                <span className="text-sm text-slate-500">Chưa có dữ liệu nhân viên</span>
              ) : employees.map(emp => (
                <label key={emp.telegramId} className="flex items-center space-x-2 text-sm text-slate-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="rounded text-blue-600 focus:ring-blue-500"
                    checked={filter.senders.includes(emp.telegramId.toString())}
                    onChange={(e) => {
                      const newSenders = e.target.checked 
                        ? [...filter.senders, emp.telegramId.toString()] 
                        : filter.senders.filter(id => id !== emp.telegramId.toString());
                      setFilter({...filter, senders: newSenders});
                    }}
                  />
                  <span>{emp.name}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
          <button onClick={() => handleExport('CSV')} className="flex items-center px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
            <FileText className="w-4 h-4 mr-2" /> Xuất CSV
          </button>
          <button onClick={() => handleExport('Excel')} className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors">
            <FileSpreadsheet className="w-4 h-4 mr-2" /> Xuất Excel
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-bold text-navy-900">Xem trước kết quả lọc (Mẫu 5 dòng)</h3>
          <span className="text-sm text-slate-500">
            Tổng cộng: {formatCurrency(filteredInvoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0))}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 font-semibold">Mã HĐ</th>
                <th className="px-6 py-3 font-semibold">Ngày chứng từ</th>
                <th className="px-6 py-3 font-semibold">Người gửi</th>
                <th className="px-6 py-3 font-semibold">Nhà cung cấp</th>
                <th className="px-6 py-3 font-semibold">Danh mục</th>
                <th className="px-6 py-3 font-semibold text-right">Thành tiền</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredInvoices.slice(0, 5).map(inv => (
                <tr key={inv.id}>
                  <td className="px-6 py-3 font-medium text-navy-900">{inv.id}</td>
                  <td className="px-6 py-3 text-slate-600">{inv.date}</td>
                  <td className="px-6 py-3 text-slate-700">{inv.sender_name || inv.user_id}</td>
                  <td className="px-6 py-3 text-slate-700">{inv.store_name}</td>
                  <td className="px-6 py-3 text-slate-500">{inv.ocr?.category || 'Khác'}</td>
                  <td className="px-6 py-3 text-right font-medium text-navy-900">{formatCurrency(inv.total_amount || 0)}</td>
                </tr>
              ))}
              {filteredInvoices.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-6 py-8 text-center text-slate-500">
                    Chưa có hóa đơn nào phù hợp với bộ lọc.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Export;
