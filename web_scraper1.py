import requests
from bs4 import BeautifulSoup
import datetime
import re
import boto3

s3 = boto3.client('s3')
BUCKET_NAME = 'foodbucket2'
BASE_URL = 'https://www.nutritics.com/menu/ma4003'
BASE_FOOD_URL = "https://www.nutritics.com/images-user/food/168118/430x430x"

def get_most_recent_monday():
    today = datetime.datetime.today()
    most_recent_monday = today - datetime.timedelta(days=today.weekday())
    return most_recent_monday.strftime("%B %-d")

def normalize_whitespace(text):
    return ' '.join(text.split())

def get_menu_id(text):
    response = requests.get(BASE_URL)
    if response.status_code != 200:
        print(f'Failed to retrieve the parent site. Status code: {response.status_code}')
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    most_recent_monday = get_most_recent_monday()
    prefix = f"Main Plate Lunch & Dinner - {most_recent_monday}" if text is "main" else f"Global Kitchen - {most_recent_monday}"
    normalized_prefix = normalize_whitespace(prefix).lower()

    span = soup.find("span", class_="title", string=lambda text: text and normalize_whitespace(text).lower().startswith(normalized_prefix))
    
    if not span:
        print("No span with the specified text found.")
        return None

    parent_div = span.find_parent("div", class_="menu")
    if not parent_div:
        print("No parent div with the specified class found.")
        return None

    div_id = parent_div.get("id")
    return re.findall("\d+", div_id)[0]

def get_menu_data(menu_id):
    url = f'{BASE_URL}/{menu_id}'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Failed to retrieve the page. Status code: {response.status_code}')
        return None
    
    return BeautifulSoup(response.content, 'html.parser')

def get_food_data(elements):
    food_data = []
    for element in elements:
        data_name = element.get('data-name')
        data_cals = element.get('data-cals')
        data_carbs = element.get('data-carbs')
        data_proteins = element.get('data-protein')
        data_fat = element.get('data-fat')
        photo_id = element.get('data-fid')
        if data_name:
            food_url = f"{BASE_FOOD_URL}{photo_id}.jpg"
            food_data.append((data_name, data_cals, data_carbs, data_proteins, data_fat, food_url))
    return food_data

def write_food_data(f, meal_of_day, food_data):
    if food_data:
        f.write(f"<h2>{meal_of_day}</h2>")
        f.write("<table border='1' style='width: 100%;text-align: center; border-collapse: collapse;'>")
        f.write("<tr><th style='width: 30%;'>Name</th><th style='width: 17.5%;'>Image</th><th style='width: 17.5%;'>Carbs (g)</th><th style='width: 17.5%;'>Proteins (g)</th><th style='width: 17.5%;'>Fat (g)</th></tr>")
        for name, cals, carbs, proteins, fat, image_url in food_data:
            f.write(f"<tr><td><em>{name}</em><br>{cals} calories</td><td><img src='{image_url}' alt='{name}' style='width: 150px; height: 123.5px;' class='responsive-img'></td><td>{carbs}</td><td>{proteins}</td><td>{fat}</td></tr>")
        f.write("</table>")

def create_html_email(soup):
    today = datetime.datetime.now()
    formatted_date = today.strftime('%A%B%-d')
    header_date = today.strftime('%A,&nbsp %B %d')  
    title = soup.find('title').get_text()
    lunch_elements = soup.select(f'[class^="item g-{formatted_date}Lunch"]') or soup.select(f'[class^="item g-{formatted_date}Brunch"]')
    dinner_elements = soup.select(f'[class^="item g-{formatted_date}Dinner"]')
    
    lunch_data = get_food_data(lunch_elements)
    dinner_data = get_food_data(dinner_elements)
    file_path = "/tmp/daily_menu.html"
    with open(file_path, 'w') as f:
        f.write(f"""
        <!DOCTYPE html>               
        <html>
        <head>
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @media only screen and (max-width: 600px) {{
                    .responsive-img {{
                        width: 100% !important;
                        height: auto !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <h1 style='background-color: #B20838; padding: 10px; text-align: center; color: #FCB041;'>{header_date}</h1>
        """)
        
        write_food_data(f, "Lunch", lunch_data)
        write_food_data(f, "Dinner", dinner_data)
        f.write("<br><br><a href='#' style='color: #ffffff; background-color: #ff0000; padding: 10px 20px; text-decoration: none;'>Unsubscribe</a>")
    
        f.write("</body></html>")
        
        return file_path
def upload_to_s3(file_path, bucket_name, key):
    try:
        with open(file_path, 'rb') as file_data:
            s3.upload_fileobj(file_data, bucket_name, key)
        print(f"File uploaded to S3: s3://{bucket_name}/{key}")
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")

def lambda_handler(event, context):
    menu_id = get_menu_id()
    if not menu_id:
        return
    
    soup = get_menu_data(menu_id)
    if soup:
       file_path = create_html_email(soup)

       s3_key = "daily_menu.html"
       upload_to_s3(file_path, BUCKET_NAME, s3_key)

    return {
        'statusCode': 200,
        'body': f"HTML email created and uploaded to S3: s3://{BUCKET_NAME}/{s3_key}"
    }

