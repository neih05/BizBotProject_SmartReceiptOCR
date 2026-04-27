import React, { useState } from 'react';
import { Search, Plus } from 'lucide-react';
import { accounts, suppliers } from '../mockData';

const MasterData = () => {
  const [tab, setTab] = useState('accounts');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Danh mục dữ liệu</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý hệ thống tài khoản và nhà cung cấp</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="flex border-b border-slate-100">
          <button 
            onClick={() => setTab('accounts')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${tab === 'accounts' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            Tài khoản kế toán (TT200)
          </button>
          <button 
            onClick={() => setTab('suppliers')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${tab === 'suppliers' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            Đối tác / Nhà cung cấp
          </button>
        </div>

        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input type="text" placeholder={`Tìm kiếm ${tab === 'accounts' ? 'tài khoản' : 'nhà cung cấp'}...`} className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-80" />
          </div>
          <button className="flex items-center px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
            <Plus className="w-4 h-4 mr-2" /> Thêm mới
          </button>
        </div>

        <div className="overflow-x-auto">
          {tab === 'accounts' ? (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Mã TK</th>
                  <th className="px-6 py-3 font-semibold">Tên tài khoản</th>
                  <th className="px-6 py-3 font-semibold">Loại</th>
                  <th className="px-6 py-3 font-semibold">Cấp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {accounts.map((acc, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-navy-900">{acc.code}</td>
                    <td className={`px-6 py-3 text-slate-700 ${acc.level > 1 ? 'pl-10' : 'font-semibold'}`}>{acc.name}</td>
                    <td className="px-6 py-3 text-slate-500">{acc.type}</td>
                    <td className="px-6 py-3 text-slate-500">Cấp {acc.level}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Tên công ty / NCC</th>
                  <th className="px-6 py-3 font-semibold">Mã số thuế</th>
                  <th className="px-6 py-3 font-semibold text-center">Số HĐ</th>
                  <th className="px-6 py-3 font-semibold">Lần GD gần nhất</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {suppliers.map((sup, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-navy-900">{sup.name}</td>
                    <td className="px-6 py-3 text-slate-600 font-mono">{sup.taxCode}</td>
                    <td className="px-6 py-3 text-center font-medium">{sup.invoicesCount}</td>
                    <td className="px-6 py-3 text-slate-500">{sup.lastTransaction}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default MasterData;
