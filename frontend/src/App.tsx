import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from '@/pages/Login';
import Home from '@/pages/Home';
import ImportEleves from '@/pages/ImportEleves';
import ImportResultats from '@/pages/ImportResultats';
import AdminUsers from '@/pages/AdminUsers';
import Navbar from '@/components/Navbar';
import client from '@/api/client';
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

const SuperuserRoute = ({ children }: { children: JSX.Element }) => {
  const [isAllowed, setIsAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;

    client
      .get('/admin/me')
      .then((response) => {
        if (mounted) {
          setIsAllowed(Boolean(response.data?.is_superuser));
        }
      })
      .catch(() => {
        if (mounted) {
          setIsAllowed(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  if (isAllowed === null) {
    return <div className="p-6 text-sm text-gray-600">Verification des permissions...</div>;
  }

  if (!isAllowed) {
    return <Navigate to="/" replace />;
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
        <Route 
          path="/groupes" 
          element={
            <ProtectedRoute>
              <Layout><GroupList /></Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/groupes/:groupId" 
          element={
            <ProtectedRoute>
              <Layout><GroupDetail /></Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/eleves/:fiche" 
          element={
            <ProtectedRoute>
              <Layout><StudentDetail /></Layout>
            </ProtectedRoute>
          } 
        />
        </Routes>

          path="/admin/users"
          element={
            <ProtectedRoute>
              <SuperuserRoute>
                <Layout><AdminUsers /></Layout>
              </SuperuserRoute>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
