import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from '@/pages/Login';
import Home from '@/pages/Home';
import ImportEleves from '@/pages/ImportEleves';
import ImportResultats from '@/pages/ImportResultats';
import Navbar from '@/components/Navbar';
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

// Layout pour inclure la Navbar sur les pages protégées
const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gray-50">
    <Navbar />
    <main>{children}</main>
  </div>
);

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        {/* Routes Protégées avec Layout */}
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <Layout><Home /></Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/import/eleves" 
          element={
            <ProtectedRoute>
              <Layout><ImportEleves /></Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/import/resultats" 
          element={
            <ProtectedRoute>
              <Layout><ImportResultats /></Layout>
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;
