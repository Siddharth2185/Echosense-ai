/**
 * API Client for Echosense AI Backend
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = 'http://localhost:8000';

class EchosenseAPI {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async _fetch(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * Upload audio file
   * @param {File} file - Audio file to upload
   * @returns {Promise<Object>} Upload response with call_id
   */
  async uploadAudio(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${this.baseUrl}/api/upload/audio`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Upload Error:', error);
      throw error;
    }
  }

  /**
   * Get processing status for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Processing status
   */
  async getProcessingStatus(callId) {
    return this._fetch(`/api/processing/status/${callId}`);
  }

  /**
   * Get transcript for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Transcript data
   */
  async getTranscript(callId) {
    return this._fetch(`/api/processing/transcript/${callId}`);
  }

  /**
   * Get quality scores for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Quality scores
   */
  async getQualityScore(callId) {
    return this._fetch(`/api/processing/quality/${callId}`);
  }

  /**
   * Get compliance flags for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Compliance flags
   */
  async getComplianceFlags(callId) {
    return this._fetch(`/api/processing/compliance/${callId}`);
  }

  /**
   * Get full report for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Complete call analysis
   */
  async getFullReport(callId) {
    return this._fetch(`/api/processing/full-report/${callId}`);
  }

  /**
   * Get dashboard statistics
   * @param {number} days - Number of days to analyze (default: 7)
   * @returns {Promise<Object>} Dashboard stats
   */
  async getDashboardStats(days = 7) {
    return this._fetch(`/api/analytics/dashboard?days=${days}`);
  }

  /**
   * Get recent calls
   * @param {number} limit - Number of calls to retrieve (default: 10)
   * @returns {Promise<Object>} Recent calls list
   */
  async getRecentCalls(limit = 10) {
    return this._fetch(`/api/analytics/recent-calls?limit=${limit}`);
  }

  /**
   * Get quality trends over time
   * @param {number} days - Number of days (default: 30)
   * @returns {Promise<Object>} Quality trends data
   */
  async getQualityTrends(days = 30) {
    return this._fetch(`/api/analytics/quality-trends?days=${days}`);
  }

  /**
   * Delete a call and all related data
   * @param {string} callId - Call ID to delete
   * @returns {Promise<Object>} Deletion result
   */
  async deleteCall(callId) {
    return this._fetch(`/api/calls/${callId}`, {
      method: 'DELETE'
    });
  }

  /**
   * Force re-process a call (reset + requeue)
   * @param {string} callId - Call ID to reprocess
   * @returns {Promise<Object>} Reprocess result
   */
  async reprocessCall(callId) {
    return this._fetch(`/api/processing/reprocess/${callId}`, {
      method: 'POST'
    });
  }

  /**
   * Add a review / training comment to a call
   * @param {string} callId - Call ID
   * @param {Object} data - { reviewer_name, category, comment, score_override }
   * @returns {Promise<Object>} Created review comment
   */
  async addReviewComment(callId, data) {
    return this._fetch(`/api/processing/review/${callId}`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * Get all review / training comments for a call
   * @param {string} callId - Call ID
   * @returns {Promise<Object>} Review comments
   */
  async getReviewComments(callId) {
    return this._fetch(`/api/processing/reviews/${callId}`);
  }

  /**
   * Get compliance summary
   * @param {number} days - Number of days (default: 7)
   * @returns {Promise<Object>} Compliance summary
   */
  async getComplianceSummary(days = 7) {
    return this._fetch(`/api/analytics/compliance-summary?days=${days}`);
  }
}

// Create singleton instance
const api = new EchosenseAPI();

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { EchosenseAPI, api };
}
