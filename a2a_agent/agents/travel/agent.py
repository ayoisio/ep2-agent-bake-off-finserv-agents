# Filename: agents/travel/agent.py

from google.adk.agents import LlmAgent


def _make_sub_agents():
    planner = LlmAgent(
        name="travel_planner",
        model="gemini-2.5-flash",
        description="Plans itineraries and finds travel deals",
        instruction=(
            "You help plan trips by finding flights, hotels, and creating itineraries. "
            "When asked about travel options, provide helpful suggestions based on available data. "
            "Always consider user's budget constraints and preferences. "
            "Mention specific tools like search_flights, search_hotels, get_weather when relevant."
        ),
    )
    
    visualizer = LlmAgent(
        name="travel_visualizer",
        model="gemini-2.5-flash",
        description="Creates personalized travel visualizations to inspire saving",
        instruction=(
            "You create exciting travel visualizations to help users see themselves at their dream destination. "
            "When users express interest in a destination, enthusiastically offer to create a visualization. "
            "IMPORTANT: First, check if the session state contains 'uploaded_image_path'. "
            "If {uploaded_image_path} exists in the state:\n"
            "  - Use that value as the character_image_path parameter when calling create_travel_visualization\n"
            "  - Say something like 'I see you've uploaded a photo! Let me create your visualization.'\n"
            "  - Ask for their monthly savings amount\n"
            "  - Ask if they want an image, video, or both\n"
            "If {uploaded_image_path} does NOT exist in the state:\n"
            "  - Let them know they need to upload a photo first\n"
            "  - Say something like 'To create your personalized travel visualization, please upload a photo of yourself!'\n"
            "Always make the experience exciting and motivating! Help them visualize their dream trip becoming reality."
        ),
    )
    
    budget_advisor = LlmAgent(
        name="travel_budget_advisor",
        model="gemini-2.5-flash",
        description="Provides travel budgeting advice and savings strategies",
        instruction=(
            "You help users budget for trips and create savings plans. "
            "Calculate trip costs, suggest saving strategies, and find ways to reduce expenses. "
            "Use search_reddit_finance_advice and get_reddit_community_tips for community insights. "
            "Be encouraging and practical in your advice."
        ),
    )
    
    return planner, visualizer, budget_advisor


_sub_planner, _sub_visualizer, _sub_budget_advisor = _make_sub_agents()

root_agent = LlmAgent(
    name="travel_agent",
    model="gemini-2.5-flash",
    description="Coordinates travel planning, visualization, and budgeting assistance",
    instruction=(
        "You orchestrate travel planning and inspiration. You have three specialized sub-agents:\n"
        "1. 'travel_planner' - for finding flights, hotels, and creating itineraries\n"
        "2. 'travel_visualizer' - for creating personalized travel visualizations (NEW FEATURE!)\n"
        "3. 'travel_budget_advisor' - for budgeting and savings advice\n\n"
        "First, use 'travel_planner' to help with trip planning and logistics.\n"
        "When users mention a destination, always mention the exciting new visualization feature!\n"
        "Use 'travel_visualizer' to create inspiring images/videos of them at their destination.\n"
        "Use 'travel_budget_advisor' to help them create a savings plan.\n"
        "Keep responses concise and actionable."
    ),
    sub_agents=[_sub_planner, _sub_visualizer, _sub_budget_advisor],
)