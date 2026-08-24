from pydantic import BaseModel, ConfigDict, Field


class DeveloperInfo(BaseModel):
    name: str = Field(..., description="Developer full name")
    username: str = Field(..., description="Developer username")
    website: str = Field(..., description="Developer website URL")


class WelcomeData(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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

    project: str = Field(..., description="API project name")
    version: str = Field(..., description="API version")
    documentation: dict[str, str] = Field(..., description="Links to API documentation")
    system: dict[str, str] = Field(..., description="Core system endpoint URLs")
    developer: DeveloperInfo = Field(..., description="API developer information")


class HealthData(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok", "redis": "connected"}}
    )

    status: str = Field(..., description="Overall service status", examples=["ok"])
    redis: str = Field(..., description="Redis connectivity", examples=["connected", "disconnected"])
