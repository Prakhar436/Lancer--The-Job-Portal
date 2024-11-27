from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import os
import bcrypt
import logging

user = os.environ['USERNAME']
password = os.environ['PASSWORD']
host = os.environ['HOSTNAME']
port = os.environ['DBPORT']
database = os.environ['DATABASE']
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}")

def add_user(credentials):
    password = credentials.get('password')
    # converting password to array of bytes
    arrbytes = password.encode('utf-8') 
    # generating the salt 
    salt = bcrypt.gensalt() 
    # Hashing the password 
    encrypted_password = bcrypt.hashpw(arrbytes, salt)
    with engine.connect() as conn:

        sql_query = text("insert into users(email, password, firstname, lastname) values (:email, :encrypted_password, :fname, :lname)")
        params = {
            'email': credentials.get('email'),
            'encrypted_password': encrypted_password,
            'fname': credentials.get('fname'),
            'lname': credentials.get('lname')
        }
        conn.execute(sql_query, params)
        sql_query = text("select user_id from users where email = :email")
        result = conn.execute(sql_query, {'email':credentials.get('email')}).scalar() #get the generated user_id
        sql_query = text("insert into userprofiles (user_id, email) values (:user_id, :email)") #insert user_id and email into userprofiles
        conn.execute(sql_query, {'user_id':result, 'email':credentials.get('email')})
        conn.commit()
        logging.info("User added successfully")

def user_exists(credentials):
    email = credentials.get('email')
    with engine.connect() as conn:
        sql_query = text("select * from users where email = :email")
        result = conn.execute(sql_query, {'email':email})
        rows = result.fetchall()
        if len(rows) == 0:
            return False
        else:
            return True


def validate_user(credentials): #returns the user's credentials if the user exists, else returns None
    email = credentials.get('email')
    password = credentials.get('password').encode('utf-8')
    with engine.connect() as conn:
        sql_query = text("select * from users where email = :email")
        result = conn.execute(sql_query, {'email':email})
        rows = result.fetchall()
        if len(rows) == 0:
            return None
        columns = result.keys()
        db_credentials = dict(zip(columns, rows[0])) # converting the result into a dictionary
        match = bcrypt.checkpw(password, db_credentials['password'].encode('utf-8')) # checking if the password matches
        if not match:
            return None
        else: 
            return db_credentials

def validate_admin(credentials):
    email = credentials.get('email')
    password = credentials.get('password').encode('utf-8')
    with engine.connect() as conn:
        sql_query = text("select * from admin where email = :email")
        result = conn.execute(sql_query, {'email':email})
        rows = result.fetchall()
        if len(rows) == 0:
            return False
        columns = result.keys()
        db_credentials = dict(zip(columns, rows[0])) # converting the result into a dictionary
        match = bcrypt.checkpw(password, db_credentials['password'].encode('utf-8')) # checking if the password matches
        if not match:
            return False
        else: return True

def insert_job_into_db(job_data, secure_url, public_id):
    #we need "secure_url" to access uploaded image, and "public_id" to delete the image
    try:
        with engine.connect() as conn:
            sql_query = text("INSERT INTO Jobs (title, company, location, description, requirements, work_environment, salary, secure_url, public_id, employment_type, experience) VALUES (:title, :company, :location, :description, :requirements, :work_environment, :salary, :secure_url, :public_id, :employment_type, :experience)")
            params = {
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'location': job_data.get('location'),
                'description': job_data.get('description'),
                'requirements': job_data.get('requirements'),
                'work_environment': job_data.get('work_environment'),
                'salary': job_data.get('salary'),
                'secure_url': secure_url,
                'public_id': public_id,
                'employment_type': job_data.get('employment_type'),
                'experience': job_data.get('experience')
            }
            conn.execute(sql_query, params)
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE INSERTING JOB DATA INTO DATABASE:  {str(e)}", exc_info=True)
        return False

def load_jobs(q=None, sort_by=None, locations=None, employment_types=None, experiences=None, date_filter=None, user_id = None):
    try:
        with engine.connect() as connection:
            if user_id is not None: # if user is logged_in, show which jobs are bookmarked and which are not
                sql_query = """SELECT job_id, title, company, location, created_at, updated_at, status, work_environment, salary, secure_url, employment_type, experience, 
                                (SELECT COUNT(*) FROM applications WHERE job_id = Jobs.job_id) AS application_count,
                                EXISTS (SELECT 1 FROM bookmarkedjobs WHERE user_id = :user_id AND job_id = Jobs.job_id) AS is_bookmarked
                                FROM Jobs WHERE status='open' """
                # using EXISTS() is better than JOIN, because we are not fetching any data from the bookmarkedjobs table, just checking if a bookmark exists
            else:
                sql_query = """SELECT job_id, title, company, location, created_at, updated_at, status, work_environment, salary, secure_url, employment_type, experience,
                                (SELECT COUNT(*) FROM applications WHERE job_id = Jobs.job_id) AS application_count
                                FROM Jobs WHERE status='open' """ 
            params = {'user_id': user_id}
            if q is not None: #if there is a search query (keyword)
                sql_query += " AND (title LIKE :keyword OR company LIKE :keyword OR location LIKE :keyword OR salary LIKE :keyword)"
                params['keyword'] = f"%{q}%"

            if locations:  # If locations are specified
                sql_query += " AND ("
                location_conditions = []
                if 'remote' in locations:
                    location_conditions.append("work_environment = 'Remote'") #in 'Jobs' table, this field is called 'work_environment'
                if 'onsite' in locations:
                    location_conditions.append("work_environment = 'Onsite'")
                sql_query += " OR ".join(location_conditions) + ")"

            if employment_types:  # If employment types are specified
                sql_query += " AND ("
                employment_conditions = []
                if 'full-time' in employment_types:
                    employment_conditions.append("employment_type = 'Full-Time'")
                if 'part-time' in employment_types:
                    employment_conditions.append("employment_type = 'Part-Time'")
                if 'internship' in employment_types:
                    employment_conditions.append("employment_type = 'Internship'")
                if 'freelance' in employment_types:
                    employment_conditions.append("employment_type = 'Freelance'")
                sql_query += " OR ".join(employment_conditions) + ")"

            if experiences:  # If experiences are specified
                sql_query += " AND ("
                experience_conditions = []
                if 'entry-level' in experiences:
                    experience_conditions.append("experience = 'Entry-level'")
                if '1plus' in experiences:
                    experience_conditions.append("experience = '1+ Years'")
                if '3plus' in experiences:
                    experience_conditions.append("experience = '3+ Years'")
                if '5plus' in experiences:
                    experience_conditions.append("experience = '5+ Years'")
                sql_query += " OR ".join(experience_conditions) + ")"

            if date_filter:
                # comparing dates using MySQL functions: NOW(): returns current datetime in UTC, DATE():extracts the date from given datetime, CONVERT_TZ(): converts datetime from one timezone to another, YEARWEEK(): returns the year & the week no. of the year(0-51), YEAR(): returns the year from the given datetime
                #note that timestamp in MySQL is stored as UTC, so we need to convert it to IST (+5:30 hrs) using CONVERT_TZ() before comparing with current datetime               
                if date_filter == 'today': 
                    sql_query += " AND DATE(CONVERT_TZ(created_at, '+00:00', '+05:30')) = DATE(CONVERT_TZ(NOW(), '+00:00', '+05:30'))" #if 'created_at' date is equal to today's date
                elif date_filter == 'this-week':
                    sql_query += " AND YEARWEEK(CONVERT_TZ(created_at, '+00:00', '+05:30'), 1) = YEARWEEK(CONVERT_TZ(NOW(), '+00:00', '+05:30'), 1)" #if 'created_at' and today's date fall in the same week of the year (optional parameter '1' in YEARWEEK() is the mode, it means that weeks are numbered from (1-52))
                elif date_filter == 'this-month':
                    sql_query += " AND YEAR(CONVERT_TZ(created_at, '+00:00', '+05:30')) = YEAR(CONVERT_TZ(NOW(), '+00:00', '+05:30')) AND MONTH(CONVERT_TZ(created_at, '+00:00', '+05:30')) = MONTH(CONVERT_TZ(NOW(), '+00:00', '+05:30'))" #if both year and month are same
                elif date_filter == 'this-year':
                    sql_query += " AND YEAR(CONVERT_TZ(created_at, '+00:00', '+05:30')) = YEAR(CONVERT_TZ(NOW(), '+00:00', '+05:30'))"#if the year is same
            
            if sort_by == 'relevance' and q is not None: #if sorting by relevance and there is a search query
                sql_query += " ORDER BY CASE WHEN title LIKE :keyword THEN 1 WHEN company LIKE :keyword THEN 2 WHEN location LIKE :keyword THEN 3 ELSE 4 END" #CASE WHEN in SQL allows conditional logic within queries (like if-else). It assigns a value based on conditions (WHEN) and handles default cases (ELSE), useful here for prioritizing search matches (title, company, location) in sorting job listings. "ORDER BY" then sorts the results based on the assigned values (1 > 2 > 3 > 4)
            elif sort_by == 'date_posted':
                sql_query += " ORDER BY created_at DESC"
            elif sort_by == 'salary':
                sql_query += " ORDER BY salary DESC"
            else:
                sql_query += " ORDER BY title ASC" #default sorting
            result = connection.execute(text(sql_query), params) 
            
            #to work on the fetched sql entries, we should convert them to an array of dictionaries, where each dict = each row of the table 
            # Fetch all rows from the result
            rows = result.fetchall()
            # Get column names
            columns = result.keys()
            # Convert rows into dictionaries
            list_of_dicts = [dict(zip(columns, row)) for row in rows]
            list_of_dicts = append_posting_time(list_of_dicts) #calculate and append the posting time for each job
            return list_of_dicts
            
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING JOBS FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def append_posting_time(list_of_dicts):
    for job in list_of_dicts:
        # "created_at" is returned as a naive datetime object (without timezone info), you need to make it timezone-aware to allow subtraction with current time
        created_at = job['created_at']
        if created_at.tzinfo is None:
            # If created_at is naive, assume it's in UTC
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        time_diff = now - created_at
        now = datetime.now(timezone.utc)
        time_diff = now - created_at
        # Convert time difference to a human-readable format
        if time_diff.days > 0:
            job['posted_time'] = f"Posted {time_diff.days} day{'s' if time_diff.days > 1 else ''} ago" #if days > 1, add 's' to the singular 'day'
        else:
            hours = time_diff.seconds // 3600
            if hours > 0:
                job['posted_time'] = f"Posted {hours} hour{'s' if hours > 1 else ''} ago"
            else:
                minutes = (time_diff.seconds // 60) % 60
                job['posted_time'] = f"Posted {minutes} minute{'' if minutes == 1 else 's'} ago"
    return list_of_dicts

def get_job_details(job_id, user_id = None, concise=False):
    try:
        with engine.connect() as connection:
            if(concise==True): #if only concise details (title and company names) are needed
                sql_query = 'SELECT job_id, title, company FROM Jobs WHERE job_id = :job_id'
            else: 
                sql_query = '''SELECT job_id, title, company, location, description, requirements, work_environment, salary, status, employment_type, experience, secure_url, public_id, 
                                CONVERT_TZ(created_at, '+00:00', '+05:30') as created_at,
                                CONVERT_TZ(updated_at, '+00:00', '+05:30') as updated_at 
                                FROM Jobs WHERE job_id = :job_id'''
                #CONVERT_TZ() is used to convert the timezone of the timestamp from UTC to IST (+5:30 hrs)
            result = connection.execute(text(sql_query), {'job_id': job_id})
            rows = result.fetchall()
            if len(rows) == 0:
                return None
            columns = result.keys()
            job = dict(zip(columns, rows[0]))
            if user_id is not None: #check if user has applied to job
                sql_query_2 = '''SELECT EXISTS( SELECT 1 FROM applications a
                                                WHERE a.job_id = :job_id AND a.user_id = :user_id)
                                                AS has_applied'''
            
                result = connection.execute(text(sql_query_2), {'job_id': job_id, 'user_id': user_id})
                row = result.fetchone()
                job['has_applied'] = bool(row[0])
            return job
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING JOB DETAILS FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def set_job_details(job_id, job_data, file_meta_data = None):
    try:
        with engine.connect() as conn:
            params = {
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'location': job_data.get('location'),
                'description': job_data.get('description'),
                'requirements': job_data.get('requirements'),
                'work_environment': job_data.get('work_environment'),
                'salary': job_data.get('salary'),
                'employment_type': job_data.get('employment_type'),
                'experience': job_data.get('experience'),
                'job_id': job_id
            }
            sql_query = """UPDATE Jobs SET 
                            title = :title,
                            company = :company,
                            location = :location,
                            description = :description,
                            requirements = :requirements,
                            work_environment = :work_environment,
                            salary = :salary,
                            employment_type = :employment_type,
                            experience = :experience """
            # Add secure_url and public_id to the query if they are provided
            if file_meta_data is not None:
                sql_query += ', secure_url = :secure_url, public_id = :public_id'
                params['secure_url'] = file_meta_data['secure_url']
                params['public_id'] = file_meta_data['public_id']
            sql_query += ' WHERE job_id = :job_id'
            conn.execute(text(sql_query), params)
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE UPDATING JOB IN DATABASE:  {str(e)}", exc_info=True)
        return False

def insert_application(job_data, user_id, secure_url, public_id):
    try:
        with engine.connect() as conn:
            sql_query = text("""
            INSERT INTO applications (
                user_id, email, job_id, first_name, last_name, phone, country, city, secure_url, public_id
            ) VALUES (
                :user_id, :email, :job_id, :first_name, :last_name, :phone, :country, :city, :secure_url, :public_id
            )
            """) 
            params = {
                'user_id': user_id,
                'job_id': job_data.get('job_id'),
                'secure_url': secure_url,
                'public_id': public_id,
                'first_name': job_data.get('firstName'),
                'last_name': job_data.get('lastName'),
                'email': job_data.get('email'),
                'phone': job_data.get('phone'),
                'country': job_data.get('country'),
                'city': job_data.get('city')

            }
            conn.execute(sql_query, params)
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE INSERTING APPLICATION INTO DATABASE:  {str(e)}", exc_info=True)
        return False

def load_applications(q=None, filter='Pending', sort_by='relevance'):
    try:
        with engine.connect() as connection:
            params = {}
            sql_query = ''' select title as job_title,
                            application_id, company, first_name, last_name, phone, city, country, email,
                            applications.secure_url,
                            applications.status,
                            DATE_FORMAT(CONVERT_TZ(application_date, '+00:00', '+05:30'), '%d-%m-%Y') AS date_applied
                            from applications JOIN Jobs on applications.job_id = Jobs.job_id WHERE 1=1''' # WHERE 1=1 is used for building dynamic queries so that we can add more conditions using 'AND' later on, and if no conditions are added, it returns everything (1=1 is always true)                
            if q is not None: #if there is a search query (keyword)
                sql_query += ''' AND ( title like :keyword or company like :keyword or first_name like :keyword or last_name like :keyword or phone like :keyword or email like :keyword or city like :keyword or country like :keyword)'''
                params['keyword'] = f"%{q}%"
            if filter is not None:
                if filter == "All-reviewed":
                    sql_query += " AND applications.status != 'Pending'"
                else:
                    sql_query += " AND applications.status = :filter"
                    params['filter'] = filter
            if sort_by == 'relevance' and q is not None and q != '': #if sorting by relevance and there is a non empty search query
                sql_query += " ORDER BY CASE WHEN title LIKE :keyword THEN 1 WHEN company LIKE :keyword THEN 2 WHEN first_name like :keyword THEN 3 WHEN last_name LIKE :keyword THEN 4 WHEN phone LIKE :keyword THEN 5 WHEN email LIKE :keyword THEN 6 WHEN city LIKE :keyword THEN 7 WHEN country LIKE :keyword THEN 8 ELSE 9 END" #CASE WHEN in SQL allows conditional logic within queries (like if-else). It assigns a value based on conditions (WHEN) and handles default cases (ELSE), useful here for prioritizing search matches (title, company, location) in sorting job listings. "ORDER BY" then sorts the results based on the assigned values (1 > 2 > 3 > 4)
            else:
                sql_query += " ORDER BY application_date DESC"
            result = connection.execute(text(sql_query), params)                
            rows = result.fetchall()
            columns = result.keys()
            list_of_dicts = [dict(zip(columns, row)) for row in rows]
            return list_of_dicts
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING APPLICATIONS FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def set_application_status(application_id, new_status):
    #error handling done in caller function in app.py
    with engine.connect() as conn:
        params = {
            'new_status': new_status,
            'application_id': application_id
        }
        sql_query = text("UPDATE applications SET status = :new_status WHERE application_id = :application_id")
        conn.execute(sql_query, params)
        sql_query = text('SELECT user_id, job_id FROM applications WHERE application_id = :application_id') #fetch user_id and job_id to insert a new notification
        result = conn.execute(sql_query, params)
        user_id, job_id = result.fetchone()
        params['user_id'] = user_id
        params['job_id'] = job_id
        params['notification_type'] = 1 if new_status == 'Accepted' else 0 #now insert new notification into notifications table
        sql_query = text('INSERT INTO notifications (user_id, job_id, notification_type) VALUES (:user_id, :job_id, :notification_type)')
        conn.execute(sql_query, params)
        conn.commit()
        return 

def set_job_status(job_id, new_status):
    #error handling done in caller function in app.py
    with engine.connect() as conn:
        params = {
            'new_status': new_status,
            'job_id': job_id
        }
        sql_query = "UPDATE Jobs SET status = :new_status"
        if(new_status == 'open'): sql_query += ',created_at = NOW()' #if job is reopened, update the created_at timestamp as well
        sql_query += ' WHERE job_id = :job_id; '
        conn.execute(text(sql_query), params)
        if new_status == 'closed': #if job is closed, reject all pending applications and notify the applicants
            #firstly, insert notifications (sending notifications first avoids sending them to already processed applications by filtering required applications via 'Pending' status)
            sql_query = """INSERT INTO notifications (job_id, user_id, notification_type)
                            SELECT :job_id, user_id, 0 
                            FROM applications
                            WHERE job_id = :job_id AND status = 'Pending';"""
            conn.execute(text(sql_query), params)

            #Now update application status
            sql_query = """ UPDATE applications
                            SET status = 'rejected'
                            WHERE job_id = :job_id AND status = 'pending';"""
            conn.execute(text(sql_query), params)
        conn.commit()

def load_jobs_for_table(q=None, filter='All-jobs', sort_by='relevance'): #this func is different from load_jobs() since it does not fetch description & requirements, and applies search query to almost all columns of the table. It also does not append posting time, as is not needed here
    try: 
        with engine.connect() as conn:
            sql_query = "SELECT job_id, title, company, salary, work_environment, employment_type, experience, status, created_at, secure_url  FROM Jobs WHERE 1=1" # WHERE 1=1 is used for building dynamic queries so that we can add more conditions using 'AND' later on, and if no conditions are added, it returns everything (1=1 is always true)
            params = {}
            if q is not None: #if there is a search query (keyword)
                sql_query += ''' AND ( title like :keyword or company like :keyword or work_environment like :keyword or salary like :keyword or employment_type like :keyword or experience like :keyword)'''
                params['keyword'] = f"%{q}%"
            if filter != 'All-jobs':
                sql_query += " AND status = :filter"
                params['filter'] = filter
            if sort_by == 'relevance' and q is not None and q != '': #if sorting by relevance and there is a non empty search query
                sql_query += " ORDER BY CASE WHEN title LIKE :keyword THEN 1 WHEN company LIKE :keyword THEN 2 WHEN work_environment LIKE :keyword THEN 3 WHEN salary LIKE :keyword THEN 4 WHEN employment_type LIKE :keyword THEN 5 WHEN experience LIKE :keyword THEN 6 ELSE 7 END" #CASE WHEN in SQL allows conditional logic within queries (like if-else). It assigns a value based on conditions (WHEN) and handles default cases (ELSE), useful here for prioritizing search matches (title, company, location) in sorting job listings. "ORDER BY" then sorts the results based on the assigned values (1 > 2 > 3 > 4)
            else:
                sql_query += " ORDER BY created_at DESC"

            result = conn.execute(text(sql_query), params) 
            rows = result.fetchall()
            columns = result.keys()
            list_of_dicts = [dict(zip(columns, row)) for row in rows]
            return list_of_dicts
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING JOBS FOR TABLE FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def get_dashboard_data():
    try:
        with engine.connect() as connection:
            highlights = {}
            # Fetch total open jobs
            q1 = text("SELECT COUNT(*) FROM Jobs WHERE status = 'open';")
            res1 = connection.execute(q1)
            highlights['total_jobs'] = res1.scalar() #scalar() returns integer value
        
            # Fetch total applications
            q2 = text("SELECT COUNT(*) FROM applications;")
            res2 = connection.execute(q2)
            highlights['total_applications'] = res2.scalar()
            
            # Fetch total accepted applications
            q3 = text("SELECT COUNT(*) FROM applications WHERE status = 'Accepted';")
            res3 = connection.execute(q3)
            highlights['total_hired'] = res3.scalar()
            
            # Fetch total users
            q4 = text("SELECT COUNT(*) FROM users;")
            res4 = connection.execute(q4)
            highlights['total_users'] = res4.scalar()

            #Fetch bar chart data
            q5 = text(""" SELECT  employment_type, work_environment, COUNT(*) as count
                    FROM Jobs
                    GROUP BY employment_type, work_environment;""")
            result = connection.execute(q5).fetchall()
            #initialize data
            remote_data = [0, 0, 0, 0]
            onsite_data = [0, 0, 0, 0]
            job_types = ['Full-Time', 'Part-Time','Freelance', 'Internship']
            
            for row in result:
                employment_type, work_environment, count = row #unpack the row into these variables
                index = job_types.index(employment_type)
                if work_environment == 'Remote':
                    remote_data[index] = count
                elif work_environment == 'Onsite':
                    onsite_data[index] = count
            
            # Fetch doughnut chart data
            q6 = text("""SELECT status, COUNT(*) as count 
                        FROM applications
                        GROUP BY status;""")
            
            result = connection.execute(q6).fetchall()
            # Initialize the dictionary
            doughnut_chart_data = {'Pending': 0, 'Accepted': 0, 'Rejected': 0}
            # Process the result
            for row in result:
                status, count = row #unpack the row data into these variables status and count
                if status in doughnut_chart_data:
                    doughnut_chart_data[status] = count
            
            # Fetch top 5 most recent jobs
            q7 = text("""
                SELECT job_id, title, employment_type, company, created_at
                FROM Jobs
                ORDER BY created_at DESC
                LIMIT 5;
            """)
            res5 = connection.execute(q7)
            res5_rows = res5.fetchall()
            columns = res5.keys()
            jobs = [dict(zip(columns, row)) for row in res5_rows]

            
            # Fetch top 5 most recent applications
            q8 = text(''' select title as job_title,
                            application_id, company, first_name, last_name,
                            applications.secure_url,
                            DATE_FORMAT(CONVERT_TZ(application_date, '+00:00', '+05:30'), '%d-%m-%Y') AS date_applied
                            from applications JOIN Jobs on applications.job_id = Jobs.job_id 
                            ORDER BY application_date DESC LIMIT 5;''')
            res6 = connection.execute(q8)
            res6_rows = res6.fetchall()
            columns = res6.keys()
            applications = [dict(zip(columns, row)) for row in res6_rows]
            return highlights, remote_data, onsite_data, doughnut_chart_data, jobs, applications
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE FETCHING DASHBOARD DATA FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def get_user_profile(user_id, pfp_only = False, completion_percentage_only=False):
    try:
        with engine.connect() as connection:
            if pfp_only == True: #if only pfp is needed for navbar
                q = text("SELECT pfp_secure_url FROM userprofiles WHERE user_id = :user_id;")
            elif completion_percentage_only: #if only completion_percentage is needed when updating profile via inline_editing
                q = text('''SELECT 
                            ((firstname IS NOT NULL) +
                            (lastname IS NOT NULL) +
                            (userprofiles.email IS NOT NULL) +
                            (phone_number IS NOT NULL) +
                            (resume_secure_url IS NOT NULL) +
                            (city IS NOT NULL) +
                            (country IS NOT NULL) +
                            (pfp_secure_url IS NOT NULL)) AS filled_fields
                            FROM users LEFT JOIN userprofiles ON users.user_id = userprofiles.user_id 
                            WHERE users.user_id = :user_id;''')
            else:
                q = text('''SELECT 
                            users.user_id, firstname, lastname,  userprofiles.email, phone_number, resume_secure_url, resume_name, city, country, pfp_secure_url,
                            ((firstname IS NOT NULL) +
                            (lastname IS NOT NULL) +
                            (userprofiles.email IS NOT NULL) +
                            (phone_number IS NOT NULL) +
                            (resume_secure_url IS NOT NULL) +
                            (city IS NOT NULL) +
                            (country IS NOT NULL) +
                            (pfp_secure_url IS NOT NULL)) AS filled_fields,
                            (SELECT COUNT(*) FROM applications WHERE user_id = :user_id) AS applications_count,
                            (SELECT COUNT(*) FROM bookmarkedjobs WHERE user_id = :user_id) AS bookmarked_jobs_count
                            FROM users LEFT JOIN userprofiles ON users.user_id = userprofiles.user_id 
                            WHERE users.user_id = :user_id;''')

            params = {
                'user_id': user_id
            }
            result = connection.execute(q, params)
            rows = result.fetchall()
            if len(rows) == 0:
                return None
            columns = result.keys()
            user_profile = dict(zip(columns, rows[0]))
            # Before accessing conditionally requested fields, check if they were actually requested (ie. if they are even present in the user_profile dict)
            if not completion_percentage_only and user_profile['pfp_secure_url'] == None: #if pfp is actually requested and user has not set a pfp
                user_profile['pfp_secure_url'] = '/static/images/default-pfp.svg'
            if pfp_only == False: #if completion_percentage is actually requested
                user_profile['completion_percentage'] = round(user_profile['filled_fields']/8 *100) #8 fields in total
            return user_profile
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE FETCHING USER PROFILE FROM DATABASE:  {str(e)}", exc_info=True)
        return None

def update_user_profile(user_id, data=None, pfp_url = None, resume_url = None, resume_name=None):
    users_fields = []
    userprofiles_fields = []
    params = {}

    if data is not None:
        #users table updates:
        if(data.get('fname') and data.get('fname') != '-'): #check if the field has some value and that value is not '-'
            users_fields.append('firstname = :fname')
            params['fname'] = data.get('fname')
        if(data.get('lname') and data.get('lname') != '-'):
            users_fields.append('lastname = :lname')
            params['lname'] = data.get('lname')
        #userprofiles table updates:
        if (data.get('email') and data.get('email') != '-'):
            userprofiles_fields.append("email = :email")
            params['email'] = data.get('email')
        if (data.get('phone') and data.get('phone') != '-'):
            userprofiles_fields.append("phone_number = :phone")
            params['phone'] = data.get('phone')
        if (data.get('city') and data.get('city') != '-'):
            userprofiles_fields.append("city = :city")
            params['city'] = data.get('city')
        if (data.get('country') and data.get('country') != '-'):
            userprofiles_fields.append("country = :country")
            params['country'] = data.get('country')

    if pfp_url:
        userprofiles_fields.append("pfp_secure_url = :pfp_url")
        params['pfp_url'] = pfp_url
    
    if resume_url and resume_name:
        userprofiles_fields.append("resume_secure_url = :resume_url")
        userprofiles_fields.append("resume_name = :resume_name")
        params['resume_url'] = resume_url
        params['resume_name'] = resume_name

    params['user_id'] = user_id
    with engine.connect() as conn:

        if users_fields:
            users_query = f"UPDATE users SET {', '.join(users_fields)} WHERE user_id = :user_id"
            conn.execute(text(users_query), params)
        # Execute update for the userprofiles table if there are fields to update
        if userprofiles_fields:
            userprofiles_query = f"UPDATE userprofiles SET {', '.join(userprofiles_fields)} WHERE user_id = :user_id"
            conn.execute(text(userprofiles_query), params)
        # Commit the transaction
        conn.commit()

def load_notifications(user_id):
    try:
        with engine.connect() as connection:
            q = text('''SELECT company, title, location, work_environment, salary, secure_url, employment_type, experience, 
                        n.created_at, notification_type FROM notifications n JOIN Jobs ON n.job_id = Jobs.job_id WHERE user_id = :user_id ORDER BY n.created_at DESC;''')
            params = {
                'user_id': user_id
            }
            result = connection.execute(q, params)
            q = text("UPDATE notifications SET is_read = true WHERE is_read = false AND user_id = :user_id;")
            connection.execute(q, params)
            connection.commit()
            rows = result.fetchall()
            columns = result.keys()
            notifications = [dict(zip(columns, row)) for row in rows]

            return notifications
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING NOTIFICATIONS FROM DATABASE:  {str(e)}", exc_info=True)
        return None, 500

def load_applications_for_user(user_id):
    try:
        with engine.connect() as connection:
            sql_query = ''' select title as job_title,
                                application_id, company, salary, location, work_environment, employment_type, experience, Jobs.secure_url as company_logo,
                                applications.secure_url,
                                applications.status,
                                DATE_FORMAT(CONVERT_TZ(application_date, '+00:00', '+05:30'), '%d-%m-%Y') AS date_applied
                                from applications JOIN Jobs on applications.job_id = Jobs.job_id WHERE user_id = :user_id ORDER BY application_date DESC;'''
            params = {'user_id': user_id}
            result = connection.execute(text(sql_query), params)
            sql_query = text("SELECT EXISTS (SELECT 1 FROM notifications WHERE user_id = :user_id AND is_read = False) AS has_unread_notifications;")
            has_unread_notifs = connection.execute(sql_query, params).scalar()
            connection.commit()
            rows = result.fetchall()
            columns = result.keys()
            list_of_applications = [dict(zip(columns, row)) for row in rows]
            return list_of_applications, has_unread_notifs
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING APPLICATIONS FOR USER FROM DATABASE:  {str(e)}", exc_info=True)
        return None, 500




def remove_application(application_id, user_id):
    with engine.connect() as conn:
        query = text("SELECT status, job_id FROM applications WHERE application_id = :application_id and user_id = :user_id") # check if the application is in "Pending" status  
        params = {'application_id': application_id, 'user_id': user_id}
        result = conn.execute(query, params)
        application = result.fetchone()
        
        if application is None: # if incorrect application_id
            return False, "Application not found"
        
        if application[0] != 'Pending': # Check if the status is 'Pending'
            return False, "Already reviewed applications cannot be withdrawn"
        
        query = text("DELETE FROM applications WHERE application_id = :application_id and user_id = :user_id")
        conn.execute(query, params)
        # insert new 'withdrawn' notification into notifications table
        query = text('INSERT INTO notifications (user_id, job_id, notification_type) VALUES (:user_id, :job_id, :notification_type)')
        params['job_id'] = application[1] # fetched above
        params['notification_type'] = 2
        conn.execute(query, params)
        conn.commit()
        return True, "Application withdrawn successfully"
    
def toggle_bookmark(user_id, job_id):
    try:
        with engine.connect() as conn:
            query = text("SELECT COUNT(*) FROM bookmarkedjobs WHERE user_id = :user_id and job_id = :job_id") # check if the job is already bookmarked
            params = {'user_id': user_id, 'job_id': job_id}
            result = conn.execute(query, params)
            count = result.fetchone()[0]
            if count == 0: # if NOT bookmarked, insert a new bookmark
                query = text("INSERT INTO bookmarkedjobs (user_id, job_id) VALUES (:user_id, :job_id)")
                msg = 'Created'
            else: # if bookmarked, delete the bookmark
                query = text("DELETE FROM bookmarkedjobs WHERE user_id = :user_id and job_id = :job_id")
                msg = 'Removed'
            conn.execute(query, params)
            conn.commit()
            return True, msg
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE TOGGLING BOOKMARK:  {str(e)}", exc_info=True)
        return False, "Error occurred while toggling bookmark"

        
def load_bookmarked_jobs(user_id, q=None, sort_by=None, locations=None, employment_types=None, experiences=None, date_filter=None):
    try:
        with engine.connect() as connection:
            sql_query = '''SELECT Jobs.job_id, title, company, location, created_at, updated_at, status, work_environment, salary, secure_url, employment_type, experience,
                            (SELECT COUNT(*) FROM applications WHERE job_id = Jobs.job_id) AS application_count
                            FROM Jobs INNER JOIN bookmarkedjobs 
                            ON Jobs.job_id = bookmarkedjobs.job_id
                            WHERE bookmarkedjobs.user_id = :user_id'''
            params = {'user_id': user_id}
            if q is not None: #if there is a search query (keyword)
                sql_query += " AND (title LIKE :keyword OR company LIKE :keyword OR location LIKE :keyword OR salary LIKE :keyword)"
                params['keyword'] = f"%{q}%"

            if locations:  # If locations are specified
                sql_query += " AND ("
                location_conditions = []
                if 'remote' in locations:
                    location_conditions.append("work_environment = 'Remote'") #in 'Jobs' table, this field is called 'work_environment'
                if 'onsite' in locations:
                    location_conditions.append("work_environment = 'Onsite'")
                sql_query += " OR ".join(location_conditions) + ")"

            if employment_types:  # If employment types are specified
                sql_query += " AND ("
                employment_conditions = []
                if 'full-time' in employment_types:
                    employment_conditions.append("employment_type = 'Full-Time'")
                if 'part-time' in employment_types:
                    employment_conditions.append("employment_type = 'Part-Time'")
                if 'internship' in employment_types:
                    employment_conditions.append("employment_type = 'Internship'")
                if 'freelance' in employment_types:
                    employment_conditions.append("employment_type = 'Freelance'")
                sql_query += " OR ".join(employment_conditions) + ")"

            if experiences:  # If experiences are specified
                sql_query += " AND ("
                experience_conditions = []
                if 'entry-level' in experiences:
                    experience_conditions.append("experience = 'Entry-level'")
                if '1plus' in experiences:
                    experience_conditions.append("experience = '1+ Years'")
                if '3plus' in experiences:
                    experience_conditions.append("experience = '3+ Years'")
                if '5plus' in experiences:
                    experience_conditions.append("experience = '5+ Years'")
                sql_query += " OR ".join(experience_conditions) + ")"

            if date_filter:
                # comparing dates using MySQL functions: NOW(): returns current datetime in UTC, DATE():extracts the date from given datetime, CONVERT_TZ(): converts datetime from one timezone to another, YEARWEEK(): returns the year & the week no. of the year(0-51), YEAR(): returns the year from the given datetime
                #note that timestamp in MySQL is stored as UTC, so we need to convert it to IST (+5:30 hrs) using CONVERT_TZ() before comparing with current datetime               
                if date_filter == 'today': 
                    sql_query += " AND DATE(CONVERT_TZ(created_at, '+00:00', '+05:30')) = DATE(CONVERT_TZ(NOW(), '+00:00', '+05:30'))" #if 'created_at' date is equal to today's date
                elif date_filter == 'this-week':
                    sql_query += " AND YEARWEEK(CONVERT_TZ(created_at, '+00:00', '+05:30'), 1) = YEARWEEK(CONVERT_TZ(NOW(), '+00:00', '+05:30'), 1)" #if 'created_at' and today's date fall in the same week of the year (optional parameter '1' in YEARWEEK() is the mode, it means that weeks are numbered from (1-52))
                elif date_filter == 'this-month':
                    sql_query += " AND YEAR(CONVERT_TZ(created_at, '+00:00', '+05:30')) = YEAR(CONVERT_TZ(NOW(), '+00:00', '+05:30')) AND MONTH(CONVERT_TZ(created_at, '+00:00', '+05:30')) = MONTH(CONVERT_TZ(NOW(), '+00:00', '+05:30'))" #if both year and month are same
                elif date_filter == 'this-year':
                    sql_query += " AND YEAR(CONVERT_TZ(created_at, '+00:00', '+05:30')) = YEAR(CONVERT_TZ(NOW(), '+00:00', '+05:30'))"#if the year is same
            
            if sort_by == 'relevance' and q is not None and q != '': #if sorting by relevance and there is a search query
                sql_query += " ORDER BY CASE WHEN title LIKE :keyword THEN 1 WHEN company LIKE :keyword THEN 2 WHEN location LIKE :keyword THEN 3 ELSE 4 END" #CASE WHEN in SQL allows conditional logic within queries (like if-else). It assigns a value based on conditions (WHEN) and handles default cases (ELSE), useful here for prioritizing search matches (title, company, location) in sorting job listings. "ORDER BY" then sorts the results based on the assigned values (1 > 2 > 3 > 4)
            elif sort_by == 'date_posted':
                sql_query += " ORDER BY updated_at DESC"
            elif sort_by == 'salary':
                sql_query += " ORDER BY salary DESC"
            else:
                sql_query += " ORDER BY bookmarked_at DESC" # default sorting by date of bookmarking
            result = connection.execute(text(sql_query), params) 
            
            #to work on the fetched sql entries, we should convert them to an array of dictionaries, where each dict = each row of the table 
            # Fetch all rows from the result
            rows = result.fetchall()
            # Get column names
            columns = result.keys()
            # Convert rows into dictionaries
            list_of_dicts = [dict(zip(columns, row)) for row in rows]
            return list_of_dicts
            
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE LOADING JOBS FROM DATABASE:  {str(e)}", exc_info=True)
        return None
