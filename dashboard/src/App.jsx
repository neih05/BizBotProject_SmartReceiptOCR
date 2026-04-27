import React, { useState } from 'react';
import DashboardLayout from './components/DashboardLayout';
import Overview from './views/Overview';
import InvoiceManagement from './views/InvoiceManagement';
import Employees from './views/Employees';
import MasterData from './views/MasterData';
import Export from './views/Export';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

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
