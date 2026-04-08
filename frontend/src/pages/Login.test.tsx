import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Login from '@/pages/Login';
import client from '@/api/client';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('Login page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('shows invalid credentials message on 401', async () => {
    vi.mocked(client.post).mockRejectedValue({
      isAxiosError: true,
      response: { status: 401, data: {} },
    });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Mot de passe'), {
      target: { value: 'wrong' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    expect(await screen.findByText('Identifiants invalides.')).toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('stores tokens and redirects on success', async () => {
    vi.mocked(client.post).mockResolvedValue({
      data: { access: 'access-token', refresh: 'refresh-token' },
    });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'user@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Mot de passe'), {
      target: { value: 'StrongPass123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Se connecter' }));

    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('access-token');
      expect(localStorage.getItem('refresh')).toBe('refresh-token');
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });
});
