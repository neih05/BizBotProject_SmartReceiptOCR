import React, { useState } from 'react';
import { Search, Plus, X, Loader2 } from 'lucide-react';
import { accounts as defaultAccounts, suppliers as defaultSuppliers, expenseTags as defaultTags } from '../mockData';

const MasterData = () => {
  const [tab, setTab] = useState('accounts');
  const [accountsList, setAccountsList] = useState(defaultAccounts);
  const [suppliersList, setSuppliersList] = useState(defaultSuppliers);
  const [tagsList, setTagsList] = useState(defaultTags);
  const [showModal, setShowModal] = useState(false);
  const [formError, setFormError] = useState('');

  // Form states cho từng loại
  const [accForm, setAccForm] = useState({ code: '', name: '', type: 'Tài sản', level: 1 });
  const [supForm, setSupForm] = useState({ name: '', taxCode: '' });
  const [tagForm, setTagForm] = useState({ name: '', description: '' });

  const openModal = () => {
    setFormError('');
    setAccForm({ code: '', name: '', type: 'Tài sản', level: 1 });
    setSupForm({ name: '', taxCode: '' });
    setTagForm({ name: '', description: '' });
    setShowModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setFormError('');

    if (tab === 'accounts') {
      if (!accForm.code || !accForm.name) {
        setFormError('Vui lòng nhập đầy đủ Mã TK và Tên tài khoản.');
        return;
      }
      if (accountsList.some(a => a.code === accForm.code)) {
        setFormError('Mã tài khoản này đã tồn tại.');
        return;
      }
      setAccountsList([...accountsList, { ...accForm }]);
    } else if (tab === 'suppliers') {
      if (!supForm.name) {
        setFormError('Vui lòng nhập tên nhà cung cấp.');
        return;
      }
      setSuppliersList([...suppliersList, { ...supForm, invoicesCount: 0, lastTransaction: '-' }]);
    } else {
      if (!tagForm.name) {
        setFormError('Vui lòng nhập tên danh mục.');
        return;
      }
      if (tagsList.some(t => t.name === tagForm.name)) {
        setFormError('Danh mục này đã tồn tại.');
        return;
      }
      setTagsList([...tagsList, { id: Date.now(), name: tagForm.name, description: tagForm.description }]);
    }

    setShowModal(false);
  };

  const deleteTag = (id) => {
    setTagsList(tagsList.filter(t => t.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-navy-900">Danh mục dữ liệu</h2>
          <p className="text-sm text-slate-500 mt-1">Quản lý hệ thống tài khoản, nhà cung cấp và danh mục chi phí</p>
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
          <button 
            onClick={() => setTab('tags')}
            className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${tab === 'tags' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
          >
            Danh mục chi phí (Tags)
          </button>
        </div>

        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input type="text" placeholder={`Tìm kiếm ${tab === 'accounts' ? 'tài khoản' : tab === 'suppliers' ? 'nhà cung cấp' : 'danh mục'}...`} className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-80" />
          </div>
          <button
            onClick={openModal}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
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
                {accountsList.map((acc, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-navy-900">{acc.code}</td>
                    <td className={`px-6 py-3 text-slate-700 ${acc.level > 1 ? 'pl-10' : 'font-semibold'}`}>{acc.name}</td>
                    <td className="px-6 py-3 text-slate-500">{acc.type}</td>
                    <td className="px-6 py-3 text-slate-500">Cấp {acc.level}</td>
                  </tr>
                ))}
                {accountsList.length === 0 && (
                  <tr><td colSpan="4" className="px-6 py-8 text-center text-slate-500">Chưa có tài khoản nào.</td></tr>
                )}
              </tbody>
            </table>
          ) : tab === 'suppliers' ? (
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
                {suppliersList.map((sup, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-navy-900">{sup.name}</td>
                    <td className="px-6 py-3 text-slate-600 font-mono">{sup.taxCode}</td>
                    <td className="px-6 py-3 text-center font-medium">{sup.invoicesCount}</td>
                    <td className="px-6 py-3 text-slate-500">{sup.lastTransaction}</td>
                  </tr>
                ))}
                {suppliersList.length === 0 && (
                  <tr><td colSpan="4" className="px-6 py-8 text-center text-slate-500">Chưa có nhà cung cấp nào.</td></tr>
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Tên danh mục (Tag)</th>
                  <th className="px-6 py-3 font-semibold">Mô tả</th>
                  <th className="px-6 py-3 font-semibold text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {tagsList.map((tag) => (
                  <tr key={tag.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3 font-medium text-navy-900">
                      <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs border border-blue-100">{tag.name}</span>
                    </td>
                    <td className="px-6 py-3 text-slate-600">{tag.description}</td>
                    <td className="px-6 py-3 text-center">
                      <button onClick={() => deleteTag(tag.id)} className="text-red-600 hover:text-red-800 text-xs font-medium">Xóa</button>
                    </td>
                  </tr>
                ))}
                {tagsList.length === 0 && (
                  <tr><td colSpan="3" className="px-6 py-8 text-center text-slate-500">Chưa có danh mục chi phí nào.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal Thêm mới */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-navy-900">
                Thêm {tab === 'accounts' ? 'tài khoản kế toán' : tab === 'suppliers' ? 'nhà cung cấp' : 'danh mục chi phí'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {tab === 'accounts' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Mã tài khoản <span className="text-red-500">*</span></label>
                    <input type="text" placeholder="VD: 6429" value={accForm.code}
                      onChange={(e) => setAccForm({ ...accForm, code: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tên tài khoản <span className="text-red-500">*</span></label>
                    <input type="text" placeholder="VD: Chi phí bảo hiểm" value={accForm.name}
                      onChange={(e) => setAccForm({ ...accForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Loại</label>
                      <select value={accForm.type} onChange={(e) => setAccForm({ ...accForm, type: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white">
                        <option>Tài sản</option>
                        <option>Nguồn vốn</option>
                        <option>Doanh thu</option>
                        <option>Chi phí</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">Cấp</label>
                      <select value={accForm.level} onChange={(e) => setAccForm({ ...accForm, level: Number(e.target.value) })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 bg-white">
                        <option value={1}>Cấp 1</option>
                        <option value={2}>Cấp 2</option>
                      </select>
                    </div>
                  </div>
                </>
              )}

              {tab === 'suppliers' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tên công ty / NCC <span className="text-red-500">*</span></label>
                    <input type="text" placeholder="VD: Công ty TNHH ABC" value={supForm.name}
                      onChange={(e) => setSupForm({ ...supForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Mã số thuế</label>
                    <input type="text" placeholder="VD: 0101234567" value={supForm.taxCode}
                      onChange={(e) => setSupForm({ ...supForm, taxCode: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </>
              )}

              {tab === 'tags' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Tên danh mục <span className="text-red-500">*</span></label>
                    <input type="text" placeholder="VD: Bảo hiểm" value={tagForm.name}
                      onChange={(e) => setTagForm({ ...tagForm, name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Mô tả</label>
                    <input type="text" placeholder="VD: Chi phí bảo hiểm nhân viên, tài sản" value={tagForm.description}
                      onChange={(e) => setTagForm({ ...tagForm, description: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </>
              )}

              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2 rounded-lg">
                  {formError}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
                  Hủy
                </button>
                <button type="submit"
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                  <Plus className="w-4 h-4 mr-2" /> Thêm mới
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterData;
