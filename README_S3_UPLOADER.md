# S3 Folder & HTML Uploader

A Streamlit app that uploads folders (as ZIP files) and HTML files to a public S3 bucket and returns the public URL.

## Features

- 📁 Upload entire folders (as ZIP files) to S3
- 📄 Upload HTML files and get public URLs
- ☁️ Automatically sets files as publicly readable
- 🔗 Generates direct URLs for accessing uploaded content
- 📋 Optional S3 folder path customization

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Set the following environment variables:

**Windows (Command Prompt):**
```cmd
set S3_BUCKET_NAME=your-bucket-name
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set AWS_REGION=us-east-1
```

**Windows (PowerShell):**
```powershell
$env:S3_BUCKET_NAME="your-bucket-name"
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:AWS_REGION="us-east-1"
```

**Linux/Mac:**
```bash
export S3_BUCKET_NAME=your-bucket-name
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_REGION=us-east-1
```

Or create a `.env` file (if using python-dotenv):
```
S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
```

### 3. Configure S3 Bucket

Your S3 bucket needs to be configured to allow:
1. **Public access** - Disable "Block all public access" in bucket settings
2. **Bucket Policy** - Add a policy to allow public reads:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

3. **CORS Configuration** (if accessing from web browsers):

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

### 4. IAM User Permissions

Your AWS user/credentials need the following S3 permissions:
- `s3:PutObject`
- `s3:PutObjectAcl`

Example IAM policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

## Usage

### Run the App

```bash
streamlit run s3_uploader_app.py
```

The app will open in your default browser at `http://localhost:8501`

### Upload Files

1. **Upload a Folder:**
   - Compress your folder as a ZIP file
   - Use the "Folder (as ZIP)" uploader
   - All files will be extracted and uploaded to S3

2. **Upload HTML File:**
   - Use the "HTML File" uploader
   - The app will return a public URL for direct access

3. **Optional - Set S3 Folder Path:**
   - Leave empty to upload to bucket root
   - Or specify a path like `my-project/` to organize files

4. **Click "Upload to S3"** to start the upload

### Output

- You'll see upload progress for each file
- For HTML files, you'll get a clickable public URL
- All uploaded file URLs are available in the expandable section

## Example URLs

After uploading, your files will be accessible at:
- `https://your-bucket-name.s3.amazonaws.com/your-file.html`
- `https://your-bucket-name.s3.us-east-1.amazonaws.com/folder/file.html` (for non us-east-1 regions)

## Troubleshooting

**"AWS credentials not found"**
- Make sure environment variables are set in the same terminal/session where you run Streamlit

**"Access Denied" errors**
- Check your IAM user has proper S3 permissions
- Verify bucket policy allows public access
- Ensure "Block all public access" is disabled on the bucket

**Files upload but return 403 Forbidden**
- Check bucket policy allows public GetObject
- Verify the files have public-read ACL

**CORS errors when accessing from web**
- Add CORS configuration to your S3 bucket
