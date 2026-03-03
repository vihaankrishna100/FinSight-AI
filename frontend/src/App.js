import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { getApiUrl } from './config';

function App() {
  const [company, setCompany] = useState('');
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stockGraph, setStockGraph] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const responseRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    
    if (!company.trim() || !question.trim()) {
      setError('Please fill in both company name and question!');
      return;
    }


    setLoading(true);
    setError('');
    setResponse('Initializing analysis...\n');
    setStockGraph(null);

    // Fetch stock graph in parallel
    const fetchGraph = async () => {
      try {
        setGraphLoading(true);
        const ticker = company.trim().toUpperCase();
        
        const chartResponse = await fetch(`${getApiUrl()}/stock/graph`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker, period: '3mo', graph_type: 'price' })
        });
        if (chartResponse.ok) {
          const chartData = await chartResponse.json();
          setStockGraph(chartData.image);
        }
      } catch (err) {
        console.error('Error fetching graph:', err);
      } finally {
        setGraphLoading(false);
      }
    };
    fetchGraph();

    try {
      const response = await fetch(`${getApiUrl()}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company: company.trim(),
          question: question.trim()
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An error occurred');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.status === 'progress') {
                setResponse(prev => prev + data.message + '\n\n');
                // Auto-scroll to bottom
                setTimeout(() => {
                  if (responseRef.current) {
                    responseRef.current.scrollTop = responseRef.current.scrollHeight;
                  }
                }, 100);
              } else if (data.status === 'complete') {
                setResponse(prev => prev + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' + data.response);
                setLoading(false);
                // Auto-scroll to bottom
                setTimeout(() => {
                  if (responseRef.current) {
                    responseRef.current.scrollTop = responseRef.current.scrollHeight;
                  }


                }, 100);

                
              } else if (data.status === 'error') {
                setError(data.message);
                setLoading(false);
                setResponse('');
              }
            } catch (err) {
              console.error('Error parsing SSE data:', err);
            }
          }
        }
      }
    } catch (err) {
      if (err.message) {
        setError(err.message);
      } else if (err.request || err.code === 'ERR_NETWORK') {
        setError('Unable to connect to the server. Please make sure the backend is running.');
      } else {
        setError('An unexpected error occurred.');
      }
      setResponse('');
      setLoading(false);
    }
  };





  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            Finsight AI
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Get real-time financial insights and investment analysis based on live news updates
          </p>
        </div>

        {/* Main Form */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="company" className="block text-lg font-semibold text-gray-700 mb-3">
                  Stock Ticker
                </label>
                <input
                  type="text"
                  id="company"
                  value={company}
                  onChange={(e) => setCompany(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, TSLA, MSFT, GOOGL"
                  className="w-full px-4 py-3 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors"
                  disabled={loading}
                />
              </div>



              <div>
                <label htmlFor="question" className="block text-lg font-semibold text-gray-700 mb-3">
                  Your Investment Question
                </label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g., What are the current investment risks and opportunities for this company?"
                  rows="4"
                  className="w-full px-4 py-3 text-lg border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors resize-none"
                  disabled={loading}
                />
              </div>

              <button
//fix button
                type="submit"

                disabled={loading}
                className={`w-full py-4 px-6 text-xl font-bold text-white rounded-xl transition-all duration-200 ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transform hover:scale-105'
                }`}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mr-3"></div>
                    Analyzing...
                  </div>
                ) : (
                  'Get Financial Analysis'
                )}
              </button>
            </form>
          </div>

          {/* Error Display */}

          {error && (
            <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 rounded-lg">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}



          {/* Response Display */}

          {(response || loading) && (
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                {loading ? 'Analyzing...' : 'Financial Analysis'}
              </h2>
              <div ref={responseRef} className="bg-gray-50 rounded-xl p-6 max-h-96 overflow-y-auto">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap font-mono text-sm">{response || 'Initializing...'}</p>
              </div>
            </div>
          )}

          {/* Stock Graph Display */}

          {(stockGraph || graphLoading) && (
            <div className="bg-white rounded-2xl shadow-2xl p-8 mt-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Stock Price Chart</h2>
              {graphLoading ? (
                <div className="flex items-center justify-center p-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Loading chart...</span>
                </div>
              ) : (
                <img src={stockGraph} alt="Stock price chart" className="w-full rounded-lg" />
              )}
            </div>
          )}

          {/* Info Section */}
          <div className="mt-12 text-center">
            <div className="bg-blue-50 rounded-2xl p-6">
              <h3 className="text-xl font-semibold text-blue-800 mb-3">How it works</h3>
              <p className="text-blue-700">

                  Our finetuned LM allows you to search for a stock and recive research-grade information from real-time news-sources.
                  Start by typing out the company of your choice and the question that you have about it!        
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 