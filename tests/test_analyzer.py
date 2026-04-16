import pytest
from analyzer import BrandAnalyzer, BrandAnalysis, SentimentReport, MarketingTask
import asyncio

@pytest.mark.asyncio
async def test_mock_analysis():
    analyzer = BrandAnalyzer()
    # Ensure it's in demo mode or similar if we want to test _generate_mock_analysis
    report = await analyzer._generate_mock_analysis("TestBrand", "CompetitorX")
    
    assert isinstance(report, BrandAnalysis)
    assert report.brand_name == "TestBrand"
    assert report.competitor_analysis.competitor_name == "CompetitorX"
    assert len(report.marketing_roadmap) > 0
    assert report.sentiment_score > 0

def test_models():
    # Verify Pydantic models
    task = MarketingTask(title="T", description="D", priority="High", category="PR")
    report = SentimentReport(score=90, label="P", summary="S", strengths=[], weaknesses=[])
    
    analysis = BrandAnalysis(
        brand_name="B",
        overall_sentiment="Pos",
        sentiment_score=90,
        platform_reports={"p": report},
        strategic_suggestions=["s"],
        marketing_roadmap=[task]
    )
    assert analysis.brand_name == "B"
