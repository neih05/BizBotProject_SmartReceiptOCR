import React, { useState, useEffect } from 'react';
import { UserPlus, Search, ShieldCheck, ShieldAlert, History, X, Loader2 } from 'lucide-react';
import { formatCurrency } from '../mockData';
import { apiClient } from '../apiClient';

const Employees = () => {
  const [employeesData, setEmployeesData] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ employee_id: '', real_name: '' });
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmAction, setConfirmAction] = useState(null);

  const fetchEmployees = () => {
    apiClient('/employees')
      .then(res => res.json())
      .then(data => setEmployeesData(data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const executeAction = async () => {
    if (!confirmAction) return;
    
    const emp = confirmAction.payload;
    try {
      const res = await apiClient(`/employees/${emp.id}/status`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !emp.isActive }),
      });
      if (res.ok) fetchEmployees();
      else alert('Có lỗi xảy ra khi cập nhật trạng thái.');
    } catch (err) {
      alert('Không thể kết nối đến server.');
    }
    setConfirmAction(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!formData.employee_id || !formData.real_name) {
      setFormError('Vui lòng điền đầy đủ thông tin.');
      return;
    }

    if (!/^\d+$/.test(formData.employee_id)) {
      setFormError('Telegram ID chỉ được chứa số.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await apiClient('/employees', {
        method: 'POST',
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        const err = await res.json();
        setFormError(err.detail || 'Đã xảy ra lỗi.');
        setIsSubmitting(false);
        return;
      }

      // Thành công
      setShowModal(false);
      setFormData({ employee_id: '', real_name: '' });
      fetchEmployees(); // Tải lại danh sách
    } catch (err) {
      setFormError('Không thể kết nối đến server.');
    }
    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Quản lý Nhân sự</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý quyền truy cập và thống kê hóa đơn của nhân viên (Dữ liệu Live)</p>
        </div>
        <button
          onClick={() => { setShowModal(true); setFormError(''); }}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <UserPlus className="w-4 h-4 mr-2" /> Thêm nhân viên
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex justify-between items-center">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input type="text" placeholder="Tìm kiếm nhân viên..." className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-80" />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 font-semibold">Nhân viên</th>
                <th className="px-6 py-4 font-semibold">Telegram ID</th>
                <th className="px-6 py-4 font-semibold text-center">Số HĐ</th>
                <th className="px-6 py-4 font-semibold text-right">Tổng giá trị</th>
                <th className="px-6 py-4 font-semibold text-center">Trạng thái</th>
                <th className="px-6 py-4 font-semibold text-center">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {employeesData.map((emp) => (
                <tr key={emp.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm uppercase">
                        {(emp.name || 'U').substring(0, 1)}
                      </div>
                      <div className="ml-3">
                        <p className="font-medium text-navy-900">{emp.name || 'Chưa đăng ký'}</p>
                        <p className="text-xs text-slate-500">{emp.department}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-600 font-mono text-xs">{emp.telegramId}</td>
                  <td className="px-6 py-4 text-center font-medium text-navy-900">{emp.invoicesSent}</td>
                  <td className="px-6 py-4 text-right font-medium text-navy-900">{formatCurrency(emp.totalValue)}</td>
                  <td className="px-6 py-4 text-center">
                    {emp.isActive ? (
                      <span className="px-2.5 py-1 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center w-max mx-auto">
                        <ShieldCheck className="w-3 h-3 mr-1" /> Đã cấp quyền
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 text-xs font-medium bg-slate-100 text-slate-500 rounded-full flex items-center justify-center w-max mx-auto">
                        <ShieldAlert className="w-3 h-3 mr-1" /> Đã thu hồi
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex space-x-2 justify-center">
                      <button 
                        onClick={() => setConfirmAction({ type: 'toggle', payload: emp })}
                        className={`p-1.5 rounded ${emp.isActive ? 'text-slate-400 hover:text-orange-600 hover:bg-orange-50' : 'text-slate-400 hover:text-emerald-600 hover:bg-emerald-50'}`} 
                        title={emp.isActive ? "Thu hồi quyền" : "Cấp lại quyền"}
                      >
                        {emp.isActive ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {employeesData.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-slate-500">
                    Chưa có nhân sự nào trong hệ thống.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Thêm nhân viên */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-navy-900">Thêm nhân viên mới</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Telegram ID <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="VD: 6200223111"
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-slate-400 mt-1">Nhân viên gửi /start cho Bot để lấy ID này.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Họ tên <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  placeholder="VD: Nguyễn Văn A"
                  value={formData.real_name}
                  onChange={(e) => setFormData({ ...formData, real_name: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">
                  {formError}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Đang lưu...</>
                  ) : (
                    <><UserPlus className="w-4 h-4 mr-2" /> Thêm nhân viên</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-navy-900">Xác nhận thao tác</h3>
              <button onClick={() => setConfirmAction(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <p className="text-slate-600">
                {confirmAction.payload.isActive 
                  ? 'Bạn có chắc chắn muốn thu hồi quyền truy cập của nhân viên này? Nhân viên sẽ không thể sử dụng bot cho đến khi được cấp lại quyền.'
                  : 'Bạn có chắc chắn muốn cấp lại quyền truy cập cho nhân viên này?'}
              </p>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setConfirmAction(null)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
                >
                  Hủy bỏ
                </button>
                <button
                  onClick={executeAction}
                  className={`px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors ${
                    confirmAction.payload.isActive
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-emerald-600 hover:bg-emerald-700'
                  }`}
                >
                  Xác nhận
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Employees;
