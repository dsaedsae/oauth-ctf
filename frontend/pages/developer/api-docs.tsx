import { useState } from 'react';
import { Code, Play, Lock, CheckCircle } from 'lucide-react';

interface ApiEndpoint {
  method: string;
  path: string;
  title: string;
  description: string;
  stage: number;
  vulnerability?: string;
  example: any;
  hint?: string;
}

const API_ENDPOINTS: ApiEndpoint[] = [
  {
    method: 'POST',
    path: '/auth/register',
    title: 'OAuth Client Registration',
    description: 'Register a new OAuth application with dynamic client registration',
    stage: 1,
    vulnerability: 'SSRF via logo_uri parameter - no URL validation',
    hint: 'Try accessing internal metadata services like http://169.254.169.254/latest/meta-data/',
    example: {
      client_name: 'My App',
      logo_uri: 'http://169.254.169.254/latest/meta-data/instance-id',
      redirect_uris: ['http://localhost:3000/callback']
    }
  },
  {
    method: 'POST',
    path: '/token/exchange',
    title: 'Authorization Code Exchange',
    description: 'Exchange authorization code for access tokens',
    stage: 3,
    vulnerability: 'PKCE downgrade attack - accepts plain method for S256 challenges',
    hint: 'Use stolen auth code with code_verifier="test" and code_challenge_method="plain"',
    example: {
      client_id: 'your_client_id',
      client_secret: 'your_client_secret',
      code: 'stolen_auth_code',
      code_verifier: 'test',
      code_challenge_method: 'plain'
    }
  },
  {
    method: 'POST',
    path: '/graphql',
    title: 'GraphQL API',
    description: 'Query user data and discover available scopes',
    stage: 4,
    vulnerability: 'Introspection enabled - reveals admin schema and scopes',
    hint: 'Send introspection query to discover ADMIN_SECRETS scope',
    example: {
      query: `{
        __schema {
          types {
            name
            fields {
              name
              type { name }
            }
          }
        }
      }`
    }
  },
  {
    method: 'POST',
    path: '/token/refresh',
    title: 'Token Refresh',
    description: 'Refresh access tokens and escalate scopes',
    stage: 5,
    vulnerability: 'Scope escalation - no validation of requested scopes',
    hint: 'Use refresh token to request ADMIN_SECRETS scope',
    example: {
      refresh_token: 'your_refresh_token',
      scope: 'ADMIN_SECRETS'
    }
  }
];

export default function ApiDocs() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(null);
  const [testResults, setTestResults] = useState<any>(null);

  const testEndpoint = async (endpoint: ApiEndpoint) => {
    try {
      const response = await fetch(`http://localhost:5000${endpoint.path}`, {
        method: endpoint.method,
        headers: {
          'Content-Type': 'application/json',
          ...(endpoint.stage >= 4 ? { 'Authorization': 'Bearer your_access_token' } : {})
        },
        body: JSON.stringify(endpoint.example)
      });

      const result = await response.json();
      setTestResults({
        status: response.status,
        data: result
      });
    } catch (error) {
      setTestResults({
        error: error.message
      });
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">API Documentation</h1>
              <p className="mt-2 text-gray-600">TechCorp Connect OAuth 2.0 API Reference</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                <Lock className="w-4 h-4 mr-1" />
                OAuth 2.0
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Endpoints List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold">API Endpoints</h2>
                <p className="text-sm text-gray-600 mt-1">Click to view details and test</p>
              </div>
              <div className="divide-y">
                {API_ENDPOINTS.map((endpoint, index) => (
                  <div
                    key={index}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedEndpoint === endpoint ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                    }`}
                    onClick={() => setSelectedEndpoint(endpoint)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 text-xs font-mono rounded ${
                            endpoint.method === 'POST' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {endpoint.method}
                          </span>
                          <span className="text-sm font-medium">{endpoint.title}</span>
                        </div>
                        <div className="mt-1 text-xs text-gray-500 font-mono">
                          {endpoint.path}
                        </div>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
                          Stage {endpoint.stage}
                        </span>
                        {endpoint.vulnerability && (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700">
                            VULN
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Endpoint Details */}
          <div className="lg:col-span-2">
            {selectedEndpoint ? (
              <div className="space-y-6">
                {/* Endpoint Info */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="flex items-center space-x-3">
                        <span className={`px-3 py-1 text-sm font-mono rounded ${
                          selectedEndpoint.method === 'POST' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {selectedEndpoint.method}
                        </span>
                        <span className="text-lg font-mono">{selectedEndpoint.path}</span>
                      </div>
                      <h3 className="text-xl font-semibold mt-2">{selectedEndpoint.title}</h3>
                    </div>
                    <button
                      onClick={() => testEndpoint(selectedEndpoint)}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Test Endpoint
                    </button>
                  </div>

                  <p className="text-gray-600 mb-4">{selectedEndpoint.description}</p>

                  {selectedEndpoint.vulnerability && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-red-600 font-semibold">⚠️ Security Vulnerability</span>
                      </div>
                      <p className="text-red-800 text-sm">{selectedEndpoint.vulnerability}</p>
                    </div>
                  )}

                  {selectedEndpoint.hint && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-blue-600 font-semibold">💡 Hint</span>
                      </div>
                      <p className="text-blue-800 text-sm">{selectedEndpoint.hint}</p>
                    </div>
                  )}
                </div>

                {/* Request Example */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <h4 className="text-lg font-semibold mb-4 flex items-center">
                    <Code className="w-5 h-5 mr-2" />
                    Request Example
                  </h4>
                  <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                    <div className="text-green-400 mb-2">
                      {selectedEndpoint.method} {selectedEndpoint.path}
                    </div>
                    <div className="text-blue-400 mb-2">
                      Content-Type: application/json
                      {selectedEndpoint.stage >= 4 && (
                        <><br />Authorization: Bearer your_access_token</>
                      )}
                    </div>
                    <div className="text-white">
                      {JSON.stringify(selectedEndpoint.example, null, 2)}
                    </div>
                  </div>
                </div>

                {/* Test Results */}
                {testResults && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center">
                      <CheckCircle className="w-5 h-5 mr-2" />
                      Test Results
                    </h4>
                    <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                      {testResults.error ? (
                        <div className="text-red-400">Error: {testResults.error}</div>
                      ) : (
                        <>
                          <div className="text-green-400 mb-2">
                            Status: {testResults.status}
                          </div>
                          <div className="text-white">
                            {JSON.stringify(testResults.data, null, 2)}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                <Code className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Select an API Endpoint</h3>
                <p className="text-gray-600">Choose an endpoint from the list to view documentation and test it</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}