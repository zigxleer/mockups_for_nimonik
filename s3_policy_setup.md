# S3 Bucket Policy Setup Guide

## Finding Your AWS Information

### Find Your Account ID:
1. AWS Console → Click your username (top right) → Account
2. Or run: `aws sts get-caller-identity`

### Find Your IAM User ARN:
Run this command:
```bash
aws sts get-caller-identity
```

Output will show:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

## Setting Up S3 Bucket Policy

### Step 1: Allow Public Access Settings

1. Go to **AWS Console → S3 → Your Bucket**
2. Click **Permissions** tab
3. Click **Edit** under "Block public access"
4. **Uncheck** "Block all public access"
5. Click **Save changes**

### Step 2: Add Bucket Policy

1. Still in **Permissions** tab
2. Scroll to **Bucket policy**
3. Click **Edit**
4. Paste this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowUploadFromApp",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/YOUR-IAM-USERNAME"
            },
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

5. Replace the placeholders:
   - `YOUR-BUCKET-NAME` → Your bucket name
   - `YOUR-ACCOUNT-ID` → Your 12-digit account ID
   - `YOUR-IAM-USERNAME` → Your IAM user name

6. Click **Save changes**

## Alternative: Simple Policy (Allow Any AWS User)

If you want to allow uploads from any authenticated AWS user with credentials:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

Then handle permissions via IAM user policy instead (see below).

## IAM User Policy (Alternative Approach)

Instead of bucket policy, you can attach this policy directly to your IAM user:

1. Go to **IAM → Users → Your User**
2. Click **Add permissions** → **Attach policies directly**
3. Click **Create policy** → **JSON**
4. Paste:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}
```

5. Name it something like `MockupsCloudS3Access`
6. Attach to your IAM user

## CORS Configuration (Required for Web Access)

If you're accessing uploaded files from a web browser, add CORS:

1. Go to **Permissions** tab
2. Scroll to **Cross-origin resource sharing (CORS)**
3. Click **Edit**
4. Paste:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD",
            "PUT",
            "POST"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": [
            "ETag"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

5. Click **Save changes**

## Testing Your Setup

After configuring, test with:

```bash
# Check if you can upload
aws s3 cp test.html s3://YOUR-BUCKET-NAME/test.html --acl public-read

# Check if file is publicly accessible
curl https://YOUR-BUCKET-NAME.s3.amazonaws.com/test.html
```

## Troubleshooting

### "Access Denied" when uploading:
- Check IAM user has PutObject permission
- Verify bucket policy allows your IAM user ARN
- Ensure AWS credentials in .env are correct

### Files upload but return 403 when accessed:
- Check "Block public access" is disabled
- Verify bucket policy has the public GetObject statement
- Ensure files are uploaded with ACL='public-read'

### "Invalid principal" error in bucket policy:
- Double-check your Account ID format (12 digits, no spaces)
- Verify IAM username is correct
- Ensure ARN format is: `arn:aws:iam::123456789012:user/username`

## Security Best Practices

1. **Use specific IAM users** instead of root account
2. **Enable MFA** on your AWS account
3. **Rotate access keys** regularly
4. **Use environment variables** for credentials (never hardcode)
5. **Consider using IAM roles** if running on EC2/ECS
6. **Limit bucket policy** to specific paths if possible:
   ```json
   "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/mockups/*"
   ```

## Quick Setup Checklist

- [ ] Disable "Block all public access" on bucket
- [ ] Add bucket policy with public GetObject
- [ ] Add bucket policy or IAM policy for PutObject
- [ ] Configure CORS settings
- [ ] Test upload with AWS CLI or app
- [ ] Verify public URL works in browser
- [ ] Confirm credentials are in .env file
