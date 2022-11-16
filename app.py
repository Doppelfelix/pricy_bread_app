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
placeholder = st.container()
st.title("Pricy Bread 💵🍞")
st.markdown(
    """This graph let's you analyze the price development of a large German supermarket since June 1st 2022. 
You can select different levels of categories.
The prices represent the average prices of products in a given category.
"""
)

if "df_main" not in st.session_state:

    with st.spinner("Loading database . . ."):

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
    "Select level",
    options=["Main Categories", "Sub Categories", "Sub Sub Categories"],
    index=1,
)

if select_level == "Main Categories":
    plot_df = df_main
    color = "main_category_name"
elif select_level == "Sub Categories":
    main_cate = st.selectbox(
        "Choose main category", options=df_sub.main_category_name.unique(), index=2
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

var_sel = st.radio("Choose Prices:", ["Absolute", "Relative"], index=1, horizontal=True)

map_var_sel = {"Absolute": "average_price", "Relative": "normal"}[var_sel]
y_title = {
    "Absolute": "Price (€)",
    "Relative": "Relative Price (100% = June 1st 2022)",
}[var_sel]
y_tick_format = {
    "Absolute": "linear",
    "Relative": ".0%",
}[var_sel]


categories_to_show = plot_df.sort_values("normal", ascending=False)[color].unique()[:5]

fig = px.line(plot_df, x="day", y=map_var_sel, color=color, width=1000, height=600)
fig.update_xaxes(title_text="")
fig.update_yaxes(title_text=y_title)
fig.update_layout(yaxis_tickformat=y_tick_format)
fig.update_layout(legend_title_text="Category Name")
fig.update_layout(
    margin=dict(l=0, r=20, t=20, b=20),
)


fig.for_each_trace(
    lambda trace: trace.update(visible="legendonly")
    if trace.name not in categories_to_show
    else ()
)
st.plotly_chart(fig)
st.info(
    "You can enable more categories by clicking on the legend name on the right",
    icon="💡",
)
