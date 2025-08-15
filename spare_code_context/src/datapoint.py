from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple

class QueryPoint(BaseModel):
    candidates: Dict[str, str]
class Prediction(BaseModel):
    context: str = ""
    prefix: str = ""
    suffix: str = ""

class DataPoint(BaseModel):
    """
    Pydantic model for code completion/search dataset entries.
    
    This model represents a code snippet with context, typically used for
    code completion tasks where the model needs to fill in missing code
    between a prefix and suffix.
    """
    
    id: str = Field(
        ..., 
        description="Unique identifier for this code entry"
    )
    
    repo: str = Field(
        ..., 
        description="Repository name in format 'owner/repo'"
    )
    
    revision: str = Field(
        ..., 
        description="Git commit hash/revision identifier"
    )
    
    path: str = Field(
        ..., 
        description="File path within the repository"
    )
    
    modified: List[str] = Field(
        ..., 
        description="List of file paths that were modified"
    )
    
    prefix: str = Field(
        ..., 
        description="Code content before the completion point"
    )
    
    suffix: str = Field(
        ..., 
        description="Code content after the completion point"
    )
    
    archive: str = Field(
        ..., 
        description="Archive file name containing the code"
    )
    
    completion_point: Optional[Tuple[int, int]] = Field(
        None, 
        description="Optional tuple indicating the line and column of the completion point"
    )
    
    diff: Optional[str] = Field(
        None, 
        description="Diff representation of changes between original and incomplete code"
    )

    class Config:
        # Allow extra fields in case the dataset schema evolves
        extra = "allow"
        
        # Example of how the model should be used
        schema_extra = {
            "example": {
                "id": "3c4689",
                "repo": "celery/kombu",
                "revision": "0d3b1e254f9178828f62b7b84f0307882e28e2a0",
                "path": "t/integration/test_redis.py",
                "modified": ["t/integration/common.py", "t/integration/test_redis.py"],
                "prefix": "from __future__ import absolute_import...",
                "suffix": "                ]:\n                    producer.publish(...",
                "archive": "celery__kombu-0d3b1e254f9178828f62b7b84f0307882e28e2a0.zip",
                "completion_point": (10, 4)
            }
        }