import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Upload, Share2, Sparkles, X, RefreshCw } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

// Hardcoded backend URL - same as in your agent.ts
const AGENT_BASE_URL =
  "https://financial-service-agent-609099553774.us-central1.run.app";

interface TripVisualizationProps {
  tripId: string;
  userId: string;
}

export const TripVisualization: React.FC<TripVisualizationProps> = ({
  tripId,
  userId,
}) => {
  const [prompt, setPrompt] = useState("");
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referenceImagePreview, setReferenceImagePreview] = useState<
    string | null
  >(null);
  const [visual, setVisual] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const { toast } = useToast();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (referenceImagePreview) {
        URL.revokeObjectURL(referenceImagePreview);
      }
    };
  }, [referenceImagePreview]);

  // Handle reference image selection
  const handleImageSelect = (file: File | null) => {
    if (referenceImagePreview) {
      URL.revokeObjectURL(referenceImagePreview);
    }

    if (file) {
      setReferenceImage(file);
      setReferenceImagePreview(URL.createObjectURL(file));
    } else {
      setReferenceImage(null);
      setReferenceImagePreview(null);
    }
  };

  const generateVisualization = async () => {
    setLoading(true);

    const formData = new FormData();
    formData.append("trip_id", tripId);
    formData.append("user_id", userId);
    formData.append("prompt", prompt);
    if (referenceImage) {
      formData.append("reference_image", referenceImage);
    }

    try {
      const response = await fetch(
        `${AGENT_BASE_URL}/api/trips/${tripId}/visualize`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(
          `Failed to generate visualization: ${response.statusText}`
        );
      }

      const result = await response.json();
      setVisual(result);

      toast({
        title: "Visualization created!",
        description:
          "Your image has been generated. Video animation is processing...",
      });

      // Poll for video completion
      if (result.video_status === "pending") {
        pollForVideo();
      }
    } catch (error) {
      console.error("Failed to generate visualization:", error);
      //   toast({
      //     title: "Generation failed",
      //     description: "Unable to create visualization. Please try again.",
      //     variant: "destructive",
      //   });
    } finally {
      setLoading(false);
    }
  };

  const pollForVideo = () => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    intervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(
          `${AGENT_BASE_URL}/api/trips/${tripId}/visuals`
        );
        if (!response.ok) throw new Error("Failed to fetch visuals");

        const visuals = await response.json();
        const currentVisual = visuals.find((v: any) => v.user_id === userId);

        if (currentVisual?.video_status === "ready") {
          setVisual(currentVisual);
          setVideoReady(true);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
          toast({
            title: "Video ready!",
            description: "Your animated visualization is now available.",
          });
        } else if (currentVisual?.video_status === "failed") {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
          //   toast({
          //     title: "Video generation failed",
          //     description:
          //       "The animation couldn't be created, but your image is still available.",
          //     variant: "destructive",
          //   });
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 5000);
  };

  const regenerate = () => {
    setVisual(null);
    setVideoReady(false);
    generateVisualization();
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Visualize Your Trip
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Input
            placeholder="Describe your dream trip scene..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="mb-2"
            disabled={loading}
          />

          <div className="flex gap-2 items-center">
            <label className="flex items-center gap-2 cursor-pointer border rounded-md px-3 py-2 hover:bg-accent">
              <Upload className="h-4 w-4" />
              <span className="text-sm">
                {referenceImage ? "Change photo" : "Add yourself to the scene"}
              </span>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => handleImageSelect(e.target.files?.[0] || null)}
                className="hidden"
                disabled={loading}
              />
            </label>

            {referenceImage && (
              <Button
                variant="outline"
                size="icon"
                onClick={() => handleImageSelect(null)}
                disabled={loading}
              >
                <X className="h-4 w-4" />
              </Button>
            )}

            <Button
              onClick={generateVisualization}
              disabled={!prompt || loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate"
              )}
            </Button>

            {visual && (
              <Button
                variant="outline"
                size="icon"
                onClick={regenerate}
                disabled={loading}
                title="Regenerate"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
          </div>

          {referenceImagePreview && (
            <div className="mt-2">
              <img
                src={referenceImagePreview}
                alt="Reference"
                className="h-20 w-20 object-cover rounded-md"
              />
            </div>
          )}
        </div>

        {visual && (
          <div className="space-y-4">
            {visual.image_url && (
              <div className="relative">
                <img
                  src={visual.image_url}
                  alt="Trip visualization"
                  className="w-full rounded-lg"
                />
                <div className="absolute top-2 right-2 flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => window.open(visual.image_url, "_blank")}
                  >
                    View Full Size
                  </Button>
                </div>
              </div>
            )}

            {visual.video_status === "pending" && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating animated version...
              </div>
            )}

            {visual.video_url && (
              <video
                src={visual.video_url}
                controls
                className="w-full rounded-lg"
                preload="metadata"
              />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
