import streamlit as st
import numpy as np
import pandas as pd
from io import StringIO, BytesIO

st.header("Dashboard")
file_area = st.container(border=True,)
input_area = st.container(border=True,)

## File Area

data=pd.DataFrame()
# Column 1
file_col1, file_col2 = file_area.columns([2, 3])
file_col1.subheader("File Upload")
uploaded_file = file_col1.file_uploader("Upload File:")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)

csv_buffer = BytesIO()
data.to_csv(csv_buffer, index=False, encoding='utf-8')
csv_data = csv_buffer.getvalue()
file_col1.download_button(
    label="Download CSV",
    data=csv_data,
    file_name='output.csv',
    mime='text/csv'
)
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
    row={
        "company":"Microsoft"
    }
    refine_messages = [
        (
            "system",
            "Refined the given text format it by removing any typo, expanding abbrevations (if required) and making sure the variables in '"+"{}"+f"' matches one of following columns : {str(list(row.keys()))}, or return 'invalid string' if no column matches, return only the formatted text without any other information. Don't remove "+"{} around the variables",
        ),
        ("human", query),
    ]
    refined_ans=summary_model.invoke(refine_messages)
    refined_query=dict(refined_ans)['content']
    print("--refined--")
    print(refined_query)
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
                            f"Given the prompt, extract just the relevant information, eliminating all other words and just the answer to the question '{refined_query}'. Also give the accuracy score from 0 to 1, in how relevant the ans seems for the question, if the ans matches correctly show '"+"{your ans}"+":1', if you can't find ans at all '"+"{your ans}"+":0'",
                        ),
                        ("human", json.loads(dict(dict(chunk)['tools']['messages'][0])['content'])[0]['content']),
                    ]
                    ans = summary_model.invoke(messages)
                    print(dict(ans)['content'])
        except:pass
