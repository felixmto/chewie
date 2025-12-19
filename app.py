import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

import base64

# Page configuration
st.set_page_config(page_title="Chewie (Academic Scout)", page_icon="🔍", layout="wide")

# Function to load and encode image
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Inject CSS for background image
def add_bg_image():
    try:
        bin_str = get_base64_of_bin_file("chewie.svg")
        page_bg_img = f"""
        <style>
        /* Force Background Color */
        .stApp, 
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main {
            background-color: #D7CCC8 !important;
            background-image: url("data:image/svg+xml;base64,{bin_str}") !important;
            background-size: 15% !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            background-position: bottom 20px right 20px !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #EFEBE9 !important;
        }
        
        /* Disable header icon fullscreen - Aggressive */
        button[title="View fullscreen"],
        [data-testid="StyledFullScreenButton"],
        [data-testid="stImage"] button {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        [data-testid="stImage"] img {
            pointer-events: none !important;
        }
        
        /* Hide sidebar collapse button - Aggressive */
        [data-testid="collapsedControl"], 
        [data-testid="stSidebarCollapsedControl"],
        section[data-testid="stSidebar"] > button,
        button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            width: 0 !important;
        }
        
        /* Compact sidebar layout */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* Reduce widget spacing in sidebar */
        section[data-testid="stSidebar"] .stElement {
            margin-bottom: 0.2rem !important;
        }
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except Exception:
        pass # Fail silently if image not found

add_bg_image()

# OpenAlex API base URL
OPENALEX_API = "https://api.openalex.org/works"

# University mappings to OpenAlex institution IDs and display names
UNIVERSITY_IDS = {
    "UC Berkeley": ["I95457486", "I148283060"],   # UC Berkeley + Lawrence Berkeley National Lab
    "UC Berkeley & UCSF": ["I95457486", "I148283060", "I180670191"], # UC Berkeley + LBL + UCSF
    "Stanford": ["I4200000001"],    # Stanford University
    "MIT": ["I127595847"],          # Massachusetts Institute of Technology
    "Harvard": ["I136199984"]       # Harvard University
}

UNIVERSITY_DISPLAY_NAMES = {
    "UC Berkeley": "University of California, Berkeley",
    "Stanford": "Stanford University",
    "MIT": "Massachusetts Institute of Technology",
    "Harvard": "Harvard University"
}

# VIP Authors List
VIP_AUTHORS = {
    "Chunlei Liu", "Jennifer Listgarten", "Jun-Chau Chien", "Jack Gallant", 
    "Preeya Khanna", "Doris Tsao", "William Jagust", "Gül Dölen", 
    "Richard Ivry", "Markita Landry", "John G. Flannery", "James Olzmann", 
    "Roberto Zoncu", "Fyodor Urnov", "James Nuñez", "Margaux Pinney", 
    "Kathleen Collins", "Xavier Darzacq", "Michael Rape", "David Schaffer", 
    "Ehud Isacoff", "David Nguyen", "Doug Koshland", "Robert Tjian", 
    "Daniel Portnoy", "David Savage", "Peter Sudmant", "Britt Glaunsinger", 
    "Andrea Gomez", "Robert Saxton", "Jennifer A. Doudna", "Daniel K. Nomura", 
    "Ashok Ajoy", "Kevan Shokat", "Peidong Yang", "Matthew B. Francis", 
    "Jennifer Bergner", "Jay T. Groves", "Omar Yaghi", "Karthik Shekhar", 
    "Rebecca Bart", "Adam Arkin", "Kevin Healy", "Phillip Messersmith", 
    "John Dueber", "Dorian Liepmann", "Derfogail Delcassian", "Rikky Muller"
}

def get_recent_papers(university_id, author_names, days_back, university_display_name=None):
    """
    Queries OpenAlex for papers by specific authors at a specific institution
    from the last X days using a two-step approach:
    1. Find author IDs by searching authors endpoint
    2. Use author IDs to find their works
    """
    # Calculate the date (YYYY-MM-DD) - 90 days ago
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Clean up author names
    authors_list = [name.strip() for name in author_names.split(',') if name.strip()]
    
    
    if not authors_list:
        return pd.DataFrame(), []
    
    # Handle university_id being a list or string
    if isinstance(university_id, str):
        university_ids = [university_id]
    else:
        university_ids = university_id
    
    # Create pipe-separated string for OR query
    institutions_str = "|".join(university_ids)

    # STEP 1: Get Author IDs
    author_ids = []
    missing_authors = []
    authors_url = "https://api.openalex.org/authors"
    
    for author_name in authors_list:
        found_match = False
        try:
            # Smart Search:
            # 1. Search by Last Name (most specific token)
            # 2. Filter results by checking if all parts of the input name exist in the result name
            
            name_parts = author_name.strip().split()
            if not name_parts:
                continue
                
            last_name = name_parts[-1]
            
            # Using 'last_known_institutions.id' (plural) as per OpenAlex API
            # Search for the Last Name to cast a wide net, then filter
            params = {
                'filter': f'display_name.search:{last_name},last_known_institutions.id:{institutions_str}',
                'per_page': 50
            }
            
            response = requests.get(authors_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if results:
                # Filter results: Check if all parts of the input name match
                for result in results:
                    display_name = result.get('display_name', '')
                    # Case-insensitive check if all parts of input name are in the display name
                    if all(part.lower() in display_name.lower() for part in name_parts):
                        author_id = result.get('id')
                        if author_id:
                            author_ids.append(author_id)
                            found_match = True
            
            if not found_match:
                missing_authors.append(author_name)
                
        except requests.exceptions.RequestException as e:
            # Handle 400 Bad Request specifically to generic warning if needed, but the fix should prevent it
            # st.warning(f"Error searching for author '{author_name}': {str(e)}")
            missing_authors.append(author_name)
            continue
    
    if not author_ids:
        return pd.DataFrame(), missing_authors
    
    
    # STEP 2: Get Papers using Author IDs
    works_url = "https://api.openalex.org/works"
    
    all_works = []
    # Batch size to prevent URL length errors (400 Bad Request)
    # OpenAlex allows OR queries but long URLs fail. 25-50 is a safe chunk size.
    chunk_size = 25
    
    for i in range(0, len(author_ids), chunk_size):
        chunk_ids = author_ids[i:i + chunk_size]
        author_ids_str = "|".join(chunk_ids)
        
        # Filter by author IDs, publication date, and institution
        filter_str = (
            f"authorships.author.id:{author_ids_str},"
            f"authorships.institutions.id:{institutions_str},"
            f"publication_date:>{start_date}"
        )
        
        params = {
            'filter': filter_str,
            'sort': 'publication_date:desc',
            'per_page': 200
        }
        
        try:
            response = requests.get(works_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            all_works.extend(data.get('results', []))
            
        except requests.exceptions.RequestException as e:
            st.warning(f"Error fetching batch of works: {str(e)}")
            continue

    # Process all results
    works = all_works
        
    # Format results
    results = []
    
    for work in works:
        title = work.get('display_name', 'Untitled')
        pub_date = work.get('publication_date', 'Unknown')
        
        # Check authorship for VIPs to highlight title
        is_vip_paper = False
        authorships = work.get('authorships', [])
        
        # Check if any author on the paper matches our VIP list
        for authorship in authorships:
            auth_name = authorship.get('author', {}).get('display_name') or ''
            if any(vip_name.lower() in auth_name.lower() for vip_name in VIP_AUTHORS):
                is_vip_paper = True
                break
        
        if is_vip_paper:
            # title = "➡️ " + title # Reverted as per user request
            pass
        
        # Get journal name
        location = work.get('primary_location') or {}
        source = location.get('source') or {}
        journal = source.get('display_name', 'Unknown Journal')
        
        # Get link
        link = location.get('landing_page_url') or work.get('doi') or '#'
        
        # Format authors
        author_names_list = [a.get('author', {}).get('display_name', 'Unknown') for a in authorships]
        author_str = ", ".join(author_names_list[:3])
        if len(authorships) > 3:
            author_str += " et al."
        
        results.append({
            "Title": title,
            "Authors": author_str,
            "Date": pub_date,
            "Journal": journal,
            "Link": link,
            "_is_vip": is_vip_paper # Hidden column for styling
        })
    
    df = pd.DataFrame(results)
    if not df.empty:
        # Deduplicate: Keep earliest version
        # 1. Sort by Date ascending (oldest first)
        df = df.sort_values('Date', ascending=True)
        # 2. Drop duplicates on Title+Authors, keeping the first (oldest)
        df = df.drop_duplicates(subset=['Title', 'Authors'], keep='first')
        # 3. Sort by Date descending (newest first) for final display
        df = df.sort_values('Date', ascending=False)

    return df, missing_authors

# Main app
# Header with custom icon
col1, col2 = st.columns([1, 10])
with col1:
    st.image("header_icon.png", width=70)
with col2:
    st.title("Chewie (Academic Scout)")
st.markdown("Find recent papers from authors at selected universities")

# Sidebar
with st.sidebar:
    st.header("Search Parameters")
    
    # University selection
    university = st.selectbox(
        "Select University",
        options=list(UNIVERSITY_IDS.keys()),
        index=0
    )
    
    # Time Horizon selection
    time_horizon_options = {
        "1 Month": 30,
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365
    }
    
    time_horizon = st.selectbox(
        "Time Horizon",
        options=list(time_horizon_options.keys()),
        index=1  # Default to 3 Months
    )
    
    st.markdown("---")
    
    # Author names input
    st.subheader("Author Names")
    author_input = st.text_area(
        "Enter author names (one per line)",
        height=125,
        help="Enter one author name per line."
    )
    
    st.markdown("OR")
    
    # Excel file uploader
    uploaded_file = st.file_uploader("Upload Excel file with author names", type=['xlsx', 'xls'])
    if uploaded_file:
        try:
            df_authors = pd.read_excel(uploaded_file)
            if not df_authors.empty:
                # Assume first column has names
                file_authors = df_authors.iloc[:, 0].dropna().astype(str).tolist()
                st.success(f"Loaded {len(file_authors)} authors from file.")
            else:
                file_authors = []
                st.warning("Uploaded file is empty.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            file_authors = []
    else:
        file_authors = []
    
    # Search button
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# Main content area logic
if search_button:
    if not author_input.strip() and not file_authors:
        st.warning("Please enter at least one author name or upload a file.")
    else:
        # Parse author names from text area
        text_authors = [name.strip() for name in author_input.split("\n") if name.strip()]
        
        # Combine with file authors
        author_names = list(set(text_authors + [name.strip() for name in file_authors if name.strip()]))
        
        if not author_names:
            st.warning("Please enter at least one valid author name.")
        else:
            with st.spinner(f"Searching for papers from {len(author_names)} author(s) at {university} (fetching last 1 year)..."):
                university_id = UNIVERSITY_IDS[university]
                university_display_name = UNIVERSITY_DISPLAY_NAMES.get(university)
                # Convert list of author names to comma-separated string
                author_names_str = ", ".join(author_names)
                
                # ALWAYS fetch 365 days (1 Year) to allow filtering later
                df, missing_authors = get_recent_papers(university_id, author_names_str, days_back=365, university_display_name=university_display_name)
                
                # Store in session state
                st.session_state['results_df'] = df
                st.session_state['missing_authors'] = missing_authors
                st.session_state['has_searched'] = True
                
                if df.empty and not missing_authors:
                    st.info("No papers found matching your criteria in the last year.")
                elif df.empty and missing_authors:
                    st.warning("No papers found, and some authors were not found at this university.")

# Display Logic (Runs on every rerun if results exist)
if 'has_searched' in st.session_state:
    
    # --- Top Dashboard: Successful Papers ---
    st.markdown("### 📚 Recent Publications")
    
    if 'results_df' in st.session_state and not st.session_state['results_df'].empty:
        df_all = st.session_state['results_df']
        
        # Filter based on current Time Horizon selection
        days_back = time_horizon_options[time_horizon]
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Ensure Date column is datetime or string comparable
        # API returns ISO strings YYYY-MM-DD
        df_filtered = df_all[df_all['Date'] >= cutoff_date]
        
        if not df_filtered.empty:
            st.success(f"Found {len(df_filtered)} paper(s) published in the last {days_back} days!")
            
            # Display table with clickable links
            # Define highlight function
            def highlight_vip(row):
                if '_is_vip' in row and row['_is_vip']:
                    return ['background-color: #FFF9C4'] * len(row)
                return [''] * len(row)
            
            # Apply styling
            # Note: Styler object must be passed to st.dataframe
            styled_df = df_filtered.style.apply(highlight_vip, axis=1)

            # Display table with clickable links
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Link": st.column_config.LinkColumn(
                        "Link",
                        display_text="View Paper",
                        width="small"
                    ),
                    "Title": st.column_config.TextColumn(
                        "Title",
                        width="large"
                    ),
                    "Authors": st.column_config.TextColumn(
                        "Authors",
                        width="medium"
                    ),
                    "Date": st.column_config.TextColumn(
                        "Date",
                        width="small"
                    ),
                    "Journal": st.column_config.TextColumn(
                        "Journal",
                        width="medium"
                    ),
                    "_is_vip": None # Hide the helper column
                }
            )
        else:
            st.info(f"No papers found in the last {days_back} days (but {len(df_all)} found in the last year).")
    elif 'results_df' in st.session_state:
        st.info("No papers found matching the found authors.")

    # --- Bottom Dashboard: Missing Authors ---
    if 'missing_authors' in st.session_state and st.session_state['missing_authors']:
        st.markdown("---")
        st.markdown("### ❓ Unaffiliated / Missing Authors")
        
        st.warning(f"The following {len(st.session_state['missing_authors'])} author(s) were not found at **{university}** or could not be matched:")
        
        # Display as a dataframe or list
        missing_df = pd.DataFrame(st.session_state['missing_authors'], columns=["Author Name"])
        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True
        )
        
        st.caption("Tip: Check the spelling or ensure they are affiliated with the selected university in OpenAlex.")

elif 'has_searched' in st.session_state and st.session_state.get('results_df', pd.DataFrame()).empty:
    # already handled by the search block info message, but good for persistence state
    pass

else:
    if not search_button:
        st.info("👈 Use the sidebar to select a university and enter author names, then click 'Search' to find recent papers.")

