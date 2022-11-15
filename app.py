import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

user = os.environ["user"]
password = os.environ["password"]
host = os.environ["host"]
port = os.environ["port"]
database = os.environ["database"]


import logging

logger = logging.getLogger()

if "df_main" not in st.session_state:

    try:

        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        )
    except:
        logger.error("Couldn't connect to Postgres SQL with SQLAlchelmy")

    df_sub_sub = pd.read_sql("agg_prices", engine)

    # Cleaning category names

    for col in ["main_category_name", "sub_category_name", "sub_sub_category_name"]:
        df_sub_sub[col] = df_sub_sub[col].str.strip()

    df_sub_sub["tmp_price"] = df_sub_sub["count_rows"] * df_sub_sub["avg_price"]
    df_sub_sub = df_sub_sub.rename({"avg_price": "average_price"}, axis=1)
    first_vals = (
        df_sub_sub.sort_values("day")
        .groupby("sub_sub_category_name")
        .transform("first")
    )
    df_sub_sub["normal"] = df_sub_sub["average_price"] / first_vals["average_price"]

    # Sub Category

    df_sub = (
        df_sub_sub.groupby(["sub_category_name", "day"])
        .agg({"tmp_price": sum, "count_rows": sum, "main_category_name": min})
        .reset_index()
    )
    df_sub["average_price"] = df_sub["tmp_price"] / df_sub["count_rows"]
    first_vals = (
        df_sub.sort_values("day").groupby("sub_category_name").transform("first")
    )
    df_sub["normal"] = df_sub["average_price"] / first_vals["average_price"]

    # Main Category

    df_main = (
        df_sub_sub.groupby(["main_category_name", "day"])
        .agg({"tmp_price": sum, "count_rows": sum})
        .reset_index()
    )
    df_main["average_price"] = df_main["tmp_price"] / df_main["count_rows"]
    first_vals = (
        df_main.sort_values("day").groupby("main_category_name").transform("first")
    )
    df_main["normal"] = df_main["average_price"] / first_vals["average_price"]

    st.session_state["df_sub_sub"] = df_sub_sub
    st.session_state["df_sub"] = df_sub
    st.session_state["df_main"] = df_main


df_sub_sub = st.session_state["df_sub_sub"]
df_sub = st.session_state["df_sub"]
df_main = st.session_state["df_main"]

select_level = st.selectbox(
    "Select level", options=["Main Categories", "Sub Categories", "Sub Sub Categories"]
)

if select_level == "Main Categories":
    plot_df = df_main
    color = "main_category_name"
elif select_level == "Sub Categories":
    main_cate = st.selectbox(
        "Choose main category", options=df_sub.main_category_name.unique()
    )
    color = "sub_category_name"
    plot_df = df_sub.query(f"main_category_name == '{main_cate}'")
else:
    main_cate = st.selectbox(
        "Choose main category", options=df_sub_sub.main_category_name.unique()
    )
    options = df_sub_sub.query(
        f"main_category_name == '{main_cate}'"
    ).sub_category_name.unique()
    sub_cate = st.selectbox("Choose Sub category", options=options)
    plot_df = df_sub_sub.query(
        f"main_category_name == '{main_cate}' and sub_category_name =='{sub_cate}'"
    )
    color = "sub_sub_category_name"

var_sel = st.radio("Choose Values:", ["Absolute", "Relative"], index=1)

map_var_sel = {"Absolute": "average_price", "Relative": "normal"}[var_sel]

# plot_df = plot_df.sort_values("normal", ascending=False)
# plot_df = plot_df.head(10)
fig = px.line(plot_df, x="day", y=map_var_sel, color=color, width=1000, height=600)
st.plotly_chart(fig)
