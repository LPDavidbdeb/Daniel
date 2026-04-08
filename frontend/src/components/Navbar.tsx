import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileUp, 
  Users, 
  LogOut, 
  ChevronDown,
  Database
} from 'lucide-react';

const Navbar = () => {
  const [isImportOpen, setIsImportOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    // Note: If you have an auth context, you should update it here
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <Database className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
                GPI-Optimizer
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-4">
              <Link 
                to="/" 
                className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                <LayoutDashboard className="h-4 w-4" />
                <span>Tableau de bord</span>
              </Link>

              {/* Dropdown Importations */}
              <div className="relative">
                <button
                  onMouseEnter={() => setIsImportOpen(true)}
                  className="flex items-center space-x-1 text-gray-600 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium transition-colors h-16"
                >
                  <FileUp className="h-4 w-4" />
                  <span>Importations</span>
                  <ChevronDown className={`h-4 w-4 transition-transform ${isImportOpen ? 'rotate-180' : ''}`} />
                </button>

                {isImportOpen && (
                  <div 
                    onMouseLeave={() => setIsImportOpen(false)}
                    className="absolute left-0 mt-0 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 animate-in fade-in zoom-in-95 duration-100"
                  >
                    <div className="py-1">
                      <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider border-b border-gray-50">
                        Extraits GPI
                      </div>
                      <Link
                        to="/import/eleves"
                        onClick={() => setIsImportOpen(false)}
                        className="flex items-center space-x-2 px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                      >
                        <Users className="h-4 w-4" />
                        <span>Élèves Actifs</span>
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* User Section */}
          <div className="flex items-center">
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 text-gray-500 hover:text-red-600 px-3 py-2 rounded-md text-sm font-medium transition-colors"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
