import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { agentService } from "@/services/agent";
import type { Artifact } from "@/services/agent";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Download, Expand, X, TrendingUp, BarChart3, Sparkles } from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
  formattedText?: string;
  artifacts?: Artifact[];
  timestamp: Date;
}

const BigPurchasesPage: React.FC = () => {
  const { currentUser } = useAuth();
  const [selectedImage, setSelectedImage] = useState<Artifact | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "agent",
      text: "Welcome. I'm your Big Purchase Agent, trained on your personal transaction history to provide accurate financial insights.\n\nI analyze your actual spending patterns and financial data to deliver evidence-based recommendations for major purchases. Each analysis includes data visualizations generated from your transaction history.\n\nWhat big purchase are you considering? I'll provide a data-driven assessment based on your financial profile.",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [contextId, setContextId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Helper function to format response text with bold and newlines
  const formatResponseText = (text: string) => {
    // Convert markdown-style bold (**text**) to HTML bold tags
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert newlines to <br> tags for proper display
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
      const response = await agentService.sendBigPurchaseQuery(
        inputValue,
        contextId
      );
      const responseText = agentService.extractResponseText(response);
      const artifacts = agentService.extractArtifacts(response);
      const sessionId = agentService.getSessionId(response);

      if (sessionId) {
        setContextId(sessionId);
      }

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: responseText,
        formattedText: formatResponseText(responseText),
        artifacts: artifacts,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "agent",
        text: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-6 px-4 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
          ML-Powered Big Purchase Advisor
          <span className="text-lg bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent font-medium">
            (Trained on Your Data)
          </span>
        </h1>
        <p className="text-muted-foreground mt-2">
          Evidence-based purchase planning powered by machine learning models trained on your actual transaction history. 
          <strong className="text-primary"> Every recommendation comes with data visualizations!</strong>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Purchase Planning Tools */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Purchase Goals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="p-3 bg-muted rounded-lg">
                  <p className="font-medium">Home Purchase</p>
                  <p className="text-sm text-muted-foreground">
                    Target: $500,000
                  </p>
                  <div className="mt-2 bg-background rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: "15%" }}
                    ></div>
                  </div>
                </div>
                <Button variant="outline" className="w-full">
                  Add New Goal
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Affordability Calculator
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Calculate what you can afford based on your income and expenses
              </p>
              <Button className="w-full mt-3">Open Calculator</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Savings Progress</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">$15,000</p>
              <p className="text-sm text-muted-foreground">
                Saved for big purchases
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle>Chat with Your Big Purchase Advisor</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto custom-scrollbar">
              <div className="space-y-4 animate-slide-up">
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
                        <div>
                          <div
                            className="text-sm"
                            dangerouslySetInnerHTML={{
                              __html: message.formattedText,
                            }}
                          />
                          {/* Display graphs/images with enhanced UI */}
                          {message.artifacts && message.artifacts.map((artifact, index) => (
                            artifact.type === "image" && (
                              <div key={index} className="mt-4 relative group">
                                <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 p-1">
                                  <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-primary/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                  
                                  {/* Graph container with glassmorphism effect */}
                                  <div className="relative bg-background/95 backdrop-blur-sm rounded-lg p-2">
                                    {/* Graph header */}
                                    <div className="flex items-center justify-between mb-2 px-2">
                                      <div className="flex items-center gap-2">
                                        <BarChart3 className="h-4 w-4 text-primary animate-pulse" />
                                        <span className="text-xs font-medium text-primary">Data Visualization</span>
                                      </div>
                                      <div className="flex gap-1">
                                        <button
                                          onClick={() => setSelectedImage(artifact)}
                                          className="p-1.5 hover:bg-primary/10 rounded-lg transition-colors group/expand"
                                          title="View fullscreen"
                                        >
                                          <Expand className="h-3.5 w-3.5 text-muted-foreground group-hover/expand:text-primary transition-colors" />
                                        </button>
                                        <button
                                          onClick={() => {
                                            const link = document.createElement('a');
                                            link.href = artifact.data;
                                            link.download = artifact.name || `graph-${Date.now()}.png`;
                                            link.click();
                                          }}
                                          className="p-1.5 hover:bg-primary/10 rounded-lg transition-colors group/download"
                                          title="Download graph"
                                        >
                                          <Download className="h-3.5 w-3.5 text-muted-foreground group-hover/download:text-primary transition-colors" />
                                        </button>
                                      </div>
                                    </div>
                                    
                                    {/* The actual graph image */}
                                    <img 
                                      src={artifact.data} 
                                      alt={artifact.name || `Graph ${index + 1}`}
                                      className="rounded-lg shadow-2xl w-full cursor-pointer transform transition-all duration-300 hover:scale-[1.02]"
                                      style={{ maxWidth: '500px' }}
                                      onClick={() => setSelectedImage(artifact)}
                                    />
                                    
                                    {/* Graph footer with name and sparkle effect */}
                                    {artifact.name && (
                                      <div className="mt-2 px-2 flex items-center justify-between">
                                        <p className="text-xs font-medium text-muted-foreground">
                                          {artifact.name.replace('.png', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </p>
                                        <Sparkles className="h-3 w-3 text-yellow-500 animate-pulse" />
                                      </div>
                                    )}
                                  </div>
                                </div>
                                
                                {/* Glow effect on hover */}
                                <div className="absolute -inset-1 bg-gradient-to-r from-primary/30 to-primary/30 rounded-xl blur-xl opacity-0 group-hover:opacity-50 transition-opacity duration-500 -z-10" />
                              </div>
                            )
                          ))}
                        </div>
                      ) : (
                        <div>
                          <p className="text-sm">{message.text}</p>
                          {/* Enhanced graph display for user messages */}
                          {message.artifacts && message.artifacts.map((artifact, index) => (
                            artifact.type === "image" && (
                              <div key={index} className="mt-4">
                                <img 
                                  src={artifact.data} 
                                  alt={artifact.name || `Graph ${index + 1}`}
                                  className="rounded-lg shadow-xl w-full cursor-pointer hover:scale-105 transition-transform"
                                  style={{ maxWidth: '500px' }}
                                  onClick={() => setSelectedImage(artifact)}
                                />
                                {artifact.name && (
                                  <p className="text-xs mt-1 opacity-70">{artifact.name}</p>
                                )}
                              </div>
                            )
                          ))}
                        </div>
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
                  placeholder="Ask me to analyze your data! E.g., 'Show my spending trends' or 'Can I afford a $500K house?'"
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
      
      {/* Fullscreen Modal for Graphs */}
      {selectedImage && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-300"
          onClick={() => setSelectedImage(null)}
        >
          <div 
            className="relative max-w-7xl max-h-[90vh] bg-background/10 backdrop-blur-xl rounded-2xl p-2 border border-primary/20 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="absolute top-4 right-4 z-10 flex gap-2">
              <button
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = selectedImage.data;
                  link.download = selectedImage.name || `graph-${Date.now()}.png`;
                  link.click();
                }}
                className="p-2 bg-primary/20 hover:bg-primary/30 rounded-full backdrop-blur-sm transition-colors"
                title="Download"
              >
                <Download className="h-5 w-5 text-primary-foreground" />
              </button>
              <button
                onClick={() => setSelectedImage(null)}
                className="p-2 bg-primary/20 hover:bg-primary/30 rounded-full backdrop-blur-sm transition-colors"
                title="Close"
              >
                <X className="h-5 w-5 text-primary-foreground" />
              </button>
            </div>
            
            {/* Graph title with gradient */}
            <div className="absolute top-4 left-4 z-10">
              <div className="flex items-center gap-2 bg-background/80 backdrop-blur-sm px-4 py-2 rounded-full border border-primary/20">
                <TrendingUp className="h-5 w-5 text-primary" />
                <span className="font-semibold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                  {selectedImage.name?.replace('.png', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Data Visualization'}
                </span>
              </div>
            </div>
            
            {/* The fullscreen image */}
            <div className="mt-12 flex items-center justify-center">
              <img 
                src={selectedImage.data} 
                alt={selectedImage.name || 'Graph'}
                className="max-w-full max-h-[75vh] rounded-xl shadow-2xl"
              />
            </div>
            
            {/* Decorative gradient borders */}
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-primary/20 via-transparent to-primary/20 pointer-events-none" />
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-primary/20 via-transparent to-primary/20 pointer-events-none" />
          </div>
        </div>
      )}
    </div>
  );
};

export default BigPurchasesPage;
