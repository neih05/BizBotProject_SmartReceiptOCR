export const employees = [];

export const invoices = [];

export const accounts = [];

export const suppliers = [];

export const departments = [];

export const expenseTags = [];

export const weeklyChartData = [];

export const categoryPieData = [];

export const formatCurrency = (value) => {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value);
};
