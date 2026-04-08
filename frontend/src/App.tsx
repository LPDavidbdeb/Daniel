import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from '@/pages/Login';
import Home from '@/pages/Home';
import ImportEleves from '@/pages/ImportEleves';
import { isAuthenticated, subscribeAuthChange } from '@/auth';

// Composant pour protéger les routes
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => subscribeAuthChange(() => setAuthenticated(isAuthenticated())), []);

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/import/eleves" 
          element={
            <ProtectedRoute>
              <ImportEleves />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
