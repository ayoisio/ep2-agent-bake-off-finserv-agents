import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { agentService, AgentType } from "@/services/agent";
import { useAuth } from "@/contexts/AuthContext";

const RobotIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect x="2" y="8" width="20" height="10" rx="2" ry="2"></rect>
    <path d="M6 8V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2"></path>
    <circle cx="8" cy="13" r="1"></circle>
    <circle cx="16" cy="13" r="1"></circle>
    <path d="M10 17h4"></path>
  </svg>
);

interface Message {
  sender: "user" | "bot";
  text: string;
  formattedText?: string;
  messageId?: string;
  contextId?: string;
}

const Chatbot: React.FC = () => {
  const { currentUser } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello! I am Cymbal Chat, your AI financial assistant. I can help you with your transaction history, current assets, financial planning, and more. How can I assist you today?",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [contextId, setContextId] = useState<string | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Helper function to format response text with bold and newlines
  const formatResponseText = (text: string) => {
    // Convert markdown-style bold (**text**) to HTML bold tags
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Convert newlines to <br> tags for proper display
    formattedText = formattedText.replace(/\n/g, "<br>");

    return formattedText;
  };

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Send message to Agent API
  const sendMessageToAPI = async (messageText: string): Promise<string> => {
    if (!currentUser) {
      return "Please log in to use the chat assistant.";
    }

    try {
      const response = await agentService.sendMessage(
        messageText,
        AgentType.GENERAL,
        contextId || undefined
      );

      // Update context ID if provided
      const sessionId = agentService.getSessionId(response);
      if (sessionId) {
        setContextId(sessionId);
      }

      return agentService.extractResponseText(response);
    } catch (error) {
      console.error("Error sending message to API:", error);
      return "Sorry, I encountered an error while processing your request. Please try again.";
    }
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() && !isLoading) {
      const userMessage: Message = {
        sender: "user",
        text: inputValue,
      };

      // Add user message immediately
      setMessages((prev) => [...prev, userMessage]);
      setInputValue("");
      setIsLoading(true);

      try {
        // Send to API and get response
        const apiResponse = await sendMessageToAPI(inputValue);

        const botMessage: Message = {
          sender: "bot",
          text: apiResponse,
          formattedText: formatResponseText(apiResponse),
          contextId: contextId || undefined,
        };

        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        console.error("Error handling message:", error);
        const errorMessage: Message = {
          sender: "bot",
          text: "Sorry, I encountered an error. Please try again.",
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // Handle click outside to close chat
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        chatRef.current &&
        buttonRef.current &&
        !chatRef.current.contains(event.target as Node) &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      <Button
        ref={buttonRef}
        onClick={toggleChat}
        className="fixed w-16 h-16 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 pointer-events-auto z-50"
        style={{ right: "7.5vw", bottom: "7.5vh" }}
      >
        <RobotIcon />
      </Button>

      {isOpen && (
        <Card
          ref={chatRef}
          className="fixed w-96 bg-card text-card-foreground shadow-2xl pointer-events-auto z-40"
          style={{ right: "7.5vw", bottom: "18vh" }}
        >
          <CardHeader>
            <CardTitle>Cymbal Chat</CardTitle>
          </CardHeader>
          <CardContent className="h-80 overflow-y-auto">
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`p-3 rounded-lg max-w-xs break-words ${
                      msg.sender === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {msg.sender === "bot" && msg.formattedText ? (
                      <div
                        dangerouslySetInnerHTML={{ __html: msg.formattedText }}
                      />
                    ) : (
                      msg.text
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="p-3 rounded-lg bg-muted text-muted-foreground">
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
          <CardFooter>
            <div className="flex w-full space-x-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Type a message..."
                disabled={isLoading || !currentUser}
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim() || !currentUser}
              >
                Send
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </div>
  );
};

export default Chatbot;
