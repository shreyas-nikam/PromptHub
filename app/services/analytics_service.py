# app/services/analytics_service.py
from typing import Dict, List, Any
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.execution import ExecutionLog
from app.models.feedback import Feedback

class AnalyticsService:
    async def get_usage_analytics(
        self,
        application_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage analytics for an application"""
        # Aggregation pipeline for usage stats
        pipeline = [
            {
                "$match": {
                    "application_id": ObjectId(application_id),
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                        "status": "$status"
                    },
                    "count": {"$sum": 1},
                    "avg_latency": {"$avg": "$latency_ms"},
                    "total_tokens": {"$sum": "$token_count"},
                    "total_cost": {"$sum": "$cost_usd"}
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "total_requests": {"$sum": "$count"},
                    "success_count": {
                        "$sum": {
                            "$cond": [{"$eq": ["$_id.status", "success"]}, "$count", 0]
                        }
                    },
                    "avg_latency": {"$avg": "$avg_latency"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_cost": {"$sum": "$total_cost"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await ExecutionLog.aggregate(pipeline).to_list()
        
        # Calculate success rate
        for result in results:
            result["success_rate"] = (
                result["success_count"] / result["total_requests"] * 100
                if result["total_requests"] > 0 else 0
            )
        
        return {
            "daily_usage": results,
            "summary": await self._calculate_summary(application_id, start_date, end_date)
        }
    
    async def get_prompt_performance(
        self,
        prompt_id: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific prompt"""
        match_criteria = {"prompt_id": ObjectId(prompt_id)}
        if version:
            match_criteria["version"] = version
        
        # Get prompt versions
        prompt_versions = await PromptVersion.find(match_criteria).to_list()
        version_ids = [pv.id for pv in prompt_versions]
        
        # Aggregation for performance metrics
        pipeline = [
            {
                "$match": {
                    "prompt_version_id": {"$in": version_ids}
                }
            },
            {
                "$facet": {
                    "execution_stats": [
                        {
                            "$group": {
                                "_id": "$model_provider",
                                "count": {"$sum": 1},
                                "avg_latency": {"$avg": "$latency_ms"},
                                "success_rate": {
                                    "$avg": {
                                        "$cond": [{"$eq": ["$status", "success"]}, 1, 0]
                                    }
                                },
                                "avg_tokens": {"$avg": "$token_count"},
                                "total_cost": {"$sum": "$cost_usd"}
                            }
                        }
                    ],
                    "feedback_stats": [
                        {
                            "$lookup": {
                                "from": "feedback",
                                "localField": "prompt_version_id",
                                "foreignField": "prompt_version_id",
                                "as": "feedback"
                            }
                        },
                        {"$unwind": "$feedback"},
                        {
                            "$group": {
                                "_id": null,
                                "avg_rating": {"$avg": "$feedback.rating"},
                                "total_feedback": {"$sum": 1}
                            }
                        }
                    ]
                }
            }
        ]
        
        results = await ExecutionLog.aggregate(pipeline).to_list()
        
        return {
            "execution_metrics": results[0]["execution_stats"] if results else [],
            "feedback_metrics": results[0]["feedback_stats"][0] if results and results[0]["feedback_stats"] else {
                "avg_rating": 0,
                "total_feedback": 0
            }
        }