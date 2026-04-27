import React, { useState, useEffect } from 'react';
import { UserPlus, Search, ShieldCheck, ShieldAlert, History } from 'lucide-react';
import { formatCurrency } from '../mockData';

const Employees = () => {
  const [employeesData, setEmployeesData] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/employees')
      .then(res => res.json())
      .then(data => setEmployeesData(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Quản lý Nhân sự</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý quyền truy cập và thống kê hóa đơn của nhân viên (Dữ liệu Live)</p>
        </div>
        <button className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
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
                        <p className="text-xs text-slate-500">Nickname: "{emp.nickname}" • {emp.department}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-600 font-mono text-xs">{emp.telegramId}</td>
                  <td className="px-6 py-4 text-center font-medium text-navy-900">{emp.invoicesSent}</td>
                  <td className="px-6 py-4 text-right font-medium text-navy-900">{formatCurrency(emp.totalValue)}</td>
                  <td className="px-6 py-4 text-center">
                    {emp.status === 'approved' ? (
                      <span className="px-2.5 py-1 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center w-max mx-auto">
                        <ShieldCheck className="w-3 h-3 mr-1" /> Đã phê duyệt
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full flex items-center justify-center w-max mx-auto">
                        <ShieldAlert className="w-3 h-3 mr-1" /> Chờ duyệt
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {emp.status === 'pending' ? (
                      <div className="flex space-x-2 justify-center">
                        <button className="px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700">Duyệt</button>
                        <button className="px-3 py-1 bg-red-50 text-red-600 text-xs font-medium rounded hover:bg-red-100">Từ chối</button>
                      </div>
                    ) : (
                      <div className="flex space-x-2 justify-center">
                        <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded" title="Lịch sử hóa đơn">
                          <History className="w-4 h-4" />
                        </button>
                        <button className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded" title="Thu hồi quyền">
                          <ShieldAlert className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {employeesData.length === 0 && (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-slate-500">
                    Đang tải dữ liệu nhân sự...
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

export default Employees;
