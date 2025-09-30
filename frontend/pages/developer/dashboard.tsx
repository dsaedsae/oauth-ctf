import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Plus,
  Key,
  Activity,
  Users,
  AlertCircle,
  ExternalLink,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react';

interface Application {
  id: string;
  name: string;
  client_id: string;
  logo_uri: string;
  redirect_uris: string[];
  created_at: string;
  last_used: string;
  requests_count: number;
}

export default function DeveloperDashboard() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [newApp, setNewApp] = useState({
    name: '',
    logo_uri: '',
    redirect_uris: ['']
  });
  const [apiUsage, setApiUsage] = useState({
    current_month: 125432,
    limit: 1000000,
    percentage: 12.5
  });

  // Simulate loading applications
  useEffect(() => {
    // This would normally fetch from API
    setApplications([
      {
        id: '1',
        name: 'Mobile App',
        client_id: 'mobile_app_client_123',
        logo_uri: 'https://via.placeholder.com/64',
        redirect_uris: ['com.techcorp.mobile://oauth/callback'],
        created_at: '2024-01-15',
        last_used: '2 hours ago',
        requests_count: 45672
      },
      {
        id: '2',
        name: 'Web Dashboard',
        client_id: 'web_dashboard_456',
        logo_uri: 'https://via.placeholder.com/64',
        redirect_uris: ['https://dashboard.techcorp.com/callback'],
        created_at: '2024-02-01',
        last_used: '5 minutes ago',
        requests_count: 78231
      }
    ]);
  }, []);

  const handleRegisterApp = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // 🚨 VULNERABILITY: This will trigger SSRF in Stage 1
      const response = await fetch('/api/oauth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_name: newApp.name,
          logo_uri: newApp.logo_uri, // No validation - SSRF possible
          redirect_uris: newApp.redirect_uris.filter(uri => uri.trim())
        })
      });

      const result = await response.json();

      if (response.ok) {
        // Add new application to list
        const newApplication: Application = {
          id: result.client_id,
          name: newApp.name,
          client_id: result.client_id,
          logo_uri: newApp.logo_uri,
          redirect_uris: newApp.redirect_uris,
          created_at: new Date().toISOString().split('T')[0],
          last_used: 'Never',
          requests_count: 0
        };

        setApplications([...applications, newApplication]);
        setShowRegisterModal(false);
        setNewApp({ name: '', logo_uri: '', redirect_uris: [''] });

        // Show success message
        alert(`Application registered successfully!\nClient ID: ${result.client_id}\nClient Secret: ${result.client_secret}`);
      } else {
        alert('Registration failed: ' + result.error);
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('Registration failed. Please try again.');
    }
  };

  const addRedirectUri = () => {
    setNewApp({
      ...newApp,
      redirect_uris: [...newApp.redirect_uris, '']
    });
  };

  const updateRedirectUri = (index: number, value: string) => {
    const updated = [...newApp.redirect_uris];
    updated[index] = value;
    setNewApp({
      ...newApp,
      redirect_uris: updated
    });
  };

  const removeRedirectUri = (index: number) => {
    if (newApp.redirect_uris.length > 1) {
      const updated = newApp.redirect_uris.filter((_, i) => i !== index);
      setNewApp({
        ...newApp,
        redirect_uris: updated
      });
    }
  };

  return (
    <>
      <Head>
        <title>Developer Dashboard - TechCorp Connect</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link href="/" className="flex items-center">
                  <Key className="h-8 w-8 text-blue-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">TechCorp Connect</span>
                </Link>
                <nav className="ml-10 flex space-x-8">
                  <Link href="/developer/dashboard" className="text-blue-600 border-b-2 border-blue-600 px-1 pb-4 text-sm font-medium">
                    Dashboard
                  </Link>
                  <Link href="/developer/applications" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    Applications
                  </Link>
                  <Link href="/developer/api-keys" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    API Keys
                  </Link>
                  <Link href="/developer/api-docs" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    API Docs
                  </Link>
                  <Link href="/community" className="text-gray-500 hover:text-gray-700 px-1 pb-4 text-sm font-medium">
                    Community
                  </Link>
                </nav>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm">
                  <span className="text-gray-500">Welcome back,</span>
                  <span className="font-medium text-gray-900 ml-1">John Developer</span>
                </div>
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">JD</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">API Requests</p>
                  <p className="text-2xl font-bold text-gray-900">{apiUsage.current_month.toLocaleString()}</p>
                  <p className="text-sm text-gray-500">This month</p>
                </div>
              </div>
              <div className="mt-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Usage</span>
                  <span className="text-gray-900">{apiUsage.percentage}% of limit</span>
                </div>
                <div className="mt-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${apiUsage.percentage}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Users</p>
                  <p className="text-2xl font-bold text-gray-900">2,847</p>
                  <p className="text-sm text-green-600">+12% from last month</p>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center">
                <Key className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Applications</p>
                  <p className="text-2xl font-bold text-gray-900">{applications.length}</p>
                  <p className="text-sm text-gray-500">Registered apps</p>
                </div>
              </div>
            </div>
          </div>

          {/* Applications Section */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">OAuth Applications</h2>
                <button
                  onClick={() => setShowRegisterModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Register New App
                </button>
              </div>
            </div>

            <div className="divide-y divide-gray-200">
              {applications.map((app) => (
                <div key={app.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <img
                        src={app.logo_uri}
                        alt={app.name}
                        className="w-12 h-12 rounded-lg border"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDgiIGhlaWdodD0iNDgiIHZpZXdCb3g9IjAgMCA0OCA0OCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQ4IiBoZWlnaHQ9IjQ4IiByeD0iOCIgZmlsbD0iIzM3NDE1MSIvPgo8L3N2Zz4K';
                        }}
                      />
                      <div className="ml-4">
                        <h3 className="text-sm font-medium text-gray-900">{app.name}</h3>
                        <p className="text-sm text-gray-500">Client ID: {app.client_id}</p>
                        <p className="text-xs text-gray-400">Created {app.created_at} • Last used {app.last_used}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{app.requests_count.toLocaleString()}</p>
                        <p className="text-xs text-gray-500">requests</p>
                      </div>
                      <button className="text-gray-400 hover:text-gray-600">
                        <ExternalLink className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}

              {applications.length === 0 && (
                <div className="px-6 py-12 text-center">
                  <Key className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No applications</h3>
                  <p className="mt-1 text-sm text-gray-500">Get started by registering your first OAuth application.</p>
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Register App Modal */}
        {showRegisterModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Register New Application</h3>

                <form onSubmit={handleRegisterApp} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Application Name
                    </label>
                    <input
                      type="text"
                      required
                      value={newApp.name}
                      onChange={(e) => setNewApp({...newApp, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="My Awesome App"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Logo URI
                      <span className="text-xs text-gray-500 ml-1">(optional - for branding)</span>
                    </label>
                    <input
                      type="url"
                      value={newApp.logo_uri}
                      onChange={(e) => setNewApp({...newApp, logo_uri: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="https://example.com/logo.png"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      💡 Try: http://169.254.169.254/latest/meta-data/ for testing
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Redirect URIs
                    </label>
                    {newApp.redirect_uris.map((uri, index) => (
                      <div key={index} className="flex mb-2">
                        <input
                          type="url"
                          required
                          value={uri}
                          onChange={(e) => updateRedirectUri(index, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          placeholder="https://example.com/oauth/callback"
                        />
                        {newApp.redirect_uris.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeRedirectUri(index)}
                            className="ml-2 px-3 py-2 text-red-600 hover:text-red-800"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={addRedirectUri}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      + Add another redirect URI
                    </button>
                  </div>

                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowRegisterModal(false)}
                      className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Register Application
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}