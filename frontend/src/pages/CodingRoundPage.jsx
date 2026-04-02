import { useCallback, useEffect, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import axios from 'axios';
import { useParams } from 'react-router-dom';

export default function CodingRoundPage() {
  const { examId, problemId } = useParams();
  const editorRef = useRef(null);
  const isMountedRef = useRef(true);
  const pollControllerRef = useRef(null);
  const [problem, setProblem] = useState(null);
  const [code, setCode] = useState('');
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [testResults, setTestResults] = useState([]);

  const loadProblem = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(
        `/api/v1/coding/problems/${examId}/${problemId}`
      );
      if (!isMountedRef.current) {
        return;
      }
      setProblem(response.data);
      setCode(response.data.starter_code || '// Write your Java code here\npublic class Main {\n    public static void main(String[] args) {\n        // Your code\n    }\n}');
    } catch (error) {
      if (!isMountedRef.current) {
        return;
      }
      console.error('Failed to load problem:', error);
      setError(error?.message || 'Failed to load problem');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [examId, problemId]);

  useEffect(() => {
    loadProblem();
  }, [loadProblem]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (pollControllerRef.current) {
        pollControllerRef.current.abort();
      }
    };
  }, []);

  const handleSubmit = async () => {
    if (!code.trim()) {
      alert('Please write some code');
      return;
    }

    setLoading(true);
    try {
      const submitResponse = await axios.post(
        `/api/v1/coding/submit/${problemId}`,
        { code }
      );
      const submissionId = submitResponse.data.submission_id;
      if (!isMountedRef.current) {
        return;
      }
      setSubmission(submitResponse.data);

      // Poll for evaluation result
      if (pollControllerRef.current) {
        pollControllerRef.current.abort();
      }
      const pollController = new AbortController();
      pollControllerRef.current = pollController;

      let evaluated = false;
      for (let i = 0; i < 30; i++) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        if (!isMountedRef.current || pollController.signal.aborted) {
          return;
        }

        const statusResponse = await axios.get(
          `/api/v1/coding/submissions/${submissionId}`,
          { signal: pollController.signal }
        );

        if (!isMountedRef.current || pollController.signal.aborted) {
          return;
        }
        
        if (statusResponse.data.status !== 'pending') {
          setSubmission(statusResponse.data);
          setTestResults(statusResponse.data.test_results || []);
          evaluated = true;
          break;
        }
      }

      if (!evaluated) {
        alert('Evaluation timeout - check status later');
      }
    } catch (error) {
      if (!isMountedRef.current) {
        return;
      }
      console.error('Submission failed:', error);
      alert('Failed to submit code');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  if (error) {
    return (
      <div className="p-8 text-white">
        <h2 className="text-xl font-semibold mb-2">Failed to load problem</h2>
        <p className="text-gray-300 mb-4">{error}</p>
        <button
          onClick={loadProblem}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  if (loading || !problem) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Problem Panel */}
      <div className="w-1/2 overflow-y-auto p-6 border-r border-gray-700">
        <h1 className="text-3xl font-bold mb-2">{problem.title}</h1>
        <div className="mb-4">
          <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${
            problem.difficulty === 'easy' ? 'bg-green-600' :
            problem.difficulty === 'medium' ? 'bg-yellow-600' :
            'bg-red-600'
          }`}>
            {(problem.difficulty || 'unknown').toUpperCase()}
          </span>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Problem Description</h3>
          <p className="text-gray-300 whitespace-pre-wrap">{problem.description}</p>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Constraints</h3>
          <ul className="text-sm text-gray-300 space-y-1">
            <li>• Time Limit: {problem.time_limit_seconds} seconds</li>
            <li>• Memory Limit: {problem.memory_limit_mb} MB</li>
          </ul>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Sample Input/Output</h3>
          <div className="space-y-4">
            {(problem.visible_test_cases || []).map((test, idx) => (
              <div key={idx} className="bg-gray-800 p-3 rounded">
                <p className="text-sm font-semibold text-gray-300 mb-1">Test Case {idx + 1}</p>
                <p className="text-xs text-gray-400 mb-2">Input:</p>
                <pre className="bg-gray-900 p-2 rounded text-xs mb-2 overflow-x-auto">{test.input}</pre>
                <p className="text-xs text-gray-400 mb-2">Expected Output:</p>
                <pre className="bg-gray-900 p-2 rounded text-xs overflow-x-auto">{test.expected}</pre>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Editor Panel */}
      <div className="w-1/2 flex flex-col bg-gray-800">
        {/* Editor */}
        <div className="flex-1">
          <Editor
            ref={editorRef}
            height="100%"
            defaultLanguage="java"
            theme="vs-dark"
            value={code}
            onChange={(value) => setCode(value || '')}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              automaticLayout: true,
            }}
          />
        </div>

        {/* Controls */}
        <div className="p-4 border-t border-gray-700 space-y-2">
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-2 px-4 rounded transition"
          >
            {loading ? 'Evaluating...' : 'Submit Code'}
          </button>
        </div>

        {/* Results */}
        {submission && (
          <div className="p-4 border-t border-gray-700 bg-gray-900 max-h-56 overflow-y-auto">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span>Status:</span>
                <span className={`font-semibold ${
                  submission.status === 'accepted' ? 'text-green-400' :
                  submission.status === 'wrong_answer' ? 'text-red-400' :
                  submission.status === 'compile_error' ? 'text-red-500' :
                  'text-yellow-400'
                }`}>
                  {submission.status.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Score:</span>
                <span className="font-semibold">{submission.score}/100</span>
              </div>
              <div className="flex justify-between text-sm text-gray-300">
                <span>Tests:</span>
                <span>{submission.passed_visible}/{submission.total_visible} visible, {submission.passed_hidden}/{submission.total_hidden} hidden</span>
              </div>
              <div className="flex justify-between text-sm text-gray-300">
                <span>Time:</span>
                <span>{submission.execution_time_ms}ms</span>
              </div>
              {submission.error && (
                <div className="text-red-400 text-sm mt-2">
                  <p className="font-semibold">Error:</p>
                  <pre className="text-xs bg-gray-800 p-2 rounded overflow-x-auto mt-1">{submission.error}</pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
