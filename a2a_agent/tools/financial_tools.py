# Filename: tools/financial_tools.py

import os
import requests
from typing import Union, Optional
import tempfile

API_BASE_URL = os.environ.get("API_BASE_URL", "https://backend-ep2-879168005744.us-west1.run.app/api")

def get_user_profile(user_id: str) -> dict:
    """
    Gets a user's profile.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}")
    return response.json()

def get_user_accounts(user_id: str) -> dict:
    """
    Fetches all accounts for a specific user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/accounts")
    return response.json()

def get_user_transactions(user_id: str) -> dict:
    """
    Retrieves all transactions for a user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/transactions")
    return response.json()

def get_user_debts(user_id: str) -> dict:
    """
    Retrieves all debt accounts for a user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/debts")
    return response.json()

def get_user_investments(user_id: str) -> dict:
    """
    Retrieves all investment accounts for a user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/investments")
    return response.json()

def get_user_networth(user_id: str) -> dict:
    """
    Calculates the net worth of a user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/networth")
    return response.json()

def get_user_cashflow(user_id: str) -> dict:
    """
    Calculates the cash flow for a user over the last 30 days.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/cashflow")
    return response.json()

def get_user_average_cashflow(user_id: str) -> dict:
    """
    Calculates the average monthly cash flow for a user over the last 3 months.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/average_cashflow")
    return response.json()

def get_user_goals(user_id: str) -> dict:
    """
    Retrieves a user's financial goals.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/goals")
    return response.json()

def update_user_goal(goal_id: str, goal_data: dict) -> dict:
    """
    Updates a specific financial goal.
    
    Required Inputs:
    - goal_id (str): The unique identifier for the goal (e.g., 'goal-001')
    - goal_data (dict): Dictionary containing goal fields to update
        Example: {'target_amount': 15000, 'deadline': '2026-12-31'}
    """
    response = requests.put(f"{API_BASE_URL}/goals/{goal_id}", json=goal_data)
    return response.json()

def create_user_account(account_data: dict, user_id: str) -> dict:
    """
    Creates a new account for a specific user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    - account_data (dict): Dictionary containing account information
        Example: {
            'type': 'savings',
            'description': 'Emergency Fund',
            'balance': 0,
            'institution': 'Cymbal Bank'
        }
    """
    response = requests.post(f"{API_BASE_URL}/users/{user_id}/accounts", json=account_data)
    return response.json()

def get_user_transactions_with_history(user_id: str, history_days: int = 30) -> dict:
    """
    Retrieves all transactions for a user from the last N days.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    - history_days (int): Number of days to look back (default: 30)
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/transactions", params={"history": history_days})
    return response.json()

def create_user_goal(goal_data: dict) -> dict:
    """
    Creates a new financial goal for a user.
    
    Required Inputs:
    - goal_data (dict): Dictionary containing goal information
        Example: {
            'user_id': 'user-001',
            'description': 'Save $10,000',
            'target_amount': 10000,
            'target_date': '2025-12-31',
            'current_amount_saved': 0
        }
    """
    response = requests.post(f"{API_BASE_URL}/goals", json=goal_data)
    return response.json()

def delete_user_goal(goal_id: str) -> dict:
    """
    Cancels/deletes a specific financial goal.
    
    Required Inputs:
    - goal_id (str): The unique identifier for the goal (e.g., 'goal-001')
    """
    response = requests.delete(f"{API_BASE_URL}/goals/{goal_id}")
    return response.json()

async def create_travel_visualization(context, destination: str, character_image_path: str, 
                              scene_description: Optional[str], generate_video: bool,
                              monthly_savings: float) -> dict:
    """
    Create a personalized travel visualization showing the user at their dream destination.
    
    Required Inputs:
    - context: The tool context (automatically provided by ADK)
    - destination (str): Travel destination (e.g., 'Paris', 'Tokyo', 'Bali')
    - character_image_path (str): Artifact filename from session state (e.g., 'user_photo_xxx.png')
    - scene_description (Optional[str]): Custom scene description (pass None for default)
    - generate_video (bool): Whether to generate a video
    - monthly_savings (float): Monthly savings amount for trip
    """
    from .travel_visualization_tools import TravelVisualizationTools
    
    # Load the image artifact
    try:
        image_artifact = await context.load_artifact(character_image_path)
        if not image_artifact or not image_artifact.inline_data:
            return {
                "success": False,
                "error": f"Could not load uploaded image. Please make sure you've uploaded a photo.",
                "message": "I couldn't find your uploaded photo. Please upload an image and try again."
            }
        
        # Save artifact data to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_artifact.inline_data.data)
            temp_path = tmp_file.name
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process uploaded image: {str(e)}",
            "message": "There was an error processing your photo. Please try uploading it again."
        }
    
    viz_tools = TravelVisualizationTools()
    result = {
        "destination": destination,
        "visualization_complete": False
    }
    
    try:
        # Generate portrait using the temp file path
        portrait_result = viz_tools.generate_travel_portrait(
            destination=destination,
            character_image_path=temp_path,
            scene_description=scene_description
        )
        
        if portrait_result["success"]:
            result["portrait"] = {
                "success": True,
                "image_path": portrait_result["image_path"],
                "image_url": portrait_result.get("image_url"),
                "prompt_used": portrait_result["prompt_used"],
                "message": f"Here's you enjoying {destination}! This is what your trip could look like."
            }
            
            # Generate video if requested
            if generate_video:
                video_result = viz_tools.generate_travel_video(
                    image_path=portrait_result["image_path"],
                    destination=destination,
                    video_style="cinematic"
                )
                
                if video_result["success"]:
                    result["video"] = {
                        "success": True,
                        "video_path": video_result["video_path"],
                        "prompt_used": video_result["prompt_used"],
                        "message": "Your travel video is ready! Watch yourself exploring your dream destination."
                    }
                else:
                    result["video"] = {
                        "success": False,
                        "error": video_result["error"]
                    }
            
            # Calculate savings timeline
            savings_info = viz_tools.calculate_savings_timeline(
                destination=destination,
                monthly_savings=monthly_savings
            )
            
            result["savings_plan"] = savings_info
            result["visualization_complete"] = True
            
            # Add motivational message
            if savings_info["months_to_save"] < 6:
                timeline = "just a few months"
                excitement = "Your dream trip is right around the corner!"
            elif savings_info["months_to_save"] < 12:
                timeline = "less than a year"
                excitement = "Start saving now and you'll be there before you know it!"
            else:
                timeline = f"about {int(savings_info['months_to_save']/12)} years"
                excitement = "Every journey begins with a single step. Start saving today!"
            
            result["motivation_message"] = (
                f"Looking at yourself in {destination} makes it feel real, doesn't it? "
                f"In {timeline}, this could be you! {excitement}"
            )
            
        else:
            result["error"] = portrait_result["error"]
            
    except Exception as e:
        result["error"] = f"Visualization error: {str(e)}"
        
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass  # Don't fail if cleanup fails
    
    return result

def get_bank_partners() -> dict:
    """
    Retrieves a list of all available bank partners and their associated benefits.
    
    Required Inputs:
    - None (no parameters required)
    """
    response = requests.get(f"{API_BASE_URL}/partners")
    return response.json()

def get_user_eligible_partners(user_id: str) -> dict:
    """
    Identifies and returns a list of partners a specific user can benefit from.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/partners/user/{user_id}")
    return response.json()

def create_user_schedule(schedule_data: dict, user_id: str) -> dict:
    """
    Creates a new scheduled transaction for a user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    - schedule_data (dict): Dictionary containing schedule information
        Example: {
            'source_account_id': 'acc-001',
            'destination_account_id': 'acc-002',
            'description': 'Monthly Savings',
            'frequency': 'monthly',
            'amount': 500
        }
    """
    response = requests.post(f"{API_BASE_URL}/users/{user_id}/schedules", json=schedule_data)
    return response.json()

def get_user_schedules(user_id: str) -> dict:
    """
    Retrieves all scheduled transactions for a specific user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/users/{user_id}/schedules")
    return response.json()

def update_user_schedule(schedule_id: str, schedule_data: dict) -> dict:
    """
    Updates an existing scheduled transaction.
    
    Required Inputs:
    - schedule_id (str): The unique identifier for the schedule (e.g., 'schedule-001')
    - schedule_data (dict): Dictionary containing schedule fields to update
        Example: {'amount': 600, 'frequency': 'bi-weekly'}
    """
    response = requests.put(f"{API_BASE_URL}/schedules/{schedule_id}", json=schedule_data)
    return response.json()

def delete_user_schedule(schedule_id: str) -> dict:
    """
    Deletes a scheduled transaction by its ID.
    
    Required Inputs:
    - schedule_id (str): The unique identifier for the schedule (e.g., 'schedule-001')
    """
    response = requests.delete(f"{API_BASE_URL}/schedules/{schedule_id}")
    return response.json()

def get_all_advisors() -> dict:
    """
    Gets a list of all available financial advisors.
    
    Required Inputs:
    - None (no parameters required)
    """
    response = requests.get(f"{API_BASE_URL}/advisors")
    return response.json()

def get_advisors_by_type(advisor_type: str) -> dict:
    """
    Gets advisors by their specialization type.
    
    Required Inputs:
    - advisor_type (str): The type of advisor specialization
        Examples: 'financial_planner', 'investment_advisor', 'tax_advisor'
    """
    response = requests.get(f"{API_BASE_URL}/advisors/{advisor_type}")
    return response.json()

def schedule_meeting(meeting_data: dict) -> dict:
    """
    Schedules a new meeting with an advisor.
    
    Required Inputs:
    - meeting_data (dict): Dictionary containing meeting information
        Example: {
            'user_id': 'user-001',
            'advisor_id': 'adv-001',
            'advisor_name': 'John Smith',
            'advisor_type': 'financial_planner',
            'meeting_time': '2024-12-20T10:00:00'
        }
    """
    response = requests.post(f"{API_BASE_URL}/meetings", json=meeting_data)
    return response.json()

def get_user_meetings(user_id: str) -> dict:
    """
    Gets all scheduled meetings for a specific user.
    
    Required Inputs:
    - user_id (str): The unique identifier for the user (e.g., 'user-001')
    """
    response = requests.get(f"{API_BASE_URL}/meetings/{user_id}")
    return response.json()

def cancel_meeting(meeting_id: str) -> dict:
    """
    Cancels a scheduled meeting.
    
    Required Inputs:
    - meeting_id (str): The unique identifier for the meeting (e.g., 'meet-001')
    """
    response = requests.delete(f"{API_BASE_URL}/meetings/{meeting_id}")
    return response.json()

def search_reddit_finance_advice(query: str, category: str = "general_finance") -> dict:
    """
    Search Reddit for finance-related advice and discussions.
    
    Required Inputs:
    - query (str): What to search for (e.g., "save money groceries", "budget travel europe")
    - category (str): Type of advice - "travel", "daily_spending", or "general_finance"
    """
    from .reddit_tools import get_reddit_tool
    
    reddit = get_reddit_tool()
    results = reddit.search_relevant_threads(query, category, limit=5)
    
    # Ensure results is a list
    if results is None:
        results = []
    
    # Format results for agent consumption
    formatted_results = {
        "query": query,
        "category": category,
        "found_threads": len(results),
        "threads": []
    }
    
    for thread in results:
        formatted_results["threads"].append({
            "title": thread["title"],
            "author": thread.get("author", "unknown"),
            "subreddit": f"r/{thread['subreddit']}",
            "url": thread["url"],
            "key_points": [comment["text"][:150] + "..." for comment in thread["top_comments"][:2]] if thread.get("top_comments") else [],
            "engagement": f"{thread['score']} upvotes, {thread['num_comments']} comments"
        })
    
    return formatted_results

def get_reddit_community_tips(topic: str, spending_type: str) -> dict:
    """
    Get community tips from Reddit on specific topics.
    
    Required Inputs:
    - topic (str): Specific topic to get tips about (e.g., "cheap meals", "flight deals")
    - spending_type (str): Either "travel" or "daily_spending"
    """
    from .reddit_tools import get_reddit_tool
    
    reddit = get_reddit_tool()
    threads = reddit.search_relevant_threads(topic, spending_type, limit=3)
    
    # Ensure threads is a list
    if threads is None:
        threads = []
    
    tips = []
    sources = []
    
    for thread in threads:
        sources.append({
            "title": thread["title"],
            "url": thread["url"],
            "subreddit": thread["subreddit"]
        })
        
        # Extract tips from top comments
        for comment in thread.get("top_comments", []):
            if comment.get("score", 0) > 10:
                tips.append(comment["text"][:200] + "...")
    
    return {
        "topic": topic,
        "community_advice_found": len(tips) > 0,
        "tips": tips[:5],  # Limit to 5 tips
        "sources": sources[:3]  # Top 3 sources
    }

def get_tool_prompt() -> str:
    """
    System prompts and instructions for the Gemini Agent.
    This file contains the core instructions and tool usage guidelines.
    """
    # Tool usage guidelines with examples
    return """
    **Tool Usage Guidelines:**

    Use appropriate financial tools to answer user queries. Present information professionally and concisely.

    **Examples for Each Tool:**

    **User Profile & Accounts:**
    **User:** "What's my financial profile?"
    **Response:** "Let me retrieve your profile information."
    <tool_code>
    print(get_user_profile(user_id='user-001'))
    </tool_code>

    **User:** "Show me my accounts"
    **Response:** "I'll retrieve your account information."
    <tool_code>
    print(get_user_accounts(user_id='user-001'))
    </tool_code>

    **User:** "Create a new savings account"
    **Response:** "I'll help you create a new savings account."
    <tool_code>
    print(create_user_account(user_id='user-001', account_data={'type': 'savings', 'description': 'Emergency Fund', 'balance': 0}))
    </tool_code>

    **Transactions:**
    **User:** "What are my recent transactions?"
    **Response:** "Let me get your recent transaction history."
    <tool_code>
    print(get_user_transactions(user_id='user-001'))
    </tool_code>

    **User:** "Show transactions from last 60 days"
    **Response:** "I'll retrieve your transactions from the last 60 days."
    <tool_code>
    print(get_user_transactions_with_history(user_id='user-001', history_days=60))
    </tool_code>

    **Financial Analysis:**
    **User:** "Calculate my net worth"
    **Response:** "I'll calculate your current net worth."
    <tool_code>
    print(get_user_networth(user_id='user-001'))
    </tool_code>

    **User:** "Show my cash flow"
    **Response:** "I'll analyze your cash flow for the last 30 days."
    <tool_code>
    print(get_user_cashflow(user_id='user-001'))
    </tool_code>

    **User:** "What's my average monthly cash flow?"
    **Response:** "I'll calculate your average monthly cash flow."
    <tool_code>
    print(get_user_average_cashflow(user_id='user-001'))
    </tool_code>

    **Debts & Investments:**
    **User:** "Show my current debts"
    **Response:** "I'll retrieve your debt information."
    <tool_code>
    print(get_user_debts(user_id='user-001'))
    </tool_code>

    **User:** "What's in my investment portfolio?"
    **Response:** "I'll check your investment accounts."
    <tool_code>
    print(get_user_investments(user_id='user-001'))
    </tool_code>

    **Goals:**
    **User:** "Show my financial goals"
    **Response:** "I'll retrieve your current financial goals."
    <tool_code>
    print(get_user_goals(user_id='user-001'))
    </tool_code>

    **User:** "Create a goal to save $10,000"
    **Response:** "I'll create a new savings goal for you."
    <tool_code>
    print(create_user_goal(goal_data={'user_id': 'user-001', 'description': 'Save $10,000', 'target_amount': 10000, 'target_date': '2025-12-31', 'current_amount_saved': 0}))
    </tool_code>

    **User:** "Update my goal amount to $15,000"
    **Response:** "I'll update your goal target amount."
    <tool_code>
    print(update_user_goal(goal_id='goal-001', goal_data={'target_amount': 15000}))
    </tool_code>

    **User:** "Delete my old goal"
    **Response:** "I'll remove that goal for you."
    <tool_code>
    print(delete_user_goal(goal_id='goal-001'))
    </tool_code>

    **Bank Partners:**
    **User:** "Show available bank partners"
    **Response:** "I'll retrieve the list of available bank partners."
    <tool_code>
    print(get_bank_partners())
    </tool_code>

    **User:** "Which partners can I benefit from?"
    **Response:** "I'll check which partners you're eligible for."
    <tool_code>
    print(get_user_eligible_partners(user_id='user-001'))
    </tool_code>

    **Schedules:**
    **User:** "Create a monthly savings schedule"
    **Response:** "I'll set up a monthly savings schedule for you."
    <tool_code>
    print(create_user_schedule(user_id='user-001', schedule_data={'source_account_id': 'acc-001', 'destination_account_id': 'acc-002', 'description': 'Monthly Savings', 'frequency': 'monthly', 'amount': 500}))
    </tool_code>

    **User:** "Show my scheduled transactions"
    **Response:** "I'll retrieve your scheduled transactions."
    <tool_code>
    print(get_user_schedules(user_id='user-001'))
    </tool_code>

    **User:** "Update my savings amount to $600"
    **Response:** "I'll update your savings schedule amount."
    <tool_code>
    print(update_user_schedule(schedule_id='schedule-001', schedule_data={'amount': 600}))
    </tool_code>

    **User:** "Cancel my savings schedule"
    **Response:** "I'll remove that scheduled transaction."
    <tool_code>
    print(delete_user_schedule(schedule_id='schedule-001'))
    </tool_code>

    **Advisors & Meetings:**
    **User:** "Show available financial advisors"
    **Response:** "I'll retrieve the list of available advisors."
    <tool_code>
    print(get_all_advisors())
    </tool_code>

    **User:** "Show investment advisors"
    **Response:** "I'll find investment advisors for you."
    <tool_code>
    print(get_advisors_by_type('investment_advisor'))
    </tool_code>

    **User:** "Schedule a meeting with an advisor"
    **Response:** "I'll help you schedule a meeting."
    <tool_code>
    print(schedule_meeting(meeting_data={'user_id': 'user-001', 'advisor_id': 'adv-001', 'advisor_name': 'John Smith', 'advisor_type': 'financial_planner', 'meeting_time': '2024-12-20T10:00:00'}))
    </tool_code>

    **User:** "Show my scheduled meetings"
    **Response:** "I'll retrieve your scheduled meetings."
    <tool_code>
    print(get_user_meetings(user_id='user-001'))
    </tool_code>

    **User:** "Cancel my meeting"
    **Response:** "I'll cancel that meeting for you."
    <tool_code>
    print(cancel_meeting(meeting_id='meet-001'))
    </tool_code>

    **Community Insights from Reddit:**
    **User:** "What are the best ways to save on groceries?"
    **Response:** "I'll search for community tips on saving money on groceries."
    <tool_code>
    print(search_reddit_finance_advice(query='save money groceries', category='daily_spending'))
    </tool_code>

    **User:** "Any travel hacks for Europe?"
    **Response:** "Let me find community travel tips for Europe."
    <tool_code>
    print(get_reddit_community_tips(topic='Europe budget travel', spending_type='travel'))
    </tool_code>

    **Professional Standards:**
    - Use tools to provide accurate, current data
    - Present information in clear, organized formats
    - Offer brief insights when data reveals opportunities
    - Maintain professional tone throughout interactions
    - When sharing Reddit community tips, always cite the source subreddit
    """