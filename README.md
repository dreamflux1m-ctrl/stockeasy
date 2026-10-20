# StockEasy — beginner stock analysis app

StockEasy is a local Streamlit app for learning about stocks. It includes:
- Historical price chart with 1 month through 10 years and maximum available history
- Line and candlestick chart, plus volume
- Historical return, CAGR, annualized volatility, maximum drawdown, and calendar-year returns
- Company snapshot and common valuation/fundamental metrics where provided
- Comparison of up to five tickers, normalized to 100 at the start
- Hypothetical investment calculator using historical adjusted prices
- Provider financial statements and CSV downloads

## Important data note
This first version uses `yfinance`, an unofficial open-source interface to Yahoo Finance. Its maintainers say it is intended for research and educational purposes and that the underlying data is intended for personal use. Coverage, accuracy, freshness, and availability are not guaranteed. Review the current provider terms before use. Do not redistribute data or use this as a public/commercial data service unless you have confirmed the required rights.

This app is educational only, not financial advice. It does not execute trades. Historical performance does not predict future results.

## Windows setup

1. Install Python from https://www.python.org/downloads/ (during installation, tick **Add Python to PATH**).
2. Extract the ZIP to a folder you can find, for example `C:\StockEasy`.
3. Open that folder in File Explorer.
4. Click the folder address bar, type `cmd`, and press Enter.
5. In the terminal, run these commands one at a time:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

6. The app should open in your browser. If it does not, copy the local URL printed in the terminal (usually `http://localhost:8501`) into Chrome.
7. Keep the terminal window open while using the app. Press `Ctrl+C` in that window to stop it.

If `python` is not recognized, try `py` instead, or reinstall Python and enable **Add Python to PATH**.

## Ticker examples
- India NSE: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS`
- India BSE examples often use `.BO`, where the provider supports them
- US: `AAPL`, `MSFT`, `NVDA`, `GOOGL`
- ETFs/indices depend on provider availability, e.g. `SPY`

Ticker formats and data availability may change. The app asks the provider for all available history; a full 10 years may not exist for newer listings.

## Common problems
- **No data:** verify ticker spelling and suffix; try `AAPL` or `RELIANCE.NS`.
- **Rate limit / connection error:** wait a while, retry later, and avoid repeatedly refreshing many tickers.
- **Missing fundamentals:** some exchanges or companies do not provide every field through the source.
- **Windows blocks activation in PowerShell:** use Command Prompt (`cmd`) as described above. If you are using PowerShell, you may need a different activation command.
- **App does not start:** check that `.venv` is active and rerun `pip install -r requirements.txt`.

## Files
- `app.py` — application
- `requirements.txt` — Python dependencies
- `README.md` — this guide
- `.gitignore` — excludes local virtual environment and secrets

## Next steps for a public launch
For a public app, choose a market-data provider that explicitly permits your intended display and redistribution, and keep provider credentials on a backend. Add tests, privacy/security review, clear timestamp and delay labels, and suitable disclaimers. Yahoo Finance data through `yfinance` is not a safe default for commercial redistribution.
