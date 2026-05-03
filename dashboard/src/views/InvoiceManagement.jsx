import React, { useState, useEffect } from 'react';
import { Eye, FileImage, Search, Filter, Check, X, RotateCw, ZoomIn, ZoomOut, AlertTriangle } from 'lucide-react';
import { formatCurrency, accounts, departments, expenseTags } from '../mockData';

const InvoiceManagement = () => {
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // OCR Form State
  const [formData, setFormData] = useState({});

  const fetchInvoices = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/invoices');
      const data = await res.json();
      setInvoices(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const handleRowClick = (inv) => {
    setSelectedInvoice(inv);
    setFormData({
      supplierName: inv.store_name || inv.ocr.taxCode || '',
      taxCode: inv.ocr.taxCode || '',
      invNo: inv.ocr.invNo || '',
      date: inv.date,
      amount: inv.total_amount || 0,
      taxAmount: inv.ocr.taxAmount || 0,
      total: (inv.total_amount || 0) + (inv.ocr.taxAmount || 0),
      category: inv.ocr.category || 'Tiếp khách',
      debitAccount: '642',
      creditAccount: '111',
      department: 'Hành chính',
      notes: ''
    });
  };

  const closeSplitView = () => setSelectedInvoice(null);

  const handleAction = async (status) => {
    try {
      const res = await fetch(`http://localhost:8000/api/invoices/${selectedInvoice.id}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: status,
          debitAccount: formData.debitAccount,
          creditAccount: formData.creditAccount,
          category: formData.category,
          department: formData.department,
          notes: formData.notes,
          totalAmount: parseFloat(formData.amount) || 0
        })
      });
      if (res.ok) {
        closeSplitView();
        fetchInvoices();
      } else {
        alert("Có lỗi xảy ra khi cập nhật!");
      }
    } catch (err) {
      console.error(err);
      alert("Lỗi kết nối server!");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') closeSplitView();
  };

  const getStatusBadge = (status) => {
    switch(status) {
      case 'pending': return <span className="px-2.5 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">Chờ xử lý</span>;
      case 'processing': return <span className="px-2.5 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">Đang xử lý</span>;
      case 'approved': return <span className="px-2.5 py-1 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">Đã hạch toán</span>;
      case 'rejected': return <span className="px-2.5 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full">Bị từ chối</span>;
      default: return <span className="px-2.5 py-1 text-xs font-medium bg-slate-100 text-slate-700 rounded-full">{status}</span>;
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col" onKeyDown={handleKeyDown} tabIndex="0">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Quản lý hóa đơn</h2>
          <p className="text-sm text-slate-500 mt-1">Đối soát OCR và hạch toán tự động (Dữ liệu Live)</p>
        </div>
        {!selectedInvoice && (
          <div className="flex space-x-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <input 
                type="text" 
                placeholder="Tìm kiếm #Mã HĐ, tên..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-64" 
              />
            </div>
            <div className="relative">
              <Filter className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
              <select 
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="pl-9 pr-8 py-2 border border-slate-200 bg-white rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none cursor-pointer"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="pending">Chờ xử lý</option>
                <option value="approved">Đã hạch toán</option>
                <option value="rejected">Bị từ chối</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-1 overflow-hidden space-x-6">
        {/* Left/Main Content: Table */}
        <div className={`bg-white border border-slate-200 rounded-xl flex flex-col overflow-hidden transition-all duration-300 ${selectedInvoice ? 'hidden' : 'w-full'}`}>
          <div className="overflow-auto flex-1">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 sticky top-0 z-10 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 w-10"><input type="checkbox" className="rounded text-blue-600" /></th>
                  <th className="px-4 py-3 font-semibold">Mã HĐ</th>
                  <th className="px-4 py-3 font-semibold">Ngày nhận</th>
                  <th className="px-4 py-3 font-semibold">Người gửi</th>
                  <th className="px-4 py-3 font-semibold">Nhà cung cấp</th>
                  <th className="px-4 py-3 font-semibold">Danh mục</th>
                  <th className="px-4 py-3 font-semibold text-right">Số tiền tạm tính</th>
                  <th className="px-4 py-3 font-semibold text-center">Trạng thái</th>
                  <th className="px-4 py-3 font-semibold text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invoices
                  .filter(inv => filterStatus === 'all' || inv.status === filterStatus)
                  .filter(inv => {
                    if (!searchQuery) return true;
                    const query = searchQuery.toLowerCase();
                    return (
                      inv.id.toString().includes(query) ||
                      (inv.sender_name && inv.sender_name.toLowerCase().includes(query)) ||
                      (inv.store_name && inv.store_name.toLowerCase().includes(query)) ||
                      (inv.user_id && inv.user_id.toString().includes(query))
                    );
                  })
                  .map((inv) => (
                  <tr 
                    key={inv.id} 
                    className="hover:bg-blue-50 cursor-pointer group transition-colors"
                    onClick={() => handleRowClick(inv)}
                  >
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}><input type="checkbox" className="rounded text-blue-600" /></td>
                    <td className="px-4 py-3 font-medium">#{inv.id}</td>
                    <td className="px-4 py-3 text-slate-600">{inv.date}</td>
                    <td className="px-4 py-3 font-medium text-navy-900">{inv.sender_name || inv.user_id}</td>
                    <td className="px-4 py-3 text-slate-700">{inv.store_name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs font-medium whitespace-nowrap">
                        {inv.ocr?.category || 'Khác'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-navy-900">{formatCurrency(inv.total_amount)}</td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex flex-col items-center gap-1">
                        {getStatusBadge(inv.status)}
                        {inv.ocr?.is_suspicious_duplicate && (
                          <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold bg-orange-50 text-orange-600 rounded border border-orange-200" title="Nghi ngờ trùng lặp">
                            <AlertTriangle className="w-3 h-3 mr-1" />Trùng lặp
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-100 rounded-md opacity-0 group-hover:opacity-100 transition-all">
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && (
                  <tr>
                    <td colSpan="8" className="px-4 py-8 text-center text-slate-500">
                      Chưa có hóa đơn nào trong hệ thống. Hãy tải lên qua Telegram!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Split View Active */}
        {selectedInvoice && (
          <>
            {/* Split Left: Image Preview */}
            <div className="w-[60%] bg-slate-100 border border-slate-200 rounded-xl flex flex-col relative overflow-hidden">
              <div className="absolute top-4 right-4 flex space-x-2 z-10">
                <button className="p-2 bg-white/90 shadow-sm rounded-lg hover:bg-white text-slate-700"><ZoomIn className="w-4 h-4" /></button>
                <button className="p-2 bg-white/90 shadow-sm rounded-lg hover:bg-white text-slate-700"><ZoomOut className="w-4 h-4" /></button>
                <button className="p-2 bg-white/90 shadow-sm rounded-lg hover:bg-white text-slate-700"><RotateCw className="w-4 h-4" /></button>
              </div>
              <div className="flex-1 flex items-center justify-center p-8 overflow-hidden">
                <div className="bg-white shadow-lg w-full max-w-md h-full rounded flex flex-col items-center justify-center border border-slate-200 overflow-hidden">
                  {selectedInvoice.ocr?.file_id ? (
                    <img src={`http://localhost:8000/api/telegram-image/${selectedInvoice.ocr.file_id}`} alt="Invoice" className="w-full h-full object-contain" />
                  ) : (
                    <>
                      <FileImage className="w-16 h-16 text-slate-300 mb-4" />
                      <p className="text-slate-500 font-medium">Không có ảnh đính kèm (Nhập tay)</p>
                      <p className="text-sm text-slate-400 mt-2">ID: {selectedInvoice.id}</p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Split Right: OCR Form */}
            <div className="w-[40%] bg-white border border-slate-200 rounded-xl flex flex-col shadow-sm">
              {(() => { var isLocked = selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'; return null; })()}
              <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50 rounded-t-xl">
                <h3 className="font-bold text-navy-900">Đối soát Hóa đơn #{selectedInvoice.id}</h3>
                <button onClick={closeSplitView} className="p-1 text-slate-400 hover:text-slate-600 rounded">
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex-1 overflow-auto p-6">
                <div className="space-y-5">
                  {selectedInvoice.ocr?.is_suspicious_duplicate && (
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-start">
                      <AlertTriangle className="w-5 h-5 text-orange-600 mr-3 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-bold text-orange-800">⚠️ Cảnh báo: Hóa đơn có dấu hiệu trùng lặp</p>
                        <p className="text-xs text-orange-700 mt-1">
                          Cùng cửa hàng, cùng ngày, cùng số tiền với hóa đơn 
                          {selectedInvoice.ocr?.duplicate_of_ids?.length > 0 
                            ? selectedInvoice.ocr.duplicate_of_ids.map(id => ` #${id}`).join(',') 
                            : ' trước đó'}
                          . Vui lòng xem xét kỹ trước khi duyệt.
                        </p>
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 mb-1">Nhà cung cấp</label>
                      <input type="text" value={formData.supplierName} onChange={e => setFormData({...formData, supplierName: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 mb-1">Mã số thuế</label>
                      <input type="text" value={formData.taxCode} onChange={e => setFormData({...formData, taxCode: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 mb-1">Số hóa đơn</label>
                      <input type="text" value={formData.invNo} onChange={e => setFormData({...formData, invNo: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 mb-1">Ngày hóa đơn</label>
                      <input type="text" value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                    </div>
                  </div>

                  <div className="border-t border-slate-100 pt-5 mt-2">
                    <h4 className="text-xs font-bold text-navy-900 uppercase tracking-wider mb-3">Chi tiết Tiền & Thuế</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-600">Tổng tiền chưa VAT</span>
                        <input type="text" value={formData.amount} onChange={e => setFormData({...formData, amount: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-32 px-3 py-1.5 border border-slate-200 rounded-md text-sm text-right focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-600">Tiền thuế GTGT</span>
                        <input type="text" value={formData.taxAmount} onChange={e => setFormData({...formData, taxAmount: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-32 px-3 py-1.5 border border-slate-200 rounded-md text-sm text-right focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} />
                      </div>
                      <div className="flex justify-between items-center pt-2 border-t border-slate-100">
                        <span className="text-sm font-bold text-navy-900">Tổng cộng thanh toán</span>
                        <span className="text-lg font-bold text-blue-600">{formatCurrency(formData.total)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-100 pt-5 mt-2">
                    <h4 className="text-xs font-bold text-navy-900 uppercase tracking-wider mb-3">Thông tin Hạch toán</h4>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Tài khoản Nợ</label>
                        <select value={formData.debitAccount} onChange={e => setFormData({...formData, debitAccount: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`}>
                          {accounts.filter(a => a.level === 1 || a.level === 2).map(acc => (
                            <option key={acc.code} value={acc.code}>{acc.code} - {acc.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Tài khoản Có</label>
                        <select value={formData.creditAccount} onChange={e => setFormData({...formData, creditAccount: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`}>
                          {accounts.filter(a => a.level === 1 || a.level === 2).map(acc => (
                            <option key={acc.code} value={acc.code}>{acc.code} - {acc.name}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Loại chi phí</label>
                        <select value={formData.category} onChange={e => setFormData({...formData, category: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`}>
                          <option value="">-- Chọn loại chi phí --</option>
                          {expenseTags.map(tag => (
                            <option key={tag.id} value={tag.name}>{tag.name}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Phòng ban (Cost Center)</label>
                        <select value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`}>
                          {departments.map(d => <option key={d.name} value={d.name}>{d.name}</option>)}
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-500 mb-1">Ghi chú (Gửi kèm về Telegram)</label>
                      <textarea rows="2" value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} disabled={selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected'} className={`w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:ring-1 focus:ring-blue-500 ${(selectedInvoice.status === 'approved' || selectedInvoice.status === 'rejected') ? 'bg-slate-100 text-slate-500 cursor-not-allowed' : ''}`} placeholder="Thêm ghi chú nội bộ..."></textarea>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-between rounded-b-xl">
                <button onClick={closeSplitView} className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50">
                  Đóng (Esc)
                </button>
                {selectedInvoice.status === 'approved' ? (
                  <span className="px-4 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center">
                    <Check className="w-4 h-4 mr-2" /> Đã hạch toán — Không thể chỉnh sửa
                  </span>
                ) : selectedInvoice.status === 'rejected' ? (
                  <span className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 border border-red-200 rounded-lg flex items-center">
                    <X className="w-4 h-4 mr-2" /> Đã từ chối — Không thể chỉnh sửa
                  </span>
                ) : (
                  <div className="space-x-3">
                    <button onClick={() => handleAction('rejected')} className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50">
                      Từ chối
                    </button>
                    <button onClick={() => handleAction('approved')} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 flex items-center">
                      <Check className="w-4 h-4 mr-2" /> Ghi sổ (Enter)
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default InvoiceManagement;
