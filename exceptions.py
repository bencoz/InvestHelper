class InvestHelperError(Exception):
    """Base exception for InvestHelper"""
    pass

class DataFetchError(InvestHelperError):
    """Raised when stock data cannot be fetched"""
    pass

class InvalidTickerError(InvestHelperError):
    """Raised when ticker symbol is invalid"""
    pass

class InsufficientDataError(InvestHelperError):
    """Raised when not enough data for analysis"""
    pass
