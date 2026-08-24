from pydantic import BaseModel, ConfigDict, Field


class DeveloperInfo(BaseModel):
    name: str = Field(..., description="Developer full name")
    username: str = Field(..., description="Developer username")
    website: str = Field(..., description="Developer website URL")


class WelcomeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Welcome to SecureLedger Vault — Personal Expense Tracker API",
                "project": "SecureLedger Vault",
                "version": "1.2.0",
                "documentation": {
                    "swagger_ui": "https://your-domain.com/docs",
                    "redoc": "https://your-domain.com/redoc",
                    "openapi_json": "https://your-domain.com/openapi.json",
                },
                "system": {
                    "health": "https://your-domain.com/health",
                    "root": "https://your-domain.com/",
                },
                "developer": {
                    "name": "Md. Nazmus Sakib",
                    "username": "engrsakib",
                    "website": "https://engrsakib.com",
                },
            }
        }
    )

    message: str
    project: str
    version: str
    documentation: dict[str, str]
    system: dict[str, str]
    developer: DeveloperInfo
