"""Global settings for CLI."""

class Settings:
    def __init__(self):
        self.verbose = False
        self.quiet = False
        self.format = 'json'
        self.timeout = 30000
        self.headless = False  # Default to headed (visible browser)

    def reset(self):
        """Reset to defaults."""
        self.verbose = False
        self.quiet = False
        self.format = 'json'
        self.timeout = 30000
        self.headless = False

# Global settings instance
settings = Settings()
