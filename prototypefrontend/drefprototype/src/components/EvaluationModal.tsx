import React, { useState } from "react";
import { X, AlertCircle, CheckCircle, Lightbulb } from "lucide-react";

interface EvaluationResult {
  status?: string;
  evaluation?: {
    assessment?: string;
    status?: string;
    issues?: Array<{ field: string; issue: string }>;
    strengths?: string[];
  };
  raw_response?: string;
  error?: string;
}

interface EvaluationModalProps {
  isOpen: boolean;
  result: EvaluationResult | null;
  isLoading: boolean;
  onClose: () => void;
  formData?: Record<string, any>;
}

interface Suggestion {
  title: string;
  improvement: string;
  correction: string;
}

const EvaluationModal: React.FC<EvaluationModalProps> = ({
  isOpen,
  result,
  isLoading,
  onClose,
  formData = {},
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  const parseSuggestions = (text: string): Suggestion[] => {
    const suggestions: Suggestion[] = [];
    
    // Remove ### and clean up text
    let cleanText = text.replace(/#{1,}/g, '').trim();
    
    // Split by numbered items (e.g., "1. ", "2. ", etc.)
    const items = cleanText.split(/\d+\.\s+/).filter(item => item.trim());
    
    items.forEach(item => {
      const lines = item.split('\n').map(l => l.trim()).filter(l => l);
      if (lines.length >= 1) {
        // Extract title from various formats
        let title = '';
        let improvement = '';
        let correction = '';
        
        // Try to find title (text before colon or ** markers)
        const titleMatch = lines[0].match(/\*\*([^*]+)\*\*/) || lines[0].match(/^([^:]+?):/);
        title = titleMatch ? titleMatch[1].trim() : lines[0].split(':')[0].trim();
        
        // Remove title from full text for better parsing
        const remainingText = item.replace(title, '').trim();
        
        // Extract improvement explanation
        const improvementMatch = remainingText.match(/(?:issue|problem|missing|needs|ensure|provide|include|fix):\s*([^.!?-]+)/i);
        if (improvementMatch) {
          improvement = improvementMatch[1].trim();
        } else if (lines[1]) {
          improvement = lines[1].replace(/^\*\*|\*\*$/g, '').trim();
        }
        
        // Limit improvement to ~80 chars
        if (improvement.length > 80) {
          improvement = improvement.substring(0, 77) + '...';
        }
        
        // Extract correction (what to write)
        const correctionMatch = remainingText.match(/(?:correct|write|add|include|example|should be):\s*"?([^"]+)"?(?:\.|$)/i);
        if (correctionMatch) {
          correction = correctionMatch[1].trim().replace(/[.,;:!?]+$/, '');
        }
        
        // Limit correction to ~150 chars for display
        if (correction.length > 150) {
          correction = correction.substring(0, 147) + '...';
        }
        
        if (title && (improvement || correction)) {
          suggestions.push({
            title: title.replace(/[.,;:!?]+$/, ''),
            improvement,
            correction
          });
        }
      }
    });
    
    return suggestions;
  };

  const getStatus = () => {
    const status = result?.evaluation?.status || result?.status || "";
    return status.toLowerCase();
  };

  const fetchSuggestions = async () => {
    setLoadingSuggestions(true);
    setShowSuggestions(false);
    setSuggestions(null);
    try {
      const response = await fetch(
        "http://localhost:8000/api/v2/dref-evaluation/ai-suggestions/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ form_data: formData }),
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const suggestionsText = data.suggestions || data.raw_response || JSON.stringify(data, null, 2);
      const parsedSuggestions = parseSuggestions(suggestionsText);
      setSuggestions(parsedSuggestions.length > 0 ? parsedSuggestions : [{ title: "Suggestions", improvement: "", correction: suggestionsText }]);
      setShowSuggestions(true);
    } catch (error) {
      setSuggestions([{ title: "Error", improvement: "Failed to fetch suggestions", correction: (error as Error).message }]);
      setShowSuggestions(true);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="relative w-full max-w-2xl max-h-96 bg-white rounded-lg shadow-lg overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold">Evaluation Results</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Evaluating...</p>
              </div>
            </div>
          ) : result?.error ? (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
              <h3 className="text-lg font-semibold text-red-800 mb-2">Error</h3>
              <p className="text-red-700">{result.error}</p>
            </div>
          ) : result ? (
            <div className="space-y-6">
              {/* Status Badge */}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Status
                </h3>
                <div className="flex items-center gap-3">
                  {getStatus() === "approved" ? (
                    <>
                      <CheckCircle className="text-green-600" size={28} />
                      <span className="px-4 py-2 rounded-full font-semibold text-white bg-green-600">
                        Approved
                      </span>
                    </>
                  ) : getStatus().includes("revision") || getStatus().includes("needs") ? (
                    <>
                      <AlertCircle className="text-yellow-600" size={28} />
                      <span className="px-4 py-2 rounded-full font-semibold text-white bg-yellow-600">
                        Needs Revision
                      </span>
                    </>
                  ) : (
                    <span className="px-4 py-2 rounded-full font-semibold text-white bg-blue-600">
                      {getStatus() || "Complete"}
                    </span>
                  )}
                </div>
              </div>

              {/* Assessment */}
              {result.evaluation?.assessment ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Assessment
                  </h3>
                  <div className="bg-blue-50 p-4 rounded border border-blue-200 text-gray-700 text-sm leading-relaxed">
                    {result.evaluation.assessment}
                  </div>
                </div>
              ) : null}

              {/* Issues */}
              {result.evaluation?.issues && result.evaluation.issues.length > 0 ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Issues Found
                  </h3>
                  <div className="space-y-2">
                    {result.evaluation.issues.map((issue, idx) => (
                      <div key={idx} className="bg-red-50 p-3 rounded border border-red-200">
                        <div className="font-semibold text-red-800">{issue.field}</div>
                        <div className="text-red-700 text-sm">{issue.issue}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Strengths - only show if there are actual substantive strengths */}
              {result.evaluation?.strengths && result.evaluation.strengths.length > 0 && result.evaluation.strengths.some(s => s && typeof s === 'string' && !s.toLowerCase().includes('none') && !s.toLowerCase().includes('no substantive') && s.trim().length > 0) ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    Strengths
                  </h3>
                  <div className="space-y-2">
                    {result.evaluation.strengths
                      .filter(s => s && typeof s === 'string' && !s.toLowerCase().includes('none') && !s.toLowerCase().includes('no substantive') && s.trim().length > 0)
                      .map((strength, idx) => (
                      <div key={idx} className="bg-green-50 p-3 rounded border border-green-200 text-green-800 text-sm">
                        ✓ {strength}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Suggestions Section */}
              {showSuggestions && suggestions ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Lightbulb size={18} className="text-amber-600 flex-shrink-0" />
                    AI Suggestions
                  </h3>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-2">
                    {suggestions.map((suggestion, idx) => (
                      <div key={idx} className="bg-amber-50 border border-amber-200 rounded p-3">
                        {/* Title */}
                        <div className="font-semibold text-amber-900 text-sm break-words">
                          {suggestion.title}
                        </div>
                        
                        {/* Improvement explanation */}
                        {suggestion.improvement && (
                          <div className="text-xs text-amber-800 mt-1 break-words">
                            {suggestion.improvement}
                          </div>
                        )}
                        
                        {/* Correction - what to write */}
                        {suggestion.correction && (
                          <div className="bg-white border border-amber-100 rounded px-2 py-1 mt-2 text-xs font-mono text-gray-700 break-words overflow-hidden">
                            {suggestion.correction}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-6 border-t bg-gray-50">
          {result && !result?.error && (
            <button
              onClick={fetchSuggestions}
              disabled={loadingSuggestions}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Lightbulb size={18} />
              {loadingSuggestions ? "Getting Suggestions..." : "Get AI Suggestions"}
            </button>
          )}
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default EvaluationModal;
