
# VRM Script Toolbox

Lightweight CLI tool to automate Veracode Risk Manager tasks using HMAC authentication.

## Features
- Uses Veracode HMAC authentication with REST API + GraphQL API  
- Auto-creates VRM Applications & links Veracode Application Profile Assets (1-to-1 mapping)  
- Reads credentials from standard Veracode credentials file (`~/.veracode/credentials`)
- Detailed logging to file for troubleshooting  

## Prerequisites
- Python 3.6+  
- pip  
- Veracode API credentials (API ID and Secret Key)

## Installation

```bash
git clone https://github.com/ancient-cthulhu/VRM-Toolbox.git
cd VRM-Toolbox
python3 -m venv venv     # optional but recommended
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install requests veracode-api-signing
```

## Configuration

The script uses the standard Veracode credentials file. Create or edit `~/.veracode/credentials` (or `%USERPROFILE%\.veracode\credentials` on Windows):

```ini
[default]
veracode_api_key_id = YOUR_API_KEY_ID
veracode_api_key_secret = YOUR_API_KEY_SECRET
```

### Getting API Credentials

Generate your Veracode API credentials at:  
https://web.analysiscenter.veracode.com/app/api-credentials

**Note**: Ensure your API credentials have the necessary permissions for Veracode Risk Manager.

## Usage

```bash
python script.py
```

### Menu Options

1. **Create & link VRM Applications to Veracode Application Profiles (1 to 1)**
   - Fetches all Veracode Application Profile assets
   - Creates a VRM Application for each asset with matching name
   - Links each asset to its corresponding application (1-to-1 relationship)
   
2. **Exit**

## How It Works

The script performs the following steps:

1. **Authenticate**: Uses HMAC authentication with credentials from `~/.veracode/credentials`
2. **Fetch Assets**: Retrieves all assets from VRM using GraphQL
3. **Filter**: Identifies only "Veracode Application Profile" type assets
4. **Create Applications**: For each asset, creates a new VRM Application with the same name
5. **Link Assets**: Links each asset to its corresponding application using the asset's URI

### Example Output

```
Using Veracode API credentials from ~/.veracode/credentials
To generate API credentials, go to: https://web.analysiscenter.veracode.com/login/#APICredentialsGenerator

============================================================
VRM Script Toolbox
============================================================
1) Create and link VRM Applications to Veracode App-profiles (1 to 1)
2) Exit
============================================================
Select an option: 1

Processing: MyApp
  → Creating VRM Application 'MyApp'...
  ✓ Created (ID: abc123...)
  → Linking asset to application...
  ✓ Linked

============================================================
Summary: 21 apps created, 21 assets linked
============================================================
```

## Logging

All operations are logged to `vrm_script.log` in the same directory. The log file includes:
- API requests and responses
- Success/failure status
- Error details for troubleshooting

Console output is kept clean and user-friendly, while detailed logs are available in the log file.

## Customization

- **Pagination**: Edit `ASSETS_VARS` (default: 100 assets per page)
  ```python
  ASSETS_VARS = {"pageNumber": 1, "pageSize": 100}
  ```
- **GraphQL Query**: Modify `ASSETS_QUERY` to fetch additional asset fields
- **Application Properties**: Adjust the payload in `create_application()` to set owner, description, or application value
  ```python
  payload = {
      "name": name,
      "owner": "",  # Customize this
      "applicationValue": "UNKNOWN"  # Or "MEDIUM", "LOW", "UNKNOWN"
  }
  ```

## Error Handling

The script handles:
- Missing or invalid API credentials
- GraphQL errors
- REST API failures
- Network issues

All errors are logged to `vrm_script.log` with full stack traces for debugging.

## Troubleshooting

### "No assets exist corresponding to passed filters"
- Ensure assets have valid URIs in VRM
- Check that you're using the correct asset type filter
- Verify the asset exists and is accessible with your credentials

### Authentication Errors
- Verify your API credentials are correct in `~/.veracode/credentials`
- Ensure the credentials file format is correct (see Configuration section)
- Ensure your API credentials have the necessary permissions in Veracode
- Check that the credentials file is in the correct location:
  - Linux/Mac: `~/.veracode/credentials`
  - Windows: `%USERPROFILE%\.veracode\credentials`

### Missing Credentials File
If you see an error about missing credentials, create the file:

**Linux/Mac:**
```bash
mkdir -p ~/.veracode
nano ~/.veracode/credentials
```

**Windows:**
```cmd
mkdir %USERPROFILE%\.veracode
notepad %USERPROFILE%\.veracode\credentials
```

Then add your credentials in the format shown in the Configuration section.

### Check Logs
Review `vrm_script.log` for detailed error information and API responses.

## Support

For issues or questions:
- Check the [Veracode Help Center](https://help.veracode.com/)
- Review the `vrm_script.log` file for detailed error information
- Open an issue on GitHub
 
