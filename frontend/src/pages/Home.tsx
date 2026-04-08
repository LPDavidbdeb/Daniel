import { useNavigate } from 'react-router-dom';
import { clearTokens } from '@/auth';

const Home = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearTokens();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg text-center max-w-md w-full">
        <h1 className="text-3xl font-bold text-blue-600 mb-4">Bienvenue sur GPI-Optimizer</h1>
        <p className="text-gray-600 mb-8">Votre tableau de bord est prêt.</p>
        
        <button
          onClick={handleLogout}
          className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
        >
          Se déconnecter
        </button>
      </div>
    </div>
  );
};

export default Home;
