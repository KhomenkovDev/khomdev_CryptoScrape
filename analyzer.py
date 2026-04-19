import os
import json
import asyncio
from typing import List, Dict, Optional
from google import genai
from google.genai import types as genai_types
from pydantic import BaseModel
from loguru import logger
from config import settings

class SentimentReport(BaseModel):
    score: float  # 0 to 100
    label: str    # Positive, Neutral, Negative
    summary: str
    strengths: List[str]
    weaknesses: List[str]

class MarketingTask(BaseModel):
    title: str
    description: str
    priority: str  # High, Medium, Low
    category: str  # PR, Product, Social, Customer Service

class CompetitorComparison(BaseModel):
    competitor_name: str
    relative_sentiment: str # Better, Worse, Similar
    competitive_advantage: str
    threat_level: str # Low, Medium, High

class BrandAnalysis(BaseModel):
    brand_name: str
    overall_sentiment: str
    sentiment_score: float # 0-100
    platform_reports: Dict[str, SentimentReport]
    strategic_suggestions: List[str]
    marketing_roadmap: List[MarketingTask]
    competitor_analysis: Optional[CompetitorComparison] = None

class BrandAnalyzer:
    MODEL_ID = "gemini-2.5-flash"

    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self.client = None

    async def analyze(self, brand_name: str, scraped_data: Dict[str, List[str]], competitor_name: Optional[str] = None) -> BrandAnalysis:
        if settings.DEMO_MODE or not self.client:
            logger.info("Executing in DEMO_MODE: Generating mock analysis.")
            return await self._generate_mock_analysis(brand_name, competitor_name)

        prompt = f"""
        Analyze the following scraped Web3 community data for the project: "{brand_name}".
        {"Compare it against competitor project: " + competitor_name if competitor_name else ""}
        
        Data to process:
        {json.dumps(scraped_data, indent=2)}
        
        Provide a deep Web3 sentiment report. Focus on token utility, community hype, developer activity (if applicable), and overall 'vibes'.
        Format your response as a valid JSON matching this schema:
        {{
            "brand_name": "{brand_name}",
            "overall_sentiment": "Bullish/Bearish/Neutral",
            "sentiment_score": 0-100,
            "platform_reports": {{
                "platform": {{
                    "score": 0-100,
                    "label": "Bullish/Neutral/Bearish",
                    "summary": "Summarize the community sentiment on this platform...",
                    "strengths": ["e.g. strong whale interest", "vibrant community"],
                    "weaknesses": ["e.g. FUD regarding unlock", "low engagement"]
                }}
            }},
            "strategic_suggestions": ["tip 1 to improve token sentiment", "tip 2"],
            "marketing_roadmap": [
                {{"title": "Campaign Name", "description": "Community building idea...", "priority": "High/Medium/Low", "category": "PR/Governance/Social/Utility"}}
            ],
            "competitor_analysis": {{
                "competitor_name": "{competitor_name if competitor_name else 'N/A'}",
                "relative_sentiment": "Stronger/Weaker/Similar",
                "competitive_advantage": "What makes this project unique in the Web3 space?",
                "threat_level": "Low/Medium/High"
            }} (only if competitor provided)
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.MODEL_ID,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            return BrandAnalysis.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Gemini Analysis failed: {str(e)}")
            if settings.DEMO_MODE:
                return await self._generate_mock_analysis(brand_name, competitor_name)
            raise

    async def _generate_mock_analysis(self, brand_name: str, competitor_name: Optional[str]) -> BrandAnalysis:
        # Simulate local delay
        await asyncio.sleep(1.5)
        
        # Deterministic but dynamic mock values based on the brand name
        score_base = 70 + (len(brand_name) % 25)
        label = "Positive" if score_base > 75 else "Neutral"
        
        mock_data = {
            "brand_name": brand_name,
            "overall_sentiment": f"Highly {label}" if label == "Positive" else "Stable",
            "sentiment_score": float(score_base),
            "platform_reports": {
                "google": {
                    "score": float(score_base + 5),
                    "label": label,
                    "summary": f"{brand_name} shows strong performance in local visibility and customer trust.",
                    "strengths": ["Consistent quality", "Brand heritage"],
                    "weaknesses": ["Availability in niche markets"]
                },
                "news": {
                    "score": float(score_base - 5),
                    "label": "Neutral",
                    "summary": f"Recent coverage for {brand_name} focuses on market expansion and new leadership.",
                    "strengths": ["Innovation focus"],
                    "weaknesses": ["Regulatory compliance"]
                }
            },
            "strategic_suggestions": [
                f"Double down on {brand_name}'s digital presence to capture younger demographics.",
                f"Improve response time to critical news mentions for {brand_name}."
            ],
            "marketing_roadmap": [
                {
                    "title": "Community Engagement Program",
                    "description": "Develop a localized community program to strengthen brand loyalty.",
                    "priority": "High",
                    "category": "Social"
                },
                {
                    "title": "Supply Chain Transparency",
                    "description": "Publish a transparency report to address logistics concerns.",
                    "priority": "Medium",
                    "category": "Product"
                }
            ]
        }
        
        if competitor_name:
            # Deterministic comparison: brand is "Better" if its name is alphabetically before competitor
            # This ensures that swapping brands swaps the status!
            is_better = brand_name.lower() < competitor_name.lower()
            rel_sentiment = "Better" if is_better else "Worse"
            
            mock_data["competitor_analysis"] = {
                "competitor_name": competitor_name,
                "relative_sentiment": rel_sentiment,
                "competitive_advantage": f"{brand_name} has higher agility and better price-to-value ratio compared to {competitor_name}." if is_better else f"{competitor_name} currently leads in technical innovation and market share.",
                "threat_level": "High" if not is_better else "Medium"
            }
            
        return BrandAnalysis(**mock_data)
