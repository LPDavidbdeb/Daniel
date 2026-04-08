import React, { useState } from 'react';
import axios from 'axios';
import client from '@/api/client';

type CreateUserForm = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_active: boolean;
  is_superuser: boolean;
};

const initialForm: CreateUserForm = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  is_staff: false,
  is_active: true,
  is_superuser: false,
};

const AdminUsers = () => {
  const [form, setForm] = useState<CreateUserForm>(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (key: keyof CreateUserForm, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await client.post('/admin/users', form);
      setSuccess('Utilisateur cree avec succes.');
      setForm(initialForm);
    } catch (err: unknown) {
      if (!axios.isAxiosError(err)) {
        setError('Erreur inattendue.');
      } else if (!err.response) {
        setError('Impossible de joindre l\'API.');
      } else if (err.response.status === 403) {
        setError('Acces refuse: seuls les superusers peuvent creer des utilisateurs.');
      } else if (err.response.status === 409) {
        setError('Un utilisateur avec cet email existe deja.');
      } else {
        setError(err.response.data?.detail ?? 'Erreur serveur.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Administration - Creation d'utilisateur</h1>

      {error && <div className="mb-4 rounded-lg bg-red-100 p-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded-lg bg-green-100 p-3 text-sm text-green-700">{success}</div>}

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div>
          <label htmlFor="admin-email" className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input
            id="admin-email"
            type="email"
            value={form.email}
            onChange={(e) => handleChange('email', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            required
          />
        </div>

        <div>
          <label htmlFor="admin-password" className="mb-1 block text-sm font-medium text-gray-700">Mot de passe</label>
          <input
            id="admin-password"
            type="password"
            value={form.password}
            onChange={(e) => handleChange('password', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
            required
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="admin-first-name" className="mb-1 block text-sm font-medium text-gray-700">Prenom</label>
            <input
              id="admin-first-name"
              type="text"
              value={form.first_name}
              onChange={(e) => handleChange('first_name', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </div>
          <div>
            <label htmlFor="admin-last-name" className="mb-1 block text-sm font-medium text-gray-700">Nom</label>
            <input
              id="admin-last-name"
              type="text"
              value={form.last_name}
              onChange={(e) => handleChange('last_name', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_staff}
              onChange={(e) => handleChange('is_staff', e.target.checked)}
            />
            Utilisateur staff
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => handleChange('is_active', e.target.checked)}
            />
            Utilisateur actif
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.is_superuser}
              onChange={(e) => handleChange('is_superuser', e.target.checked)}
            />
            Donner les droits superuser
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? 'Creation...' : 'Creer l\'utilisateur'}
        </button>
      </form>
    </div>
  );
};

export default AdminUsers;

