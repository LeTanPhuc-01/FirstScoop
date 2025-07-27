import requests
from bs4 import BeautifulSoup
import datetime
import re
import boto3
import os

s3 = boto3.client('s3')
FILE_PATH = '/tmp/daily_menu.html'
BUCKET_NAME = os.environ.get('BUCKET_NAME')

# Modified to accept a date object for better testability
def get_most_recent_monday():
    today = datetime.datetime.today()
    most_recent_monday = today - datetime.timedelta(days=today.weekday())
    return most_recent_monday

def normalize_text(text):
    return ' '.join(text.split()).lower()

def get_menu_ids(parent_url, prefixes):
    parent_response = requests.get(parent_url)
    menu_ids = {}
    if parent_response.status_code == 200:
        soup = BeautifulSoup(parent_response.content, 'html.parser')
        most_recent_monday = get_most_recent_monday().strftime("%B %-d")
        for prefix, menu_name in prefixes.items():
            full_prefix = f"{prefix} - {most_recent_monday}"
            normalized_prefix = normalize_text(full_prefix)
            span = soup.find("span", class_="title", string=lambda text: text and normalize_text(text).startswith(normalized_prefix))
            if span:
                parent_div = span.find_parent("div", class_="menu")
                if parent_div:
                    div_id = parent_div.get("id")
                    if div_id:
                        menu_id = re.findall(r"\d+", div_id)[0]
                        menu_ids[menu_name] = menu_id
            else:
                print(f"No span with the specified text found for {menu_name}.")
    else:
        print(f'Failed to retrieve the parent site. Status code: {parent_response.status_code}')
    return menu_ids

def get_food_data(elements):
    PHOTO_URL_PREFIX = os.environ.get('PHOTO_URL_PREFIX')
    FOODS_TO_EXCLUDE = {"pizza", "scallions", "peppers"}
    food_data = []
    for element in elements:
        data_name = element.get('data-name')
        if data_name and any(word in data_name.lower() for word in FOODS_TO_EXCLUDE):
            continue
        allergens_div = element.select_one(".allergens")
        allergens = [] # Default to empty list
        if allergens_div:
            allergens = [icon.get_text(strip=True) for icon in allergens_div.select(".allergenicon")]
        print(allergens)
        data_cals = element.get('data-cals')
        data_carbs = element.get('data-carbs')
        data_proteins = element.get('data-protein')
        data_fat = element.get('data-fat')
        photo_id = element.get('data-fid')
        if data_name:
            photo_url = f"{PHOTO_URL_PREFIX}{photo_id}.jpg"
            food_data.append((data_name, data_cals, data_carbs, data_proteins, data_fat, photo_url, allergens))
    return food_data

def write_food_data(f, meal_of_day, food_data):
    if food_data:
        f.write(f"<h2>{meal_of_day}</h2>")
        f.write("<table>")
        f.write("<tr>"
                "<th class='name-column'>Name</th>"
                "<th>Image</th>"
                "<th>Carbs (g)</th>"
                "<th>Proteins (g)</th>"
                "<th>Fat (g)</th>"
                "</tr>")
        for name, cals, carbs, proteins, fat, image_url, allergens in food_data:
            allergens_str = ", ".join(allergens)
            f.write("<tr>")
            f.write(f"<td>"
                    f"<em>{name}</em><br>{cals} calories<br><br>"
                    f"<span class='allergen'>Properties: {allergens_str}</span>"
                    f"</td>")
            f.write(f"<td><img src='{image_url}' alt='{name}' class='responsive-img'></td>")
            f.write(f"<td>{carbs}</td>")
            f.write(f"<td>{proteins}</td>")
            f.write(f"<td>{fat}</td>")
            f.write("</tr>")
        f.write("</table>")

def upload_to_s3(file_path, bucket_name, key):
    try:
        with open(file_path, 'rb') as file_data:
            s3.upload_fileobj(file_data, bucket_name, key, ExtraArgs={
            'ContentType': 'text/html'
        })
        print(f"File uploaded to S3: s3://{bucket_name}/{key}")
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")

def lambda_handler(event, context):
    parent_url = os.environ.get('PARENT_URL')
    today = datetime.datetime.now() 
    date_of_week = today.strftime('%A')
    prefixes = {
        #prefix : menu_name
        "Main Plate Lunch & Dinner": "Main",
    }
    if today.weekday() in (0, 1, 2, 3): # Monday, Tuesday, Wednesday, Thursday
        prefixes["Global Kitchen"] = "Global"

    menu_ids = get_menu_ids(parent_url, prefixes)
    if not menu_ids:
        return
    
    formatted_date = today.strftime('%A%B%-d')
    header_date = today.strftime('%A, %B %d')
    
    meal_data = {}
    for menu_name, menu_id in menu_ids.items():
        url = f'https://www.nutritics.com/menu/ma4003/{menu_id}'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            if menu_name == "Main":
                lunch_elements = soup.select(
                    f'.item.g-{formatted_date}Lunch, '
                    f'.item.g-{formatted_date}Brunch, '
                    f'.item.g-{formatted_date}Polish'
                )
                dinner_elements = soup.select(f'.item.g-{formatted_date}Dinner')
                meal_data["Lunch"] = get_food_data(lunch_elements)
                meal_data["Dinner"] = get_food_data(dinner_elements)
            elif menu_name == "Global":
                global_elements = soup.select(f'[class^="item g-{date_of_week}"]')
                meal_data["Global"] = get_food_data(global_elements)
        else:
            print(f'Failed to retrieve the page for {menu_name}. Status code: {response.status_code}')
    
    title = "Daily Menu"
    with open(FILE_PATH, 'w') as f:
        f.write(f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Anton&display=swap" rel="stylesheet">
        <style>
        @media only screen and (max-width: 600px) {{
                .responsive-img {{
                    width: 100% !important;
                    height: auto !important;
                }}
            }}
        .responsive-img {{
        width: 150px;
        height: 123.5px;
        }}
        body {{
            background-color: #ffffff;
        }}
        h1 {{
            background-color: #97002E;
            padding: 10px;
            text-align: center;
            color: #FBAF3F;
        }}
        table {{
            width: 100%;
            text-align: center;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #000;
        }}
        th {{
            width: 17.5%;
        }}
        th.name-column {{
            width: 30%;
        }}
        .allergen {{
            font-size: 11px;
            color: rebeccapurple;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
        }}
        .footer p {{
            font-size: 12px;
            color: #888;
        }}
        
        .footer p p{{
            margin-top: 1em;
        }}
        
        .footer a {{
            color: #888;
            text-decoration: none;
        }}
        .footer img {{
            width: 12px;
            height: auto;
            margin-bottom: -2px;
        }}
        .footer p a span:hover {{
            text-decoration: underline;
        }}
        h2 {{
            font-family: "Anton", sans-serif;
            font-weight: 350;
            font-size: 24px;
            color: #97002E;
            margin-top: 30px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .danger{{
            color: red;
            font-family: Anton;

        }}
        </style>
        
    </head>
    <body>
        <h1>{header_date}</h1>
    """)
        for meal_name in ["Global", "Lunch", "Dinner"]:
            food_items = meal_data.get(meal_name, [])
            write_food_data(f, meal_name, food_items)
        f.write("""
<footer class="footer">
    <p>
        This is my personal website featuring Main Plate Lunch/Dinner and Global Menu only. I do not take responsibility for accuracy.
        <br>
        <span class='danger'>PLEASE</span> take extra precautions by visiting <a href="https://www.nutritics.com/menu/ma4003">Metz's original menu</a> if you are allergic.
        <br>
        <p>
        <a href="https://www.nutritics.com/menu/ma4003">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQQmYS2Rosl2xHcGU1osXO2NF1NClIOnosWOg&s" alt="Metz's Website">
            <span>Original menu</span>
        </a> | 
        <a href="https://www.linkedin.com/in/tanphucle/" >
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn">
            <span>Connect with me</span>
        </a>
        </p>
        <p style="font-size: 10px; color: #aaa; margin-top: 10px; font-style: italic;">
            Automated daily updates via AWS Lambda CI/CD pipeline
        </p>
    </p>
</footer>
</body>
<script>alert("This is my personal website featuring Main Plate Lunch/Dinner and Global Menu only. I do not take responsibility for accuracy. Nutrition/allergen info is from Metz Culinary Management and may change without notice. Shared kitchen prep may cause cross-contact with allergens. Please verify with cafeteria staff. By using this site, you accept these terms.");</script>
</html>""")
    s3_key = "daily_menu.html"
    upload_to_s3(FILE_PATH, BUCKET_NAME, s3_key)
    return {
        'statusCode': 200,
        'body': f"Successfully created HTML file and uploaded to S3: s3://{BUCKET_NAME}/{s3_key}"
    }
