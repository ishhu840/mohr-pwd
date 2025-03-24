import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

hide_share_button = """
    <style>
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_share_button, unsafe_allow_html=True)

# --- Authentication ---
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 Login Required")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username == "mohr" and password == "mohr2025":  # Change credentials as needed
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()  # Refresh the app
            else:
                st.error("Invalid username or password")

        st.stop()  # Prevent further execution until login

check_login()  # Call the login function before proceeding

# Load the dataset
disabled_df = pd.read_excel(
    io='CRPD Final All Data.xlsx',
    engine='openpyxl',
    sheet_name='Final Data', 
    skiprows=0,
    usecols='A:L',
    nrows=200000, 
)

# Clean up column names
disabled_df.columns = disabled_df.columns.str.strip()

# Function to calculate age
def calculate_age(dob):
    try:
        today = datetime.today()
        
        if pd.isna(dob) or dob == '':
            return None
        
        if isinstance(dob, str):
            dob = dob.replace('.', '-').strip()
            
            if dob.isdigit():
                if len(dob) == 4:
                    return today.year - int(dob)
                elif len(dob) == 5:
                    last_two_digits = int(dob[-2:])
                    birth_year = 1900 + last_two_digits if last_two_digits > 30 else 2000 + last_two_digits
                    return today.year - birth_year
            
            for fmt in ("%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d", "%y-%m-%d"):
                try:
                    dob = datetime.strptime(dob, fmt)
                    break
                except ValueError:
                    continue
        
        if isinstance(dob, (int, float)):
            dob = int(dob)
            if 1900 <= dob <= today.year:
                return today.year - dob
            elif 30 <= dob <= 99:
                birth_year = 1900 + dob if dob > 30 else 2000 + dob
                return today.year - birth_year
        
        age = today.year - dob.year
        if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
            age -= 1
        return age
    except:
        return None

# Apply age calculation
disabled_df['Age'] = disabled_df['Date of Birth'].apply(calculate_age)
disabled_df['Age'] = disabled_df['Age'].fillna('Unknown')

# Categorize age
def categorize_age(age):
    if age == 'Unknown':
        return 'Unknown'
    elif age < 17:
        return 'Under 17'
    elif 18 <= age <= 60:
        return '18 to 60'
    else:
        return 'Above 60'

disabled_df['Age Group'] = disabled_df['Age'].apply(categorize_age)

# Normalize gender
disabled_df['Gender'] = disabled_df['Gender'].apply(lambda x: 'Male' if x == 'M' else ('Female' if x == 'F' else 'Unknown') if pd.notna(x) else 'Unknown')

# Create Islamabad filter
def is_islamabad(address):
    if pd.isna(address):
        return False
    address = str(address).lower()
    return 'islamabad' in address or any(s in address for s in ['g-', 'f-', 'i-', 'h-', 'e-', 'd-', 'b-', 'c-'])

disabled_df['In Islamabad'] = disabled_df.apply(lambda row: is_islamabad(row['Present Address']) or is_islamabad(row['Permanent Address']), axis=1)

# Normalize Registration Type
disabled_df['Reg'] = disabled_df['Reg'].astype(str).str.strip().str.upper()

# Sidebar filters
st.sidebar.header("Filter Data")
age_group = st.sidebar.selectbox("Select Age Group", ['All', 'Under 17', '18 to 60', 'Above 60'])
gender = st.sidebar.selectbox("Select Gender", ['All', 'Male', 'Female', 'Unknown'])
location_filter = st.sidebar.checkbox("Show Only Islamabad Residents")
reg_type = st.sidebar.selectbox("Select Registration Type", ['All', 'CRPD', 'NCRPD'])
education_level = st.sidebar.selectbox("Select Education Level", ['All'] + disabled_df['Qualification'].dropna().unique().tolist())

# Apply filters
filtered_df = disabled_df.copy()
if age_group != 'All':
    filtered_df = filtered_df[filtered_df['Age Group'] == age_group]
if gender != 'All':
    filtered_df = filtered_df[filtered_df['Gender'] == gender]
if location_filter:
    filtered_df = filtered_df[filtered_df['In Islamabad']]
if reg_type != 'All':
    filtered_df = filtered_df[filtered_df['Reg'].str.contains(reg_type, case=False, na=False)]
if education_level != 'All':
    filtered_df = filtered_df[filtered_df['Qualification'] == education_level]

# Display statistics
st.subheader("Total Disabled Individuals and Age Groups")
st.write(f"**Total number of disabled individuals:** {len(filtered_df)}")
st.write(f"**Under 17:** {len(filtered_df[filtered_df['Age Group'] == 'Under 17'])}")
st.write(f"**18 to 60:** {len(filtered_df[filtered_df['Age Group'] == '18 to 60'])}")
st.write(f"**Above 60:** {len(filtered_df[filtered_df['Age Group'] == 'Above 60'])}")

# Age distribution graph
st.subheader(" Age Distribution")
filtered_age_counts = filtered_df['Age Group'].value_counts()
st.bar_chart(filtered_age_counts)

# Gender distribution graph
st.subheader(" Gender Distribution")
st.bar_chart(filtered_df['Gender'].value_counts())

# Marital status graph
st.subheader(" Marital Status Distribution")
st.bar_chart(filtered_df['Married/Unmarried'].value_counts())

# Education level graph
st.subheader(" Education Level Distribution")
st.bar_chart(filtered_df['Qualification'].value_counts())

# Disability type graph (Sorted and Improved)
st.subheader(" Disability Type Distribution")

disability_counts = filtered_df['Disability'].value_counts().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x=disability_counts.values, y=disability_counts.index, palette="viridis", ax=ax)

ax.set_xlabel("Count")
ax.set_ylabel("Disability Type")
ax.set_title("Disability Type Distribution")

for i in ax.patches:
    ax.text(i.get_width() + 1, i.get_y() + 0.5, str(int(i.get_width())), ha='left', va='center')

st.pyplot(fig)

# Show full dataset (optional)
if st.checkbox("Show Raw Data"):
    st.dataframe(filtered_df)

