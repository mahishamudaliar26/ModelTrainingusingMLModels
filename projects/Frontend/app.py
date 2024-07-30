import streamlit as st
from azure.storage.blob import ContainerClient
from azure.core.exceptions import ClientAuthenticationError 

# Azure Blob Storage Configuration (Dictionary)
connection_configs = {
    "Investor": {
        "connection_string": "https://storage001233.blob.core.windows.net/customers?sp=rl&st=2024-07-30T11:51:33Z&se=2024-07-30T19:51:33Z&spr=https&sv=2022-11-02&sr=c&sig=BksJNg6676v104ssD6W4aF67mOOx4l4HNJlgsGP7jM0%3D",
        "container_name": "customers"  
    },
    "Supplier": {
        "connection_string": "https://storage001233.blob.core.windows.net/investors?sp=rl&st=2024-07-30T11:52:18Z&se=2024-07-30T19:52:18Z&spr=https&sv=2022-11-02&sr=c&sig=3CxOVpNyOhtExKZxj%2B0IQU5oQl4ZjTuphsLSKEx873Q%3D",
        "container_name": "investors"
    },
    "Customer": {
        "connection_string": "https://storage001233.blob.core.windows.net/suppliers?sp=rl&st=2024-07-30T11:52:51Z&se=2024-07-30T19:52:51Z&spr=https&sv=2022-11-02&sr=c&sig=dGShvZrdn5N7E20tBKDvenofxGabUiXW%2F53HqvPh%2FLM%3D",  
        "container_name": "suppliers" 
    }
}

def get_blob_filenames(selected_tab):
    config = connection_configs.get(selected_tab)
    if config:
        try:
            container_client = ContainerClient.from_container_url(config["connection_string"]) 

            blob_list = container_client.list_blobs()
            filenames = [blob.name for blob in blob_list]
            return filenames

        except ClientAuthenticationError as e:
            st.error(f"Authorization error for {selected_tab}: {e}")
            return []  

        except Exception as e:  # Catch other potential errors
            st.error(f"Error retrieving files for {selected_tab}: {e}")
            return []  
    
    else:
        return []  # Return empty list if configuration is not found

# App Title
st.title("Sustainability Matrix")

# Create Tabs
tab_names = ["Investor", "Supplier", "Customer"]
selected_tab = st.sidebar.selectbox("Select Stakeholders", tab_names)

# Content for each Tab
if selected_tab:
    st.header(f"{selected_tab} Sustainability Assessment")
    # Dynamically fetch filenames from Azure Blob Storage
    options = get_blob_filenames(selected_tab)
    selected_files = st.multiselect(f"Select {selected_tab} Assessment Files:", options)

    if selected_files:
        # Fetch and display the content of the selected files (add logic here)
        for file in selected_files:
            st.write(f"Selected file: {file}")