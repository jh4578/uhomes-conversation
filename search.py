import streamlit as st
import mysql.connector
import pandas as pd
from config import DATABASE_CONFIG

def app():
    st.title("查询推房记录")
    def delete_record(user_wechat_id, chatbot_wechat_id):
        if user_wechat_id and chatbot_wechat_id:
            query = "DELETE FROM Unit_user WHERE user_wechat_id = %s AND chatbot_wechat_id = %s"
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute(query, (user_wechat_id, chatbot_wechat_id))
            connection.commit()  # 不要忘记提交更改
            connection.close()
            st.success("记录已删除")  # 反馈删除操作成功


    # Function to get database connection
    def get_db_connection():
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection

    def get_chatbot_wx_ids():
        query = "SELECT DISTINCT chatbot_wx_id FROM user WHERE chatbot_wx_id IS NOT NULL"
        connection = get_db_connection()
        df = pd.read_sql(query, connection)
        connection.close()
        return df['chatbot_wx_id'].tolist()

    # Function to fetch user_wechat_ids for a given chatbot_wechat_id
    def fetch_user_wechat_ids(chatbot_wechat_id):
        if chatbot_wechat_id:
            query = "SELECT DISTINCT user_wechat_id FROM Unit_user WHERE chatbot_wechat_id = %s"
            connection = get_db_connection()
            df = pd.read_sql(query, connection, params=(chatbot_wechat_id,))
            connection.close()
            return df['user_wechat_id'].tolist()
        return []

    # Initialize or update session state for user_wechat_ids
    if 'user_wechat_ids' not in st.session_state:
        st.session_state['user_wechat_ids'] = []

    with st.form("search_form"):
        chatbot_wx_ids = get_chatbot_wx_ids()
        chatbot_wechat_id = st.selectbox("Chatbot 微信ID", ['Any'] + chatbot_wx_ids)
        fetch_ids = st.form_submit_button("加载客户微信备注")

    if fetch_ids and chatbot_wechat_id:
        # Fetch and update the user_wechat_ids based on chatbot_wechat_id
        user_wechat_ids = fetch_user_wechat_ids(chatbot_wechat_id)
        st.session_state['user_wechat_ids'] = user_wechat_ids

    if st.session_state['user_wechat_ids']:
        selected_user_wechat_id = st.selectbox("客户微信备注", st.session_state['user_wechat_ids'])
        if st.button("搜索"):
            query = """
            SELECT Unit.building_name, Unit.unit_number, Unit.rent_price, Unit.floorplan, Unit.available_date
            FROM Unit_user
            JOIN Unit ON Unit_user.unit_id = Unit.unit_id
            WHERE Unit_user.user_wechat_id = %s AND Unit_user.chatbot_wechat_id = %s
            """
            connection = get_db_connection()
            df = pd.read_sql(query, connection, params=(selected_user_wechat_id, chatbot_wechat_id))
            connection.close()
            st.write(df)
            
        if st.button("删除记录"):
            # 调用删除记录的函数
            delete_record(selected_user_wechat_id, chatbot_wechat_id)
            # 更新 session state 中的 user_wechat_ids，因为记录已被删除
            user_wechat_ids = fetch_user_wechat_ids(chatbot_wechat_id)
            st.session_state['user_wechat_ids'] = user_wechat_ids

if __name__ == "__main__":
    app()
