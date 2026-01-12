"""Custom error handling for CLI."""

from typing import Optional


class CLIError(Exception):
    """Custom CLI error with suggestion support."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)

    def __str__(self):
        result = f'Error: {self.message}'
        if self.suggestion:
            result += f'\nSuggestion: {self.suggestion}'
        return result


class ElementNotFoundError(CLIError):
    """Element not found error."""

    def __init__(self, selector: str):
        super().__init__(
            f'Element "{selector}" not found',
            f'Check if the selector is correct or if the page has fully loaded. Try using --wait-for "{selector}" first.'
        )


class NavigationError(CLIError):
    """Navigation error."""

    def __init__(self, url: str, reason: str):
        super().__init__(
            f'Failed to navigate to {url}: {reason}',
            'Check if the URL is correct and accessible. Try increasing --timeout if the page loads slowly.'
        )


class TimeoutError(CLIError):
    """Timeout error."""

    def __init__(self, operation: str, timeout: int):
        super().__init__(
            f'{operation} timed out after {timeout}ms',
            f'Try increasing --timeout or check if the page/selector is accessible.'
        )
