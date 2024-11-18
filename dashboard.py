import streamlit as st
import numpy as np
import pandas as pd
from io import StringIO, BytesIO

st.header("Dashboard")
file_area = st.container()
input_area = st.container(border=True,)

data=pd.DataFrame()
if 'data' not in st.session_state:
    st.session_state['data']=pd.DataFrame()
else:
    data=st.session_state['data']
## Spreadsheet


def getSpreadsheet(SPREADSHEET_ID,RANGE_NAME):
    import os.path
    import json
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    if st.secrets['GOOGLE_TOKEN']:
      creds = Credentials.from_authorized_user_info(json.loads(st.secrets['GOOGLE_TOKEN']),SCOPES)
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        print("Need to Refresh token")
        print(creds)
      else:
        print("No Token Found")
    try:
      service = build("sheets", "v4", credentials=creds)
      sheet = service.spreadsheets()
      result = (
          sheet.values()
          .get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
          .execute()
      )
      global data
      data = pd.DataFrame(result.get("values", []))
      data.columns = data.iloc[0]  # Set the first row as the header
      data = data[1:] 
      data = data.reset_index(drop=True)
      st.session_state['data']=data
    except HttpError as err:
      print(err)

## File Area
def getId(url):
    return url.split("/d/")[1].split("/edit?")[0]

# Column 1
file_col1, file_col2 = file_area.columns([3, 3])
file_col1 = file_col1.container(border=True,)
file_col2 = file_col2.container(border=True,)

file_col1_d1, file_col2_d2 = file_col1.columns([4, 2])
file_col1_d1.subheader("Spreadsheet:")
file_col1.text("Read access to anyone with link or provide access to the email: divijmahajan_co22a4_07@dtu.ac.in")
url = file_col1.text_input("Spreadsheet URL (1st row=column names):", "")
file_col1_1, file_col2_2 = file_col1.columns([1, 1])
name = file_col1_1.text_input("Sheet Name:", "")
rang = file_col2_2.text_input("Range:", "")
if file_col2_d2.button("Upload"):
    getSpreadsheet(getId(url),name+"!"+rang)
file_col1.write("or")
file_col1.subheader("Upload File:")
uploaded_file = file_col1.file_uploader("")
if uploaded_file is not None:
    st.session_state['data'] =pd.read_csv(uploaded_file)

data=st.session_state['data']
csv_buffer = BytesIO()
data.to_csv(csv_buffer, index=False, encoding='utf-8')
csv_data = csv_buffer.getvalue()

file_col2_h1, file_col2_h2 = file_col2.columns([5, 2])
file_col2_h1.download_button(
    label="Download CSV",
    data=csv_data,
    file_name='output.csv',
    mime='text/csv',
)
file_col2_h2.button("Refresh")
# Column 2
file_col2.write(data)


## Input Area
inp_col1, inp_col2 = input_area.columns([4, 1])
inp_col1.subheader("Input Query")
input_area.write("Enter your query below using {column} as a placeholder for the selected column. For example, if your column is “Company,” you might enter: “Get me the email address of {Company}” or “Find the headquarters location of {Company}.”")
query = input_area.text_input("Input Query:", "")

def expand_query(query,dic):
    return query.format(**dic)
# submit query button
if inp_col2.button("Submit Query"):
    from langchain_anthropic import ChatAnthropic
    from langchain_groq import ChatGroq
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_core.messages import HumanMessage
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage

   
    import json

    # Create the agent
    #model = ChatAnthropic(model_name="claude-3-sonnet-20240229")
    #agent_executor = create_react_agent(model, tools, checkpointer=memory)
    memory = MemorySaver()
    search = TavilySearchResults(max_results=2)
    tools = [search]
    search_model = ChatGroq(model="llama-3.1-8b-instant")
    search_executor = create_react_agent(search_model, tools,checkpointer=memory)
    config = {"configurable": {"thread_id": "abc123"}}

    summary_model = ChatGroq(model="llama-3.1-70b-versatile")
    refine_model = ChatGroq(model="llama-3.2-3b-preview")
    refine_messages = [
        (
            "system",
            "Refined the given text format it by removing any typo, expanding abbrevations (if required) and making sure the variables in '"+"{}"+f"' matches one of following columns : {str(data.columns.tolist())}, or return 'invalid string' if no column matches, return only the formatted text without any other information. Don't remove "+"{} around the variables. In case the query is in another language then English, kindly convert it into english.",
        ),
        ("human", query),
    ]
    refined_ans=summary_model.invoke(refine_messages)
    refined_query=dict(refined_ans)['content']
    print("--refined--")
    print(refined_query)
    data['query_result']=""
    data['accuracy_score']=""
    for row_index in range(len(data)):
        row=data.iloc[row_index].to_dict()
        print("--expanded--")
        print(expand_query(refined_query,row))
        for chunk in search_executor.stream(
            {"messages": [HumanMessage(content=expand_query(refined_query,row))]},config
            ):
            try:
                for k in chunk:
                    if(k=="tools"):
                        print("--summary--")
                        #print(json.loads(dict(dict(chunk)['tools']['messages'][0])['content'])[0]['url'])
                        #print(json.loads(dict(dict(chunk)['tools']['messages'][0])['content'])[0]['content'])
                        
                        messages = [
                            (
                                "system",
                                f"Given the prompt, extract just the relevant information, eliminating all other words and just the answer to the question '{refined_query}'. Also give the accuracy score from 0 to 1, in how relevant the ans seems for the question, if the ans matches correctly show '"+"{your ans}:{score}"+"', if you can't find ans at all '"+"{your ans}"+":0'. In case the information isn't in text but you still know the answer, return just the answer you know without any other text with a lower accuracy score, and in case there is no information at all, return 'No Output' and accuray score of 0",
                            ),
                            ("human", json.loads(dict(dict(chunk)['tools']['messages'][0])['content'])[0]['content']),
                        ]
                        ans = summary_model.invoke(messages)
                        s=dict(ans)['content']
                        print(s)
                        if(len(s.split(":"))>0):
                            data.loc[row_index,'query_result']=s.split(":")[0]
                            data.loc[row_index,'accuracy_score']=s.split(":")[1]
                        else:
                            data.loc[row_index,'accuracy_score']='0'

            except:pass
    st.session_state['data']=data
    print(data)
