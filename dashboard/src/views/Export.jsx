import React, { useState, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, Filter, Calendar } from 'lucide-react';
import { formatCurrency } from '../mockData';
import { apiClient } from '../apiClient';

const Export = () => {
  const [invoices, setInvoices] = useState([]);
  const [filter, setFilter] = useState({
    dateRange: 'Tháng này',
    department: 'Tất cả',
    status: 'Đã hạch toán'
  });

  useEffect(() => {
    apiClient('/invoices')
      .then(res => res.json())
      .then(data => setInvoices(data))
      .catch(err => console.error(err));
  }, []);

  const handleExport = async (type) => {
    try {
      const endpoint = type === 'Excel' ? '/export-excel' : '/export';
      const extension = type === 'Excel' ? 'xlsx' : 'csv';
      const response = await apiClient(endpoint);
      
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

  const approvedInvoices = invoices.filter(i => i.status === 'approved');

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
              <select className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white" defaultValue="Tháng này">
                <option>Hôm nay</option>
                <option>Tuần này</option>
                <option>Tháng này</option>
                <option>Quý này</option>
                <option>Tùy chọn...</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Phòng ban</label>
            <select className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white" defaultValue="Tất cả phòng ban">
              <option>Tất cả phòng ban</option>
              <option>Hành chính</option>
              <option>Sales</option>
              <option>Marketing</option>
              <option>Kế toán</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Trạng thái</label>
            <select className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white" defaultValue="Đã hạch toán">
              <option>Tất cả trạng thái</option>
              <option>Đã hạch toán</option>
              <option>Chờ xử lý</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Khoảng tiền</label>
            <input type="range" className="w-full" min="0" max="100000000" defaultValue="0" />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>0đ</span>
              <span>100.000.000đ+</span>
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700 mb-2">Người gửi (Có thể chọn nhiều)</label>
            <input type="text" placeholder="Nhập tên người gửi..." className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500" />
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
            Tổng cộng: {formatCurrency(approvedInvoices.reduce((sum, inv) => sum + (inv.total_amount || 0), 0))}
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 font-semibold">Mã HĐ</th>
                <th className="px-6 py-3 font-semibold">Ngày</th>
                <th className="px-6 py-3 font-semibold">Người gửi</th>
                <th className="px-6 py-3 font-semibold">Nhà cung cấp</th>
                <th className="px-6 py-3 font-semibold">Loại CP</th>
                <th className="px-6 py-3 font-semibold text-right">Thành tiền</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {approvedInvoices.slice(0, 5).map(inv => (
                <tr key={inv.id}>
                  <td className="px-6 py-3 font-medium text-navy-900">{inv.id}</td>
                  <td className="px-6 py-3 text-slate-600">{inv.date}</td>
                  <td className="px-6 py-3 text-slate-700">{inv.sender_name || inv.user_id}</td>
                  <td className="px-6 py-3 text-slate-700">{inv.store_name}</td>
                  <td className="px-6 py-3 text-slate-500">{inv.ocr?.category || 'Khác'}</td>
                  <td className="px-6 py-3 text-right font-medium text-navy-900">{formatCurrency(inv.total_amount || 0)}</td>
                </tr>
              ))}
              {approvedInvoices.length === 0 && (
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
