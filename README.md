# Daily Menu Scraper Lambda Function

A serverless AWS Lambda function that scrapes daily menu data from Metz Culinary Management's Nutritics platform and generates an HTML page displaying the daily menu for Main Plate and Global Kitchen offerings.

## Overview

This Lambda function automatically:
- Fetches menu data from Nutritics based on the current date
- Scrapes food items with nutritional information and allergen data
- Generates a responsive HTML page with the daily menu
- Uploads the HTML file to an S3 bucket for web hosting

## Features

- **Automated Daily Menu Scraping**: Fetches menu data for the current day
- **Multi-Menu Support**: Handles both Main Plate (Lunch/Dinner) and Global Kitchen menus
- **Food Filtering**: Excludes specified food items (pizza, scallions, peppers)
- **Nutritional Information**: Displays calories, carbs, proteins, and fat content
- **Allergen Information**: Shows food allergens and properties
- **Responsive Design**: Mobile-friendly HTML output
- **S3 Integration**: Automatic upload to S3 bucket for web hosting

## Menu Schedule

- **Main Plate**: Available Monday through Sunday (Lunch & Dinner)
- **Global Kitchen**: Available Monday through Thursday only

## Environment Variables

The following environment variables must be set in your Lambda function:

| Variable | Description | Example |
|----------|-------------|---------|
| `PARENT_URL` | Base URL for the Nutritics menu system | `https://www.nutritics.com/menu/ma4003` |
| `PHOTO_URL_PREFIX` | URL prefix for food images | `https://example.com/images/` |
| `BUCKET_NAME` | S3 bucket name for HTML file storage | `my-menu-bucket` |

## File Structure

```
.
├── lambda/                   # Lambda function directory
│   ├── lambda_function.py    # Main Lambda function code
│   └── requirements.txt      # Lambda dependencies
├── README.md                 # This documentation
├── .gitignore               # Git ignore rules
```

## Dependencies

- `requests` - HTTP library for web scraping
- `beautifulsoup4` - HTML parsing library
- `boto3` - AWS SDK for Python (S3 operations)
- `datetime` - Date/time operations
- `re` - Regular expressions
- `os` - Environment variable access

## Function Flow

1. **Date Calculation**: Determines the current date and calculates the most recent Monday
2. **Menu ID Extraction**: Scrapes the parent URL to find menu IDs for the current week
3. **Data Scraping**: Fetches food data from each menu using BeautifulSoup
4. **Data Processing**: Filters foods, extracts nutritional info and allergens
5. **HTML Generation**: Creates a responsive HTML page with the menu data
6. **S3 Upload**: Uploads the generated HTML file to the specified S3 bucket

## Key Functions

### `get_most_recent_monday()`
Calculates the most recent Monday date for menu week identification.

### `get_menu_ids(parent_url, prefixes)`
Extracts menu IDs from the parent Nutritics page based on date and menu type.

### `get_food_data(elements)`
Processes BeautifulSoup elements to extract food information including:
- Name, calories, carbs, proteins, fat
- Photo URL
- Allergen information

### `write_food_data(f, meal_of_day, food_data)`
Generates HTML table rows for each meal category.

### `lambda_handler(event, context)`
Main Lambda entry point that orchestrates the entire process.

## HTML Output Features

- **Responsive Design**: Adapts to mobile and desktop screens
- **Professional Styling**: Custom CSS with Google Fonts (Anton)
- **Nutritional Tables**: Organized display of food items and nutrition data
- **Allergen Warnings**: Clear display of allergen information
- **Image Display**: Food photos with responsive sizing
- **Footer Links**: Links to original menu and developer contact

## Deployment

### Prerequisites
- AWS Lambda function configured
- S3 bucket created and accessible
- IAM role with S3 write permissions
- Environment variables configured
- AWS CLI installed (optional, for automated deployment)

### Manual Deployment
1. Navigate to the lambda directory:
   ```bash
   cd lambda
   ```

2. Install dependencies in the lambda directory:
   ```bash
   pip install -r requirements.txt -t .
   ```

3. Create deployment package:
   ```bash
   zip -r ../lambda-deployment.zip . -x "*.pyc" "__pycache__/*" "*.git*"
   ```

4. Upload to AWS Lambda:
   ```bash
   aws lambda update-function-code \
     --function-name daily-menu-scraper \
     --zip-file fileb://lambda-deployment.zip
   ```

### Lambda Configuration
- **Function Name**: `daily-menu-scraper` (or your preferred name)
- **Handler**: `lambda_function.lambda_handler`
- **Runtime**: Python 3.9 or later
- **Timeout**: 60 seconds (recommended)
- **Memory**: 256 MB (recommended)

### IAM Permissions Required
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

## Scheduling

The function can be scheduled using:
- **CloudWatch Events**: For daily execution
- **EventBridge**: For more complex scheduling
- **Manual Invocation**: For testing and one-off runs

Recommended schedule: Daily at 6:00 AM to capture updated menu data.

## Error Handling

The function includes error handling for:
- HTTP request failures
- Missing menu data
- S3 upload errors
- Environment variable validation

## Output

The function generates:
- `daily_menu.html`: Complete HTML page with daily menu
- S3 upload confirmation
- CloudWatch logs for monitoring and debugging

## Customization

### Adding New Menus
Modify the `prefixes` dictionary in `lambda_handler()` to include additional menu types.

### Excluding Foods
Update the `FOODS_TO_EXCLUDE` set in `get_food_data()` to filter additional items.

### Styling Changes
Modify the CSS within the HTML template in `lambda_handler()` for custom styling.

## Support

For issues or questions:
- Check CloudWatch logs for error details
- Verify environment variables are set correctly
- Ensure S3 bucket permissions are configured properly
- Validate the Nutritics URL structure hasn't changed

## License

This is a personal project for educational purposes. Please respect the terms of service of the scraped websites.

## Disclaimer

This is a personal website featuring Main Plate Lunch/Dinner and Global Menu only. The developer does not take responsibility for accuracy. Please verify allergen information with cafeteria staff as shared kitchen prep may cause cross-contact with allergens.
