import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { agentService } from "@/services/agent";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { TripVisualization } from "@/components/TripVisualization";
import {
  Plane,
  MapPin,
  Calendar,
  DollarSign,
  Users,
  Plus,
  X,
} from "lucide-react";

// Hardcoded backend URL - same as in agent.ts
const AGENT_BASE_URL =
  "https://financial-service-agent-609099553774.us-central1.run.app";

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
  formattedText?: string;
  timestamp: Date;
}

interface Trip {
  id: string;
  name: string;
  destination: string;
  startDate?: string;
  endDate?: string;
  budget?: number;
}

const TravelPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "agent",
      text: "Hello! I'm your Travel Finance Advisor. I can help you budget for trips, find the best travel rewards, manage foreign currency exchanges, and plan financially smart vacations. Where are you thinking of traveling?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [contextId, setContextId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Trip planning states
  const [currentTrip, setCurrentTrip] = useState<Trip | null>(null);
  const [showVisualization, setShowVisualization] = useState(false);
  const [showCreateTrip, setShowCreateTrip] = useState(false);
  const [newTripName, setNewTripName] = useState("");
  const [newTripDestination, setNewTripDestination] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [tripMembers, setTripMembers] = useState<string[]>([]);

  // Helper function to format response text with bold and newlines
  const formatResponseText = (text: string) => {
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    formattedText = formattedText.replace(/\n/g, "<br>");
    return formattedText;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await agentService.sendTravelQuery(
        inputValue,
        contextId
      );
      const responseText = agentService.extractResponseText(response);
      const sessionId = agentService.getSessionId(response);

      if (sessionId) {
        setContextId(sessionId);
      }

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: responseText,
        formattedText: formatResponseText(responseText),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: "Sorry, I encountered an error. Please try again. Make sure you are logged in.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const createTrip = () => {
    if (!newTripName || !newTripDestination) return;

    const trip: Trip = {
      id: `trip-${Date.now()}`,
      name: newTripName,
      destination: newTripDestination,
    };

    setCurrentTrip(trip);
    setShowCreateTrip(false);
    setNewTripName("");
    setNewTripDestination("");
  };

  const inviteFriend = async () => {
    if (!inviteEmail || !currentTrip) return;

    try {
      const formData = new FormData();
      formData.append("email", inviteEmail);
      formData.append("inviter_id", currentUser?.uid || "");

      const response = await fetch(
        `${AGENT_BASE_URL}/api/trips/${currentTrip.id}/invite`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (response.ok) {
        setTripMembers([...tripMembers, inviteEmail]);
        setInviteEmail("");
      }
    } catch (error) {
      console.error("Failed to send invitation:", error);
    }
  };

  return (
    <div className="container mx-auto py-6 px-4 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground flex items-center gap-2">
          <Plane className="h-8 w-8" />
          Travel Finance Advisor
        </h1>
        <p className="text-muted-foreground mt-2">
          Plan your trips smartly with budgeting tips, rewards optimization, and
          travel financial advice
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Travel Tools & Info - Left Column */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Current Trip
              </CardTitle>
            </CardHeader>
            <CardContent>
              {currentTrip ? (
                <div className="space-y-2">
                  <p className="font-medium">{currentTrip.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {currentTrip.destination}
                  </p>
                  <Button
                    variant="outline"
                    className="w-full mt-2"
                    onClick={() => setShowVisualization(!showVisualization)}
                  >
                    {showVisualization ? "Hide" : "Show"} Visualization
                  </Button>
                </div>
              ) : (
                <>
                  <p className="text-sm text-muted-foreground mb-3">
                    No active trip planned
                  </p>
                  <Button
                    className="w-full"
                    onClick={() => setShowCreateTrip(true)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Plan New Trip
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {showCreateTrip && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Create Trip</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="Trip name..."
                  value={newTripName}
                  onChange={(e) => setNewTripName(e.target.value)}
                />
                <Input
                  placeholder="Destination..."
                  value={newTripDestination}
                  onChange={(e) => setNewTripDestination(e.target.value)}
                />
                <div className="flex gap-2">
                  <Button onClick={createTrip} className="flex-1">
                    Create
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateTrip(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {currentTrip && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Trip Members
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-3">
                  {tripMembers.map((email, index) => (
                    <div key={index} className="text-sm">
                      {email}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Email to invite..."
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="flex-1"
                  />
                  <Button onClick={inviteFriend} size="sm">
                    Invite
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Travel Budget
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Vacation Fund</span>
                  <span className="font-medium">$3,500</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Monthly Savings</span>
                  <span className="font-medium">$300</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Travel Rewards</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <p className="font-medium">Credit Card Points</p>
                  <p className="text-sm text-muted-foreground">
                    125,000 points
                  </p>
                </div>
                <div>
                  <p className="font-medium">Airline Miles</p>
                  <p className="text-sm text-muted-foreground">45,000 miles</p>
                </div>
                <Button variant="outline" className="w-full mt-2">
                  Optimize Rewards
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Area - Right Columns */}
        <div className="lg:col-span-3 space-y-6">
          {/* Visualization Section */}
          {showVisualization && currentTrip && (
            <TripVisualization
              tripId={currentTrip.id}
              userId={currentUser?.uid || "guest"}
            />
          )}

          {/* Chat Interface */}
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle>Chat with Your Travel Finance Advisor</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.sender === "user"
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md p-3 rounded-lg ${
                        message.sender === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {message.sender === "agent" && message.formattedText ? (
                        <div
                          className="text-sm"
                          dangerouslySetInnerHTML={{
                            __html: message.formattedText,
                          }}
                        />
                      ) : (
                        <p className="text-sm">{message.text}</p>
                      )}
                      <p className="text-xs mt-1 opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted text-muted-foreground p-3 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-current rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-current rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </CardContent>
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                  placeholder="Ask about travel budgets, rewards, or destination costs..."
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim()}
                >
                  Send
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TravelPage;
