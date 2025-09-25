import { auth } from "./firebase";

// Production-ready configuration
const AGENT_BASE_URL = "https://financial-service-agent-609099553774.us-central1.run.app";

// For local development, uncomment the line below and comment out the production URL above
// const AGENT_BASE_URL = "http://localhost:8001";

export interface ChatRequest {
  message: string;
  user_id?: string;
  session_id?: string;
  skill?: "chat" | "backend_services";
}

// Interface for graph/image artifacts returned by the ML model
export interface Artifact {
  type: string;           // "image" for graphs/charts
  name: string;           // filename like "spending_trends.png"
  data: string;           // base64 encoded image data with data URL prefix
  mime_type: string;      // "image/png", "image/jpg", etc.
}

export interface ChatResponse {
  response: string;
  session_id: string;
  skill_used: string;
  artifacts?: Artifact[];  // Optional array of graphs/visualizations
}

export const AgentType = {
  DAILY_SPENDING: "daily-spending",
  BIG_PURCHASES: "big-purchases",
  TRAVEL: "travel",
  GENERAL: "general",
} as const;

export type AgentType = (typeof AgentType)[keyof typeof AgentType];

class AgentService {
  private sessionId: string | null = null;

  /**
   * Gets Firebase authentication token for API requests
   * @returns Promise<string | null> - Auth token or null if not authenticated
   */
  private async getAuthToken(): Promise<string | null> {
    const user = auth.currentUser;
    if (!user) return null;
    return user.getIdToken();
  }

  /**
   * Generates a unique session ID for conversation tracking
   * @returns string - Unique session identifier
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sends a message to the specified agent type
   * @param message - User's message/query
   * @param agentType - Type of agent to route to (DAILY_SPENDING, BIG_PURCHASES, etc.)
   * @param sessionId - Optional session ID for conversation continuity
   * @returns Promise<ChatResponse> - Agent response with optional artifacts (graphs/charts)
   */
  async sendMessage(
    message: string,
    agentType: AgentType = AgentType.GENERAL,
    sessionId?: string
  ): Promise<ChatResponse> {
    const token = await this.getAuthToken();

    if (!token) {
      throw new Error("User not authenticated");
    }

    // Use existing session ID or create a new one
    const currentSessionId =
      sessionId || this.sessionId || this.generateSessionId();

    // Store session ID for future use
    if (!this.sessionId) {
      this.sessionId = currentSessionId;
    }

    // Format message based on agent type for better routing
    let formattedMessage = message;
    if (agentType === AgentType.DAILY_SPENDING) {
      formattedMessage = `I need help with daily spending. ${message}`;
    } else if (agentType === AgentType.BIG_PURCHASES) {
      formattedMessage = `I need help with a big purchase. ${message}`;
    } else if (agentType === AgentType.TRAVEL) {
      formattedMessage = `I need help with travel planning. ${message}`;
    }

    const payload: ChatRequest = {
      message: formattedMessage,
      user_id: auth.currentUser?.uid || "user-001",
      session_id: currentSessionId,
      skill: "chat",
    };

    try {
      const response = await fetch(`${AGENT_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Agent API error:", errorText);
        throw new Error(`Agent request failed: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      // Update session ID if provided in response for conversation continuity
      if (data.session_id) {
        this.sessionId = data.session_id;
      }

      return data;
    } catch (error) {
      console.error("Error communicating with agent:", error);
      throw error;
    }
  }

  // ==================== SPECIALIZED AGENT METHODS ====================
  
  /**
   * Sends query to Daily Spending agent for expense tracking and budgeting
   * @param message - User's spending-related query
   * @param sessionId - Optional session ID for conversation continuity
   * @returns Promise<ChatResponse> - Agent response with spending insights
   */
  async sendDailySpendingQuery(
    message: string,
    sessionId?: string
  ): Promise<ChatResponse> {
    return this.sendMessage(message, AgentType.DAILY_SPENDING, sessionId);
  }

  /**
   * Sends query to Big Purchase agent (ML-powered with transaction data analysis)
   * @param message - User's big purchase query
   * @param sessionId - Optional session ID for conversation continuity
   * @returns Promise<ChatResponse> - ML-powered response with data visualizations
   */
  async sendBigPurchaseQuery(
    message: string,
    sessionId?: string
  ): Promise<ChatResponse> {
    return this.sendMessage(message, AgentType.BIG_PURCHASES, sessionId);
  }

  /**
   * Sends query to Travel agent for trip planning and recommendations
   * @param message - User's travel-related query
   * @param sessionId - Optional session ID for conversation continuity
   * @returns Promise<ChatResponse> - Travel recommendations and plans
   */
  async sendTravelQuery(
    message: string,
    sessionId?: string
  ): Promise<ChatResponse> {
    return this.sendMessage(message, AgentType.TRAVEL, sessionId);
  }

  // ==================== RESPONSE PROCESSING UTILITIES ====================

  /**
   * Extracts text content from agent response
   * @param response - Agent response object
   * @returns string - Response text content
   */
  extractResponseText(response: ChatResponse): string {
    return response.response || "No response from agent";
  }
  
  /**
   * Extracts artifacts (graphs/charts) from agent response
   * @param response - Agent response object
   * @returns Artifact[] | undefined - Array of visualizations or undefined if none
   */
  extractArtifacts(response: ChatResponse): Artifact[] | undefined {
    return response.artifacts;
  }

  /**
   * Gets session ID from response or current session
   * @param response - Agent response object
   * @returns string | undefined - Session ID for conversation tracking
   */
  getSessionId(response: ChatResponse): string | undefined {
    return response.session_id || this.sessionId || undefined;
  }

  /**
   * Clears current session (use when starting new conversations)
   */
  clearSession(): void {
    this.sessionId = null;
  }
}

// ==================== SINGLETON EXPORT ====================
/**
 * Singleton instance of AgentService for consistent session management across the app
 * 
 * Usage:
 * - agentService.sendBigPurchaseQuery() - For ML-powered financial analysis with graphs
 * - agentService.sendDailySpendingQuery() - For daily expense tracking
 * - agentService.sendTravelQuery() - For travel planning
 * - agentService.extractArtifacts() - To get graphs/charts from responses
 */
export const agentService = new AgentService();
