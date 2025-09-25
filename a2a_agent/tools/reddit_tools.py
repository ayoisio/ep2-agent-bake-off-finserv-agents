"""
Minimal Reddit integration for Travel and Daily Spending agents
"""

import os
import logging
from typing import List, Dict, Any
import praw
from datetime import datetime

logger = logging.getLogger(__name__)

class RedditTool:
    """Lightweight Reddit search tool for agents"""
    
    # Relevant subreddits for each agent type
    SUBREDDIT_MAP = {
        "travel": ["travel", "solotravel", "TravelHacks", "digitalnomad", "backpacking"],
        "daily_spending": ["personalfinance", "budget", "frugal", "EatCheapAndHealthy", "MealPrepSunday"],
        "general_finance": ["personalfinance", "financialindependence", "povertyfinance"]
    }
    
    def __init__(self):
        """Initialize Reddit client"""
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID", "dummy_id"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET", "dummy_secret"),
                user_agent="FinanceAgent/1.0"
            )
            self.reddit.read_only = True  # We only need read access
            logger.info("Reddit client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self.reddit = None

    def search_relevant_threads(
        self, 
        query: str, 
        category: str = "general_finance",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant Reddit threads"""
        if not self.reddit:
            # Return mock data if Reddit isn't configured
            mock_threads = [
                {
                    "title": f"Best tips for {query} - Great community advice!",
                    "subreddit": "personalfinance",
                    "url": "https://reddit.com/r/personalfinance/mock1",
                    "score": 234,
                    "num_comments": 45,
                    "author": "frugal_master",
                    "selftext": "Here are my top tips for saving money on daily expenses...",
                    "top_comments": [
                        {"text": "Great advice! I save $200/month using these tips", "score": 89, "author": "budget_pro"},
                        {"text": "Don't forget to check store brands - same quality, lower price", "score": 67, "author": "smart_shopper"}
                    ]
                },
                {
                    "title": f"How I cut my {query} expenses by 40%",
                    "subreddit": "frugal",
                    "url": "https://reddit.com/r/frugal/mock2",
                    "score": 567,
                    "num_comments": 123,
                    "author": "money_saver_2024",
                    "selftext": "After tracking my expenses for 3 months, I found these areas to cut...",
                    "top_comments": [
                        {"text": "Meal planning is the key! Saved me hundreds", "score": 234, "author": "meal_prep_guru"},
                        {"text": "Try buying in bulk for non-perishables", "score": 156, "author": "bulk_buyer"}
                    ]
                }
            ]
            
            # Return appropriate number of mock threads
            return mock_threads[:min(limit, len(mock_threads))]
        
        try:
            subreddits = self.SUBREDDIT_MAP.get(category, self.SUBREDDIT_MAP["general_finance"])
            combined_subreddits = "+".join(subreddits)
            
            results = []
            
            for submission in self.reddit.subreddit(combined_subreddits).search(
                query, 
                sort="relevance", 
                time_filter="month",
                limit=limit
            ):
                submission.comment_sort = "best"
                submission.comments.replace_more(limit=0)
                
                top_comments = []
                for comment in submission.comments[:3]:
                    if hasattr(comment, 'body'):
                        top_comments.append({
                            "text": comment.body[:500],
                            "score": comment.score,
                            "author": str(comment.author) if comment.author else "[deleted]"
                        })
                
                results.append({
                    "title": submission.title,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "subreddit": submission.subreddit.display_name,
                    "url": f"https://reddit.com{submission.permalink}",
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "selftext": submission.selftext[:1000] if submission.selftext else "",
                    "top_comments": top_comments
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []  # Always return a list, never None

# Singleton instance
_reddit_tool = None

def get_reddit_tool() -> RedditTool:
    """Get or create Reddit tool instance"""
    global _reddit_tool
    if _reddit_tool is None:
        _reddit_tool = RedditTool()
    return _reddit_tool