# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Edit these values to change the ticker, date range, and output directory.
# All other modules read from here.

TICKER     = "SPY"
START_DATE = "1996-01-01"
END_DATE   = "2026-05-30"

# Directory where figures are saved (.png and .tiff at 300 dpi)
OUTPUT_DIR = "."

# Cycle detection thresholds
CORRECTION_THRESHOLD = 0.05   # minimum decline to record as an event
BEAR_THRESHOLD       = 0.20   # minimum decline to classify as a bear market

# Bull market threshold
BULL_THRESHOLD = 0.20         # minimum gain from trough to qualify as bull market
