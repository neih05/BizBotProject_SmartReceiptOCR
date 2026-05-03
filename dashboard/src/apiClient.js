const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const apiClient = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_role');
      window.dispatchEvent(new Event('unauthorized'));
      throw new Error('Unauthorized');
    }
    return response;
  } catch (error) {
    throw error;
  }
};
