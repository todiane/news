from enum import Enum
from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

class APIVersion(str, Enum):
    V1 = "1.0"
    V1_1 = "1.1"
    V2 = "2.0"

class VersionedAPIConfig:
    """Configuration for versioned API endpoints."""
    
    def __init__(self):
        self.current_version = APIVersion.V1
        self.supported_versions = {
            APIVersion.V1: "2024-01-29",  # Release date of each version
            APIVersion.V1_1: "2024-02-15",
            APIVersion.V2: "2024-03-01"
        }
        self.deprecated_versions = set()  # Set of deprecated versions
        self.sunset_dates = {}  # Version: Sunset date mapping

    def is_supported(self, version: str) -> bool:
        """Check if a version is supported."""
        return version in APIVersion.__members__.values()

    def is_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated."""
        return version in self.deprecated_versions
    
    def get_version_features(self, version: str) -> set:
        """Get available features for a specific version"""
        features = {
            APIVersion.V1: {"basic_crud", "auth"},
            APIVersion.V1_1: {"basic_crud", "auth", "feed_management", "notifications"},
            APIVersion.V2: {"basic_crud", "auth", "feed_management", "notifications", "analytics", "bulk_operations"}
        }
        return features.get(version, set())

    def check_feature_availability(self, feature: str, version: str) -> bool:
        """Check if a feature is available in specified version"""
        available_features = self.get_version_features(version)
        return feature in available_features

    def get_migration_path(self, from_version: str, to_version: str) -> list:
        """Get migration steps between versions"""
        version_order = list(self.supported_versions.keys())
        try:
            start_idx = version_order.index(from_version)
            end_idx = version_order.index(to_version)
            return version_order[start_idx:end_idx + 1]
        except ValueError:
            return []

    async def verify_version(self, api_version: Optional[str] = Header(None, alias="X-API-Version")):
        """Dependency for checking API version headers."""
        if api_version is None:
            # Default to current version if none specified
            return self.current_version
            
        if not self.is_supported(api_version):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Unsupported API version",
                    "supported_versions": list(self.supported_versions.keys()),
                    "current_version": self.current_version
                }
            )
            
        if self.is_deprecated(api_version):
            # Still allow access but warn about deprecation
            headers = {
                "Warning": f'299 - "Deprecated API version {api_version}"',
                "X-API-Sunset-Date": str(self.sunset_dates.get(api_version, "TBD"))
            }
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail={
                    "message": f"API version {api_version} is deprecated",
                    "recommended_version": self.current_version,
                    "sunset_date": self.sunset_dates.get(api_version)
                },
                headers=headers
            )
            
        return api_version


class VersionFeatures:
    """Track features available in each API version"""
    def __init__(self, version: str, features: set):
        self.version = version
        self.features = features
        self.breaking_changes = []
        self.deprecated_features = set()


class VersionedResponse(BaseModel):
    """Base model for versioned API responses."""
    version: str
    deprecated: bool = False
    sunset_date: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "version": "1.0",
                "deprecated": False,
                "sunset_date": None
            }
        }

version_config = VersionedAPIConfig()
