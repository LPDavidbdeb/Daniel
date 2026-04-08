import MockAdapter from 'axios-mock-adapter';
import client from '@/api/client';
import { clearTokens, setTokens } from '@/auth';
describe('api client interceptors', () => {
  let mock: MockAdapter;
  beforeEach(() => {
    mock = new MockAdapter(client);
    localStorage.clear();
  });
  afterEach(() => {
    mock.restore();
    clearTokens();
  });
  it('adds bearer token to request headers', async () => {
    setTokens('my-access-token', 'my-refresh-token');
    mock.onGet('/protected').reply((config) => {
      expect(config.headers?.Authorization).toBe('Bearer my-access-token');
      return [200, { ok: true }];
    });
    const response = await client.get('/protected');
    expect(response.status).toBe(200);
  });
  it('clears tokens on 401 responses', async () => {
    setTokens('my-access-token', 'my-refresh-token');
    mock.onGet('/protected').reply(401, { detail: 'Unauthorized' });
    await expect(clientimport MockAdapter from 'axios-mock-adapter';
import client from '@/api/client';
import { cl()import client from '@/api/client';
import { ).import { clearTokens, setTcd "/Users/Louis-Philippe/Documents/GitHub/Daniel/frontend" && npm install
