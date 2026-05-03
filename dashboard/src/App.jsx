import React, { useState, useEffect } from 'react';
import DashboardLayout from './components/DashboardLayout';
import Overview from './views/Overview';
import InvoiceManagement from './views/InvoiceManagement';
import Employees from './views/Employees';
import MasterData from './views/MasterData';
import Export from './views/Export';
import Login from './views/Login';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('access_token'));

  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
    };

    window.addEventListener('unauthorized', handleUnauthorized);
    return () => window.removeEventListener('unauthorized', handleUnauthorized);
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <Overview />;
      case 'invoices':
        return <InvoiceManagement />;
      case 'employees':
        return <Employees />;
      case 'master':
        return <MasterData />;
      case 'export':
        return <Export />;
      default:
        return <Overview />;
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </DashboardLayout>
  );
}

export default App;
