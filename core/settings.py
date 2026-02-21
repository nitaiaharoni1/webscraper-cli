"""Global settings for CLI."""

from typing import Optional


class Settings:
    def __init__(self):
        self.verbose = False
        self.quiet = False
        self.format = "json"
        self.timeout = 30000
        self.headless = False  # Default to headed (visible browser)
        self.proxy: Optional[str] = None
        self.user_agent: Optional[str] = None

    def reset(self):
        """Reset to defaults."""
        self.verbose = False
        self.quiet = False
        self.format = "json"
        self.timeout = 30000
        self.headless = False
        self.proxy = None
        self.user_agent = None


# Global settings instance
settings = Settings()
