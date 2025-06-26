from prophet import Prophet
import yfinance as yf
import pandas as pd

def predict_stock_price(symbol: str, years: int = 1):
    START = "2015-01-01"
    TODAY = pd.to_datetime("today").strftime("%Y-%m-%d")

    data = yf.download(symbol, start=START, end=TODAY)
    data.reset_index(inplace=True)

    df_train = data[["Date", "Close"]]
    df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

    model = Prophet()
    model.fit(df_train)
    future = model.make_future_dataframe(periods=years * 365)
    forecast = model.predict(future)

    fig1 = model.plot_components(forecast)
    fig2 = model.plot(forecast)

    return {
        "forecast": forecast.tail().to_dict(),
        "plot_components": str(fig1),
        "plot_forecast": str(fig2)
    }
