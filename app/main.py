import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from pathlib import Path
from fastapi import Form
from passlib.hash import bcrypt
import logging
from fastapi import HTTPException
from typing import Optional
import json 
import re

app = FastAPI()

# Define the path to the app directory
app_path = Path(__file__).parent



# Serve the entire app directory as static files
app.mount("/static", StaticFiles(directory=app_path, html=True), name="static")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection to venues.db
db_path = app_path / 'venues.db'

@app.get("/", response_class=HTMLResponse)
def get_index():
    """
    Serves the index.html file at the root path.
    """
    return FileResponse(app_path / "index.html")

# Function to extract venue ID from the link
# Function to extract venue ID from the link (if needed elsewhere)
def extract_venue_id(link: str) -> int:
    match = re.search(r'/venue/(\d+)', link)
    if match:
        return int(match.group(1))
    raise ValueError("Invalid venue link. Could not extract venue ID.")

@app.post("/add-review/")
async def add_review(
    venue_id: int = Form(...),
    review_title: str = Form(...),
    review_text: str = Form(...),
    colors: int = Form(...),
    smells: int = Form(...),
    quiet: int = Form(...),
    crowdedness: int = Form(...),
    food_variey: int = Form(...),
    playground: str = Form(...),
    fenced: str = Form(...),
    quiet_zones: str = Form(...),
    food_own: str = Form(...),
    defined_duration: str = Form(...)
):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Insert the review into the database
        cursor.execute("""
            INSERT INTO reviews (
                venue_id, review_title, review_text, colors, smells, quiet, crowdedness, 
                food_variey, playground, fenced, quiet_zones, food_own, defined_duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            venue_id, review_title, review_text, colors, smells, quiet, crowdedness, 
            food_variey, playground, fenced, quiet_zones, food_own, defined_duration
        ))

        # Commit the transaction
        conn.commit()

        # Redirect to the venue page with the added review
        return RedirectResponse(url=f"/venue/{venue_id}", status_code=303)

    except sqlite3.Error as e:
        conn.rollback()  # Rollback the transaction on error
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        # Close the connection
        conn.close()

@app.get("/discover", response_class=HTMLResponse)
async def get_discover(request: Request, query: str = None, filters: str = None):
    """
    Fetches and displays venues based on search query and filters.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Base SQL query to fetch all venues
        sql_query = "SELECT * FROM venues"
        parameters = []

        # Apply search query if provided
        if query:
            sql_query += """
                WHERE (
                    name LIKE ? OR
                    address LIKE ? OR
                    playground LIKE ? OR
                    fenced LIKE ? OR
                    quiet_zones LIKE ? OR
                    colors LIKE ? OR
                    smells LIKE ? OR
                    food_own LIKE ? OR
                    defined_duration LIKE ? OR
                    photo_url LIKE ? OR 
                    food_variey LIKE ?
                )
            """
            parameters.extend([f"%{query}%"] * 11)

        # Initialize ordering clause
        order_by_clauses = []

        # Apply filters if provided
        if filters:
            filters_dict = json.loads(filters)
            for key, value in filters_dict.items():
                if key in ['colors', 'smells', 'quiet', 'crowdedness']:
                    # Ensure the value is numeric before adding to ordering
                    try:
                        value = int(value)
                        if 1 <= value <= 4:
                            order_by_clauses.append(f" {key} ASC")
                    except ValueError:
                        pass  # Handle the case where value is not an integer

                elif key == 'food_variey':
                    # Special case for food_variety to order descending
                    order_by_clauses.append(f" {key} DESC")

                elif key in ['playground', 'fenced', 'quiet_zones', 'food_own', 'defined_duration']:
                    # Filter for YES values only
                    if value == 'YES':
                        sql_query += f" WHERE {key} = ?"
                        parameters.append('YES')

        # Apply ordering if any order_by clauses were added
        if order_by_clauses:
            sql_query += f" ORDER BY {', '.join(order_by_clauses)}"

        cursor.execute(sql_query, parameters)
        venues = cursor.fetchall()

        conn.close()

        # Load the discover.html template and render it with the venues
        with open("discover.html", "r") as file:
            template = Template(file.read())

        rendered_html = template.render(venues=venues, query=query or "")
        return HTMLResponse(content=rendered_html)



    except sqlite3.Error as e:
        error_message = f"SQLite error: {e}"
        raise HTTPException(status_code=500, detail=error_message)

    except json.JSONDecodeError as e:
        error_message = f"JSON decoding error: {e}"
        raise HTTPException(status_code=400, detail=error_message)

    except Exception as e:
        error_message = f"An error occurred: {e}"
        raise HTTPException(status_code=500, detail=error_message)


@app.get("/signup", response_class=HTMLResponse)
def get_signup():
    """
    Serves the signup.html file for user registration.
    """
    return FileResponse(app_path / "signup.html")

@app.get("/search-venues/", response_class=HTMLResponse)
async def search_venues(request: Request):
    query = request.query_params.get('query', '')

    # Determine the SQL query to use based on the presence of the search query
    if query:
        sql_query = """
            SELECT * FROM venues WHERE
            name LIKE ? OR
            address LIKE ? OR
            playground LIKE ? OR
            fenced LIKE ? OR
            quiet_zones LIKE ? OR
            colors LIKE ? OR
            smells LIKE ? OR
            food_own LIKE ? OR
            defined_duration LIKE ? OR
            photo_url LIKE ?
        """
        parameters = [f"%{query}%"] * 10  # Apply the search term to all fields
        
    else:
        sql_query = "SELECT * FROM venues"
        parameters = []  # No parameters needed for a full table query

    # Connect to the database and execute the query
    with sqlite3.connect(db_path, check_same_thread=False) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql_query, parameters)
        venues = cursor.fetchall()

    # Load the template and render it with the search results and the query term
    template_path = app_path / "discover.html"
    with open(template_path, "r") as file:
        template = Template(file.read())

    rendered_html = template.render(venues=venues, query=query)
    return HTMLResponse(content=rendered_html)


@app.get("/filter-venues/", response_class=HTMLResponse)
async def filter_venues(
    request: Request,
    playground: str = None,
    fenced: str = None,
    quiet_zones: str = None,
    colors: str = None,
    smells: str = None,
    food_own: str = None,
    defined_duration: str = None,
    quiet: str = None,
    crowdedness: str = None,
    food_variey: str = None
):
    """
    Handles detailed filtering of venues based on user-selected criteria.
    If no filter options are provided, select all entries.
    """
    filters = {
        "playground": playground,
        "fenced": fenced,
        "quiet_zones": quiet_zones,
        "colors": colors,
        "smells": smells,
        "food_own": food_own,
        "defined_duration": defined_duration,
        "quiet": quiet,
        "crowdedness": crowdedness,
        "food_variey": food_variey
    }

    # Start with the base query
    query = "SELECT * FROM venues"
    parameters = []

    # Append conditions based on provided filter values
    for key, value in filters.items():
        if value:
            query += f" AND {key} LIKE ?"
            parameters.append(f"%{value}%")

    try:
        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            venues = cursor.fetchall()

        # Load the discover.html template and render it with the filtered results
        template_path = app_path / "discover.html"
        with open(template_path, "r") as file:
            template = Template(file.read())

        rendered_html = template.render(venues=venues, filters=filters)
        return HTMLResponse(content=rendered_html)

    except Exception as e:
        logger.error(f"Error filtering venues: {e}")
        return HTMLResponse(content=f"An error occurred: {e}", status_code=500)

@app.get("/venue/{venue_id}", response_class=HTMLResponse)
async def get_venue(venue_id: int):
    """
    Retrieve and display details for a specific venue based on its ID.
    Also serves a form for adding reviews with the venue_id included.
    """
    try:
        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM venues WHERE id = ?", (venue_id,))
            venue = cursor.fetchone()  # Fetch the venue details

        if venue is None:
            return HTMLResponse(content="Venue not found", status_code=404)

        # Convert the sqlite3.Row object to a dictionary for easier handling in the template
        venue_dict = dict(venue)

        # Render the template with venue details and a form for adding a review
        template_path = app_path / "venue_page.html"
        with open(template_path, "r") as file:
            template = Template(file.read())

        rendered_html = template.render(venue=venue_dict, venue_id=venue_id)
        return HTMLResponse(content=rendered_html)

    except Exception as e:
        return HTMLResponse(content=f"An unexpected error occurred: {e}", status_code=500)



@app.post("/register/")
async def register_user(nickname: str = Form(...), password: str = Form(...)):
    try:
        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()

            # Check if the nickname already exists
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            existing_user = cursor.fetchone()

            if existing_user:
                logger.info(f"Nickname {nickname} already taken.")
                return HTMLResponse(content="nickname already taken", status_code=400)

            # Hash the password for security
            hashed_password = bcrypt.hash(password)

            # Insert the new user into the database
            cursor.execute("INSERT INTO users (nickname, password) VALUES (?, ?)", (nickname, hashed_password))
            conn.commit()

            logger.info(f"User {nickname} registered successfully.")
            # Redirect to the login page after successful registration
            return RedirectResponse(url="/static/login.html", status_code=303)

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return HTMLResponse(content=f"An error occurred: {e}", status_code=500)

@app.get("/login", response_class=HTMLResponse)
def get_login():
    """
    Serves the login.html file for user login.
    """
    return FileResponse(app_path / "login.html")

@app.post("/login/")
async def login_user(nickname: str = Form(...), password: str = Form(...)):
    try:
        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Check if the nickname exists
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            user = cursor.fetchone()

            if not user:
                logger.info(f"Invalid login attempt for nickname {nickname}.")
                return HTMLResponse(content="Invalid nickname or password", status_code=400)

            # Verify the password
            if not bcrypt.verify(password, user["password"]):
                logger.info(f"Invalid password for nickname {nickname}.")
                return HTMLResponse(content="Invalid nickname or password", status_code=400)
            

            logger.info(f"User {nickname} logged in successfully.")
            # Redirect to the dashboard with the user's nickname
            return RedirectResponse(url=f"/welcome?nickname={nickname}", status_code=303)

            

    except Exception as e:
        logger.error(f"Login error: {e}")
        return HTMLResponse(content=f"An error occurred: {e}", status_code=500)


@app.get("/welcome", response_class=HTMLResponse)
async def get_welcome(request: Request):
    """
    Serves the welcome page after successful login.
    Includes a form to add reviews and lists submitted reviews.
    """
    try:
        nickname = request.query_params.get('nickname')
        if not nickname:
            return HTMLResponse(content="Nickname not found in the request", status_code=400)

        with sqlite3.connect(db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Fetch all reviews to display on the welcome page
            cursor.execute("""
                SELECT reviews.review_text, reviews.timestamp, users.nickname, venues.name AS venue_name
                FROM reviews
                JOIN users ON reviews.user_id = users.id
                JOIN venues ON reviews.venue_id = venues.id
                ORDER BY reviews.timestamp DESC
            """)
            reviews = cursor.fetchall()

            # Fetch all venues to populate the dropdown
            cursor.execute("SELECT id, name FROM venues")
            venues = cursor.fetchall()

        # Load dashboard.html template and render it with the reviews and venues data
        template_path = app_path / "dashboard.html"
        with open(template_path, "r") as file:
            template = Template(file.read())

        rendered_html = template.render(reviews=reviews, venues=venues, nickname=nickname)
        return HTMLResponse(content=rendered_html)

    except Exception as e:
        logger.error(f"Error loading welcome page: {e}")
        return HTMLResponse(content=f"An error occurred: {e}", status_code=500)



# Serve the entire app directory as static files
app.mount("/static", StaticFiles(directory=app_path, html=True), name="static")
