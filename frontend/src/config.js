// Configuration for API endpoints
// Change LOCAL_IP to your actual local IP address for friends to access
const LOCAL_IP = '192.168.1.100'; // Replace with your actual local IP

export const config = {
  // For local development
  development: {
    API_BASE_URL: 'http://localhost:8010'
  },
  
  external: {
    API_BASE_URL: `http://${LOCAL_IP}:8010`
  }
};


export const CURRENT_MODE = 'development'; // Change to 'external' for friends

export const getApiUrl = () => {
  return config[CURRENT_MODE].API_BASE_URL;
}; 