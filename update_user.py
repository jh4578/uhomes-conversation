import streamlit as st
import mysql.connector
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from config import DATABASE_CONFIG
import warnings
warnings.filterwarnings('ignore')
import json
    
def app():
    st.title("搜索对话")

    # Function to get database connection
    def get_db_connection():
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        return connection

    # Function to execute read query
    def execute_read_query(query=None):
        # st.write(query)
        connection = get_db_connection()
        if query is None:
            # Adjust this default query as per your requirements
            query = """
            SELECT Unit.*, Building.building_name, Building.location
            FROM Unit
            JOIN Building ON Unit.building_id = Building.building_id
            """
        df = pd.read_sql(query, connection)
        connection.close()
        return df

    # Function to execute write query (update, delete)
    def execute_write_query(query):
        # st.write(query)
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        connection.close()
    
    def sql_excecute(query, values = None):
          try:
            connection = get_db_connection()
            cursor = connection.cursor()
            if values:
                cursor.execute(query,values)
            else:
                cursor.execute(query)
            connection.commit()
          except mysql.connector.Error as err:
                  print(f"Error: {err}")
        
          finally:
              if connection.is_connected():
                  cursor.close()
                  connection.close()

    def get_chatbot_wx_ids():
        query = "SELECT DISTINCT chatbot_wx_id FROM user WHERE chatbot_wx_id IS NOT NULL"
        df = execute_read_query(query)
        return df['chatbot_wx_id'].tolist()
        
    def get_unique_building_names():
        query = "SELECT DISTINCT building_name FROM Unit"
        df = execute_read_query(query)
        return df['building_name'].tolist()

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
        chatbot_wx_ids = ['异乡好居-测试','H']
        chatbot_wx_id = st.selectbox("Chatbot 微信ID", chatbot_wx_ids)
        sche_listing_options = ["Any", "Yes", "No"]
        chatbot_on = st.selectbox("Chatbot_on", options=sche_listing_options)
        search_user = st.form_submit_button("显示表格")

    # Handle Search
    if search_user:
        search_query = f"""
        SELECT wechat_id, preference, chatbot_wx_id, chatbot_on, sche_listing, is_group, 
        conversation, user_id
        FROM user
        WHERE chatbot_wx_id = '{chatbot_wx_id}'
        """

        if chatbot_on != "Any":
            chatbot_on = 1 if chatbot_on == "Yes" else 0
            search_query += f" AND chatbot_on = {chatbot_on}"

        df = execute_read_query(search_query)
        def transform_conversation(query):
            if query is None:
                return 
            else:
                query = json.loads(query)
                conversation = []
                for conv in query:
                  if conv['role'] not in ['system','tool'] and conv['content'] != None:
                    content = conv['content'].replace('\n','')
                    conversation.append({conv['role']:content})
                return conversation
        df['conversation'] = df['conversation'].apply(transform_conversation)
        df['conversation'] = df['conversation'].apply(lambda x: json.dumps(x, ensure_ascii=False))

        st.write(df)
        st.session_state['search_results'] = df

    # Display Search Results
    if 'search_results' in st.session_state:
        df = st.session_state['search_results']

        # Set up AgGrid options for editable grid
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True, minWidth=150)
        gb.configure_selection('multiple', use_checkbox=True)
        grid_options = gb.build()

        # Display the grid
        grid_response = AgGrid(
            df, 
            gridOptions=grid_options,
            height=600, 
            width='100%',
            data_return_mode='AS_INPUT', 
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True
        )

        if 'data' in grid_response:
            updated_df = grid_response['data']
            if not updated_df.equals(df):
                if st.button('更新'):
                    # print(updated_df)
                       
                    df = df.reset_index(drop=True)
                    df.drop(columns = 'last_sent',inplace = True)
                    updated_df = updated_df.reset_index(drop=True)
                    updated_df.drop(columns = 'last_sent',inplace = True)
                    
                   

                    for index, row in updated_df.iterrows():
                        if not row.equals(df.loc[index]):  # 检查行是否有变更
                            update_parts = []
                            update_values = []
                            for col in updated_df.columns:
                                if col not in ['conversation','user_id'] and row[col] != df.loc[index, col]:  # 只添加变更的字段
                                    update_parts.append(f"{col} = %s")
                                    update_values.append(row[col])
                            
                            if not update_parts:
                                continue  # 如果没有要更新的字段，跳过此记录

                            st.write(update_parts)
                            st.write(update_values)
        
                            update_query = "UPDATE user SET " + ', '.join(update_parts) + " WHERE user_id = %s"
                            record = tuple(update_values) + (row['user_id'],)
                            
                            sql_excecute(update_query, record)
                    st.success("更新成功！")

            

        selected = grid_response['selected_rows']
        # print(selected)
        # print(type(selected))
        if selected is not None and len(selected) > 0:

            if st.button('删除'):
                for _, row in selected.iterrows():

                    user_delete_query = f"DELETE FROM user WHERE user_id = {row['user_id']}"
                    execute_write_query(user_delete_query)
                st.success("删除成功！")
    
    with st.form("add_user_form"):
        st.write("添加新用户")
        # 添加字段
        new_wechat_id = st.text_input("客人备注名", "")
        new_preference = st.text_input("租房需求", "")
        # new_roommate_preference = st.text_input("室友偏好", "")
        # new_sex = st.selectbox("性别", ["", "Male", "Female", "Other"])
        new_chatbot_wx_id = st.text_input("Chatbot昵称", "")
        frequency = st.number_input("推房频率", min_value=1, step=1, format='%d')
        
        building_names = get_unique_building_names()  # 从数据库获取所有唯一的楼名
        new_nobuilding = st.multiselect("不要推的大楼", options=building_names, default = [])
        chatbot_on = st.checkbox("chatbot_on",value = False)
        is_group = st.checkbox('群聊',value = False)
        
        # 提交按钮
        submit_new_user = st.form_submit_button("添加用户")
        
    if submit_new_user:
        no_building_str = ', '.join(new_nobuilding)
        # 插入新用户数据到数据库
        insert_query = f"""
        INSERT INTO user (wechat_id, preference, chatbot_wx_id, chatbot_on, is_group, no_building, frequency)
        VALUES ('{new_wechat_id}', '{new_preference}', '{new_chatbot_wx_id}', {chatbot_on}, {is_group}, '{no_building_str}',{frequency})
        """
        execute_write_query(insert_query)
        st.success("用户添加成功！")

    

if __name__ == "__main__":
    app()
