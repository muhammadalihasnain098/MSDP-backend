# Connecting Frontend (Next.js) to Backend (Django)

This guide explains how to integrate your React/Next.js frontend with this Django backend.

## 🔗 Overview

```
Next.js Frontend          Django Backend
(Port 3000)              (Port 8000)
     │                        │
     │    HTTP Requests       │
     │───────────────────────→│
     │                        │
     │    JSON Responses      │
     │←───────────────────────│
     │                        │
```

## 🚀 Quick Setup

### 1. Backend Setup (Already Done!)
The backend is configured with CORS to allow frontend requests.

**In `config/settings.py`:**
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Your Next.js dev server
    'https://your-app.vercel.app',  # Production frontend
]
```

### 2. Frontend Setup (In Your Next.js Project)

#### Create API Client (`lib/api.ts` or `lib/api.js`)

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Get access token from storage
const getAccessToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

// API client with authentication
export const api = {
  async request(endpoint: string, options: RequestInit = {}) {
    const token = getAccessToken();
    
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/auth/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'API request failed');
    }

    return response.json();
  },

  // Auth endpoints
  async login(username: string, password: string) {
    const data = await this.request('/api/users/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    // Save tokens
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    
    return data.user;
  },

  async register(userData: any) {
    const data = await this.request('/api/users/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    
    // Save tokens
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    
    return data.user;
  },

  async getProfile() {
    return this.request('/api/users/profile/');
  },

  // Dataset endpoints
  async uploadDataset(formData: FormData) {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/datasets/`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData, // Don't set Content-Type for FormData
    });

    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  },

  async getDatasets() {
    return this.request('/api/datasets/');
  },

  // Forecasting endpoints
  async getModels() {
    return this.request('/api/forecasting/models/');
  },

  async trainModel(modelData: any) {
    return this.request('/api/forecasting/models/', {
      method: 'POST',
      body: JSON.stringify(modelData),
    });
  },

  async getForecasts() {
    return this.request('/api/forecasting/forecasts/');
  },

  // Reports endpoints
  async generateReport(reportData: any) {
    return this.request('/api/reports/', {
      method: 'POST',
      body: JSON.stringify(reportData),
    });
  },

  async downloadReport(reportId: number) {
    const token = getAccessToken();
    const response = await fetch(
      `${API_BASE_URL}/api/reports/${reportId}/download/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) throw new Error('Download failed');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${reportId}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
  },
};
```

#### Create Environment Variable

**`.env.local` (for development):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**`.env.production` (for production):**
```env
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## 📝 Usage Examples

### 1. Login Page (`app/auth/login/page.tsx`)

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const user = await api.login(username, password);
      console.log('Logged in:', user);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      {error && <p className="text-red-500">{error}</p>}
      <button type="submit">Login</button>
    </form>
  );
}
```

### 2. Dataset Upload (`components/datasets/upload.tsx`)

```typescript
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export function DatasetUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    formData.append('description', 'Uploaded from frontend');

    try {
      const dataset = await api.uploadDataset(formData);
      console.log('Uploaded:', dataset);
      alert('Dataset uploaded successfully!');
    } catch (err: any) {
      alert('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Dataset name"
        required
      />
      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        required
      />
      <button type="submit" disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload Dataset'}
      </button>
    </form>
  );
}
```

### 3. Forecasts List (`app/forecasts/page.tsx`)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

export default function ForecastsPage() {
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadForecasts();
  }, []);

  const loadForecasts = async () => {
    try {
      const data = await api.getForecasts();
      setForecasts(data.results || data);
    } catch (err) {
      console.error('Failed to load forecasts:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Forecasts</h1>
      <ul>
        {forecasts.map((forecast: any) => (
          <li key={forecast.id}>
            {forecast.disease} - {forecast.region}: {forecast.predicted_cases} cases
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 4. Protected Route (`components/protected-route.tsx`)

Update your existing protected route to use the API:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const userData = await api.getProfile();
      setUser(userData);
    } catch (err) {
      router.push('/auth/login');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return user ? <>{children}</> : null;
}
```

## 🔐 Authentication Flow

### Complete Flow

```
1. User fills login form
   ↓
2. Frontend calls: api.login(username, password)
   ↓
3. Backend validates credentials
   ↓
4. Backend returns JWT tokens
   ↓
5. Frontend stores tokens in localStorage
   ↓
6. Future requests include token in Authorization header
   ↓
7. Backend validates token and returns data
```

### Token Storage

```typescript
// After login
localStorage.setItem('access_token', token);

// For requests
const token = localStorage.getItem('access_token');
headers: {
  'Authorization': `Bearer ${token}`
}

// On logout
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

## 🎯 Testing the Connection

### Step 1: Start Backend
```bash
cd d:/Github/MSDP-backend
python manage.py runserver
```

### Step 2: Start Frontend
```bash
cd d:/Github/MSDP
pnpm dev
```

### Step 3: Test Login
1. Go to http://localhost:3000/auth/login
2. Enter credentials
3. Check browser console for response
4. Check Application → Local Storage for tokens

### Step 4: Test Protected Endpoint
1. Try accessing a protected page
2. Should see user data from backend
3. Check Network tab to see API calls

## 🐛 Troubleshooting

### CORS Errors

**Error:** "No 'Access-Control-Allow-Origin' header"

**Solution:**
```python
# In backend settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Add your frontend URL
]
CORS_ALLOW_CREDENTIALS = True
```

### 401 Unauthorized

**Error:** "Authentication credentials were not provided"

**Solutions:**
1. Check token is in localStorage
2. Check Authorization header is set
3. Check token hasn't expired
4. Try logging in again

### Network Error

**Error:** "Failed to fetch"

**Solutions:**
1. Check backend is running on port 8000
2. Check NEXT_PUBLIC_API_URL is correct
3. Check firewall isn't blocking requests

## 📊 API Response Formats

### Success Response
```json
{
  "id": 1,
  "name": "Dataset Name",
  "status": "VALID",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Error Response
```json
{
  "error": "Invalid credentials",
  "detail": "Specific error message"
}
```

### List Response (Paginated)
```json
{
  "count": 100,
  "next": "http://api.example.com/api/datasets/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "name": "Dataset 1" },
    { "id": 2, "name": "Dataset 2" }
  ]
}
```

## 🔄 State Management (Optional)

### Using React Context

```typescript
// lib/auth-context.tsx
'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { api } from './api';

const AuthContext = createContext<any>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await api.getProfile();
      setUser(userData);
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    const userData = await api.login(username, password);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

## 📝 Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] CORS configured in backend
- [ ] API_BASE_URL set in frontend
- [ ] API client created (`lib/api.ts`)
- [ ] Login page implemented
- [ ] Protected routes working
- [ ] Tokens stored in localStorage
- [ ] Network requests visible in DevTools

## 🎉 You're Connected!

Your Next.js frontend can now:
- ✅ Authenticate users (login/register)
- ✅ Upload datasets
- ✅ View forecasts
- ✅ Generate reports
- ✅ Download files
- ✅ Handle protected routes

**Next Steps:**
1. Build out your UI components
2. Add error handling
3. Implement loading states
4. Add form validation
5. Deploy both frontend and backend
