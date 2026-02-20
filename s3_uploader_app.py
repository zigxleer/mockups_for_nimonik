import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import re
from urllib.parse import quote

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Mockups Cloud",
    page_icon="☁️",
    layout="centered"
)

# Initialize S3 client
@st.cache_resource
def get_s3_client():
    """Initialize and return S3 client using environment variables"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        return s3_client
    except Exception as e:
        st.error(f"Failed to initialize S3 client: {str(e)}")
        return None

def extract_folder_from_html(html_content):
    """Extract folder name from stylesheet href in HTML"""
    try:
        # Look for <link rel="stylesheet" href="...">
        pattern = r'<link[^>]+rel\s*=\s*["\']stylesheet["\'][^>]+href\s*=\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, html_content, re.IGNORECASE)

        if not matches:
            # Try reverse order: href before rel
            pattern = r'<link[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]+rel\s*=\s*["\']stylesheet["\']'
            matches = re.findall(pattern, html_content, re.IGNORECASE)

        if matches:
            # Get the first stylesheet href
            href = matches[0]
            # Extract directory path from href
            # e.g., "Register/style.css" -> "Register"
            folder = os.path.dirname(href)
            if folder and folder != '.':
                # Remove leading/trailing slashes and ./ prefix
                folder = folder.strip('/')
                if folder.startswith('./'):
                    folder = folder[2:]
                if folder.startswith('.\\'):
                    folder = folder[2:]
                return folder
    except Exception as e:
        st.warning(f"Could not parse folder from HTML: {str(e)}")

    return None

def upload_file_to_s3(s3_client, file_path, bucket_name, s3_key):
    """Upload a single file to S3 (public access via bucket policy)"""
    try:
        # Determine content type based on file extension
        extra_args = {}

        if file_path.endswith('.html') or file_path.endswith('.htm'):
            extra_args['ContentType'] = 'text/html'
        elif file_path.endswith('.css'):
            extra_args['ContentType'] = 'text/css'
        elif file_path.endswith('.js'):
            extra_args['ContentType'] = 'application/javascript'
        elif file_path.endswith('.json'):
            extra_args['ContentType'] = 'application/json'
        elif file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            # Let boto3 auto-detect image types
            pass

        s3_client.upload_file(
            file_path,
            bucket_name,
            s3_key,
            ExtraArgs=extra_args if extra_args else None
        )
        return True
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return False
    except NoCredentialsError:
        st.error("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        return False
    except ClientError as e:
        st.error(f"Failed to upload {s3_key}: {str(e)}")
        return False

def get_public_url(bucket_name, s3_key, region='us-east-1'):
    """Generate public URL for uploaded file with proper encoding"""
    # URL-encode the s3_key to handle spaces and special characters
    encoded_key = quote(s3_key, safe='/')
    if region == 'us-east-1':
        return f"https://{bucket_name}.s3.amazonaws.com/{encoded_key}"
    else:
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{encoded_key}"

# Sidebar - Instructions and User Selection
with st.sidebar:
    st.title("Nimonik Product Mockups")

    st.markdown("### 📖 Quick Start Guide")
    st.markdown("""
    1. **Select your user** below
    2. **Upload your HTML file**
    3. **Upload folder files** (CSS, JS, images)
    4. **Click Upload to S3**
    5. **Copy and share** the URL!
    """)

    st.markdown("---")

    # User selection
    st.subheader("👤 Select User")
    user_mapping = {
        "Janelle": "Janelle_folder",
        "Lex": "Lex_folder",
        "Yurii": "Yurii_folder"
    }
    selected_user = st.selectbox(
        "Who is uploading?",
        options=["Select a user..."] + list(user_mapping.keys()),
        help="Your files will be organized in your personal folder"
    )

    if selected_user != "Select a user...":
        user_folder = user_mapping[selected_user]
        st.info(f"📂 Files → `{user_folder}/`")
    else:
        user_folder = None
        st.warning("⚠️ Please select a user to continue")

# Main app


# Check for required environment variables
bucket_name = os.getenv('S3_BUCKET_NAME')
aws_region = os.getenv('AWS_REGION', 'us-east-1')

if not bucket_name:
    st.error("⚠️ S3_BUCKET_NAME environment variable is not set!")
    st.info("Please set the following environment variables:")
    st.code("""
S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1  # Optional, defaults to us-east-1
    """)
    st.stop()

if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
    st.warning("⚠️ AWS credentials not detected. Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set.")


# File uploaders
st.subheader("Upload Files")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📄 HTML File**")
    html_file = st.file_uploader(
        "Upload your HTML file",
        type=['html', 'htm'],
        help="This file will be uploaded and a public URL will be generated"
    )

with col2:
    st.markdown("**📁 Folder Files**")
    folder_files = st.file_uploader(
        "Select all files from your folder",
        accept_multiple_files=True,
        help="Select all files you want to upload (supports CSS, JS, images, etc.)"
    )

# Check if user is selected before showing upload section
if not user_folder:
    st.info("👆 Please select a user from the sidebar to begin uploading")
    st.stop()

# Set S3 folder prefix to user's folder
s3_folder_prefix = user_folder + "/"

# Optional custom folder name
custom_folder_name = st.text_input(
    "📂 Custom folder name (optional)",
    placeholder="Leave blank to auto-detect from HTML",
    help="Override the auto-detected folder name. If blank, the folder name is extracted from the HTML stylesheet link or the HTML filename."
)
custom_folder_name = custom_folder_name.strip() or None

# Upload button
if st.button("🚀 Upload to S3", type="primary", disabled=not (folder_files or html_file)):
    if not folder_files and not html_file:
        st.warning("Please upload at least one file.")
    else:
        s3_client = get_s3_client()

        if s3_client:
            uploaded_files = []
            html_url = None

            with st.spinner("Uploading files to S3..."):
                # Determine the folder name from HTML file's stylesheet href
                html_folder_name = None
                if html_file:
                    # Read HTML content to extract folder from stylesheet link
                    html_content = html_file.read().decode('utf-8')
                    html_file.seek(0)  # Reset file pointer for later upload

                    if custom_folder_name:
                        html_folder_name = custom_folder_name
                        st.info(f"📂 Using custom folder name: '{html_folder_name}'")
                    else:
                        html_folder_name = extract_folder_from_html(html_content)

                        if html_folder_name:
                            st.info(f"📂 Detected folder name from HTML: '{html_folder_name}'")
                        else:
                            # Fallback to HTML filename without extension
                            html_folder_name = Path(html_file.name).stem
                            st.info(f"📂 Using HTML filename as folder: '{html_folder_name}'")

                # Upload folder files into a subfolder
                if folder_files:
                    effective_folder = custom_folder_name or html_folder_name
                    if effective_folder:
                        folder_path = s3_folder_prefix + effective_folder + "/"
                    else:
                        folder_path = s3_folder_prefix

                    # Upload all selected files
                    for uploaded_file in folder_files:
                        # Save file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as temp_file:
                            temp_file.write(uploaded_file.getbuffer())
                            temp_file_path = temp_file.name

                        try:
                            # Upload to the subfolder
                            s3_key = folder_path + uploaded_file.name

                            if upload_file_to_s3(s3_client, temp_file_path, bucket_name, s3_key):
                                uploaded_files.append(s3_key)
                        finally:
                            # Clean up temp file
                            os.unlink(temp_file_path)

                # Upload HTML file to root level (not in subfolder)
                if html_file:
                    # Save HTML file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
                        temp_file.write(html_file.getbuffer())
                        temp_file_path = temp_file.name

                    try:
                        s3_key = s3_folder_prefix + html_file.name
                        if upload_file_to_s3(s3_client, temp_file_path, bucket_name, s3_key):
                            uploaded_files.append(s3_key)
                            html_url = get_public_url(bucket_name, s3_key, aws_region)
                    finally:
                        # Clean up temp file
                        os.unlink(temp_file_path)

            # Display results
            if uploaded_files:
                st.success(f"✅ Successfully uploaded {len(uploaded_files)} file(s) to S3!")

                if html_url:
                    st.subheader("🔗 HTML File URL")
                    st.code(html_url, language=None)
                    st.markdown(f"[Open HTML file in new tab]({html_url})")

                with st.expander("📋 View all uploaded files"):
                    for file_key in uploaded_files:
                        file_url = get_public_url(bucket_name, file_key, aws_region)
                        st.text(file_url)
            else:
                st.error("❌ No files were uploaded successfully.")



