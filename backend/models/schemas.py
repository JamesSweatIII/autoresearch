from pydantic import BaseModel
from typing import List, Optional, Dict


class ResearchJobCreate(BaseModel):
    topic: str


class ResearchJobResponse(BaseModel):
    id: int
    topic: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    documents_count: int = 0
    top_keywords: List[str] = []
    avg_relevance: float = 0.0
    top_source: str = ""
    processing_time: float = 0.0
    summary: str = ""
    themes: List[str] = []
    research_gaps: List[str] = []
    topic_distribution: Dict = {}
    keyword_frequency: Dict = {}
    source_rankings: List[Dict] = []
    web_results_count: int = 0
    sentiment_distribution: Dict = {}


class DocumentResponse(BaseModel):
    id: int
    title: str
    authors: str
    source: str
    year: int
    abstract: str
    keywords: List[str]
    relevance_score: float
    sentiment: str
    sentiment_scores: Dict = {}
    topic_cluster: str
    source_type: str = "sample"
    url: str = ""
    paper_id: Optional[int] = None
    llm_verified: bool = False


class PipelineStatus(BaseModel):
    stage: str
    progress: float
    message: str
