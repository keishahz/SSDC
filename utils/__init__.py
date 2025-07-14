# Helper functions for SSDC dashboard
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def clean_column_names(df):
    """Bersihkan nama kolom: lowercase, strip, ganti spasi dengan underscore."""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    return df

def drop_missing(df, subset=None):
    """Drop missing values, optionally only for certain columns."""
    return df.dropna(subset=subset)

def plot_bar_top(series, n=10, xlabel='', ylabel='', title='', color='Blues_r'):
    """Plot bar chart top n dari sebuah Series (misal hasil groupby)."""
    fig, ax = plt.subplots()
    top = series.sort_values(ascending=False).head(n)
    sns.barplot(x=top.values, y=top.index, ax=ax, palette=color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    return fig

def plot_scatter(df, x, y, alpha=0.5, title=''):
    """Plot scatterplot sederhana."""
    fig, ax = plt.subplots()
    sns.scatterplot(x=x, y=y, data=df, alpha=alpha, ax=ax)
    ax.set_title(title)
    return fig

# Tambahkan helper lain sesuai kebutuhan
