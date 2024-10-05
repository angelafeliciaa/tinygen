from pydantic import BaseModel

class CodegenRequest(BaseModel):
    repoUrl: str
    prompt: str