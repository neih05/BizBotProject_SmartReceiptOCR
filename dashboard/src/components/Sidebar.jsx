import React from 'react';
import { 
  LayoutDashboard, 
  Receipt, 
  Users, 
  Database, 
  FileDown, 
  LogOut 
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'overview', label: 'Tổng quan', icon: LayoutDashboard },
    { id: 'invoices', label: 'Hóa đơn', icon: Receipt, badge: 12 },
    { id: 'employees', label: 'Nhân sự', icon: Users },
    { id: 'master', label: 'Danh mục', icon: Database },
    { id: 'export', label: 'Xuất báo cáo', icon: FileDown },
  ];

  return (
    <div className="w-64 h-screen bg-navy-900 text-white flex flex-col fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold tracking-tight text-blue-400">BizBot</h1>
        <p className="text-xs text-slate-400 mt-1">Smart Receipt OCR</p>
      </div>

      <nav className="flex-1 mt-6">
        <ul>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-6 py-3 text-sm font-medium transition-colors ${
                    isActive 
                      ? 'bg-blue-600 text-white border-l-4 border-blue-400' 
                      : 'text-slate-300 hover:bg-navy-800 hover:text-white border-l-4 border-transparent'
                  }`}
                >
                  <div className="flex items-center">
                    <Icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </div>
                  {item.badge && (
                    <span className="bg-yellow-500 text-navy-900 text-xs font-bold px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-navy-800">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-lg">
            L
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium">Nguyễn Thị Lan</p>
            <p className="text-xs text-slate-400">Kế toán trưởng</p>
          </div>
        </div>
        <button className="w-full flex items-center text-sm text-slate-400 hover:text-white transition-colors">
          <LogOut className="w-4 h-4 mr-2" />
          Đăng xuất
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
