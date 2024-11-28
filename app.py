from flask import Flask, render_template, render_template_string, request, session, flash, get_flashed_messages, url_for, redirect, jsonify
from database import *
from CDN import upload_file
from datetime import timedelta # timedelta is a class from the datetime module that represents the duration of time
from functools import wraps
import os
import logging
import sys
# Configure the global logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
 )

app = Flask(__name__)
app.permanent_session_lifetime = timedelta(minutes=30) # setting the session to expire after 30 minutes of inactivity

app.secret_key = os.environ['APP_SECRET_KEY'] #used in session cookies

ALLOWED_EXTENSIONS_LOGO = {'svg', 'png', 'jpg','jpeg'}
ALLOWED_EXTENSIONS_RESUME = {'pdf', 'doc', 'docx'}
COUNTRIES_LIST = [
"Afghanistan",    "Åland Islands",    "Albania",    "Algeria",    "American Samoa",    "Andorra",    "Angola",    "Anguilla",    "Antarctica",    "Antigua and Barbuda",    "Argentina",    "Armenia",    "Aruba",    "Australia",    "Austria",    "Azerbaijan",    "Bahamas",    "Bahrain",    "Bangladesh",    "Barbados",    "Belarus",    "Belgium",    "Belize",    "Benin",    "Bermuda",    "Bhutan",    "Bolivia",    "Bosnia and Herzegovina",    "Botswana",    "Bouvet Island",    "Brazil",    "British Indian Ocean Territory",    "Brunei Darussalam",    "Bulgaria",    "Burkina Faso",    "Burundi",    "Cambodia",    "Cameroon",    "Canada",    "Cape Verde",    "Cayman Islands",    "Central African Republic",    "Chad",    "Chile",    "China",    "Christmas Island",    "Cocos (Keeling) Islands",    "Colombia",    "Comoros",    "Congo",    "Congo,The Democratic Republic of The",    "Cook Islands",    "Costa Rica",    "Cote D'ivoire",    "Croatia",    "Cuba",    "Cyprus",    "Czech Republic",    "Denmark",    "Djibouti",    "Dominica",    "Dominican Republic",    "Ecuador",    "Egypt",    "El Salvador",    "Equatorial Guinea",    "Eritrea",    "Estonia",    "Ethiopia",    "Falkland Islands (Malvinas)",    "Faroe Islands",    "Fiji",    "Finland",    "France",    "French Guiana",    "French Polynesia",    "French Southern Territories",    "Gabon",    "Gambia",    "Georgia",    "Germany",    "Ghana",    "Gibraltar",    "Greece",    "Greenland",    "Grenada",    "Guadeloupe",    "Guam",    "Guatemala",    "Guernsey",    "Guinea",    "Guinea-bissau",    "Guyana",    "Haiti",    "Heard Island and Mcdonald Islands",    "Holy See (Vatican City State)",    "Honduras",    "Hong Kong",    "Hungary",    "Iceland",    "India",    "Indonesia",    "Iran,Islamic Republic of",    "Iraq",    "Ireland",    "Isle of Man",    "Israel",    "Italy",    "Jamaica",    "Japan",    "Jersey",    "Jordan",    "Kazakhstan",    "Kenya",    "Kiribati",    "Korea,Democratic People's Republic of",    "Korea,Republic of",    "Kuwait",    "Kyrgyzstan",    "Lao People's Democratic Republic",    "Latvia",    "Lebanon",    "Lesotho",    "Liberia",    "Libyan Arab Jamahiriya",    "Liechtenstein",    "Lithuania",    "Luxembourg",    "Macao",    "Macedonia,The Former Yugoslav Republic of",    "Madagascar",    "Malawi",    "Malaysia",    "Maldives",    "Mali",    "Malta",    "Marshall Islands",    "Martinique",    "Mauritania",    "Mauritius",    "Mayotte",    "Mexico",    "Micronesia,Federated States of",    "Moldova,Republic of",    "Monaco",    "Mongolia",    "Montenegro",    "Montserrat",    "Morocco",    "Mozambique",    "Myanmar",    "Namibia",    "Nauru",    "Nepal",    "Netherlands",    "Netherlands Antilles",    "New Caledonia",    "New Zealand",    "Nicaragua",    "Niger",    "Nigeria",    "Niue",    "Norfolk Island",    "Northern Mariana Islands",    "Norway",    "Oman",    "Pakistan",    "Palau",    "Palestinian Territory,Occupied",    "Panama",    "Papua New Guinea",    "Paraguay",    "Peru",    "Philippines",    "Pitcairn",    "Poland",    "Portugal",    "Puerto Rico",    "Qatar",    "Reunion",    "Romania",    "Russian Federation",    "Rwanda",    "Saint Helena",    "Saint Kitts and Nevis",    "Saint Lucia",    "Saint Pierre and Miquelon",    "Saint Vincent and The Grenadines",    "Samoa",    "San Marino",    "Sao Tome and Principe",    "Saudi Arabia",    "Senegal",    "Serbia",    "Seychelles",    "Sierra Leone",    "Singapore",    "Slovakia",    "Slovenia",    "Solomon Islands",    "Somalia",    "South Africa",    "South Georgia and The South Sandwich Islands",    "Spain",    "Sri Lanka",    "Sudan",    "Suriname",    "Svalbard and Jan Mayen",    "Swaziland",    "Sweden",    "Switzerland",    "Syrian Arab Republic",    "Taiwan",    "Tajikistan",    "Tanzania,United Republic of",    "Thailand",    "Timor-leste",    "Togo",    "Tokelau",    "Tonga",    "Trinidad and Tobago",    "Tunisia",    "Turkey",    "Turkmenistan",    "Turks and Caicos Islands",    "Tuvalu",    "Uganda",    "Ukraine",    "United Arab Emirates",    "United Kingdom",    "United States",    "United States Minor Outlying Islands",    "Uruguay","Uzbekistan","Vanuatu","Venezuela","Viet Nam","Virgin Islands, British","Virgin Islands, U.S.","Wallis and Futuna","Western Sahara","Yemen","Zambia","Zimbabwe"]

def allowed_file(filename, is_resume=False): # 'resume' parameter denotes if the file is a resume
    logging.info(f'inside allowed_file(), checking if {filename} is allowed')
    if is_resume==True:
        return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_RESUME
    else: #if not resume, it is treated as an image file (pfp/logo)
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_LOGO


#CUSTOM DECORATOR FOR LOGIN AND ROLE CHECK:
def login_required(role):
    def decorator(f): # decorator function that takes the original function (f) as an argument (f here is the route function on which this decorator would be applied)
        @wraps(f) # wraps the original function to preserve its name and docstring
        def decorated_function(*args, **kwargs): # decorated function that takes the arguments of the original function
            if 'user_id' not in session or session.get('role') != role:
                logging.info(f'User not logged in or does not have the required role: {role}')
                if(role == 'admin'): # open on the admin-side of thr login page
                    return redirect(url_for('login', admin_side=True)+ f"&next={request.path}") 
                else:
                    return redirect(url_for('login')+ f"?next={request.path}") # 'next' is a query parameter that stores the URL of the page that redirected to the login page
            return f(*args, **kwargs) # after checking for login, run the original function
        return decorated_function # return the decorated function containing the additional login check logic
    return decorator #return the decorator function

#CONTEXT PROCESSORS:
@app.context_processor
def login_check():
    
    # Check if user-data is in the session
    if 'user_id' in session and session.get('role') == 'user':
        return { #returning a dictionary of variables that will be available in all templates
            'logged_in': True,
            'user_id': session.get('user_id'),
            'user_email': session.get('email'),
            'user_pfp': get_user_profile(session['user_id'], pfp_only = True) # Get pfp as a dictionary containg secure_url
        }
    else:
        return {
            'logged_in': False
        }
#ROUTES:
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    admin_side = request.args.get('admin_side', default='false', type=str).lower() == 'true' # flag that decides whether to open admin-side or not
    return render_template('login.html',admin_side=admin_side)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/add_new_user', methods=['POST'])
def new_user():
    if(user_exists(request.form) == True): #if the user already exists in the database
        flash('User Already Exists, Please Login', 'failed')
        return redirect( url_for('register'))
    else:
        add_user(request.form)
        return redirect(url_for('login'))
        

@app.route('/userLogin', methods=['POST'])
def user_login():
    user = validate_user(request.form)
    if(user is not None): #set session details
        session['email'] = user['email']
        session['user_id'] = user['user_id']
        session['role'] = 'user'
        session.permanent = True #This sets the session to use the configured timeout (permanent sessions will persist until specified timeout)
        next_page = request.form.get('next') #from the hidden input, get the page_url that sent you to the login page
        return redirect(next_page) if next_page else redirect(url_for('home'))
    else:
        flash('Invalid Email Address or Password', 'user-failed')
        return redirect(url_for('login'))

@app.route('/adminLogin', methods=['POST'])
def admin_login():
    if(validate_admin(request.form) == True):
        session['email'] = request.form.get('email')
        session['user_id'] = 1 # hardcoded user_id for admin
        session['role'] = 'admin'
        session.permanent = True #This sets the session to use the configured timeout (permanent sessions will persist until specified timeout)
        next_page = request.form.get('next')
        return redirect(next_page) if next_page else redirect(url_for('admin_base'))
    else:
        flash('Invalid Email Address or Password', 'admin-failed')
        return redirect(url_for('login', admin_side=True))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home')) # redirect back to the last page, or to the login page (as a fallback) 

@app.route('/profile')
@login_required('user')
def profile():
    user_id = session.get('user_id')
    user_data = get_user_profile(user_id)
    return render_template('profile.html', user_data=user_data)

@app.route('/edit/<file_type>', methods=['POST'])
def editFile(file_type): #file_type is either 'pfp' or 'profile_resume'
    if file_type not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files[file_type] #get the profile_resume or pfp file
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename, is_resume = (file_type == 'profile_resume')):
        file_meta_data = upload_file(file, type=file_type)
        if file_meta_data['success'] == False:
            return jsonify({'error': 'Error uploading file'}), 500

        #else if file uploaded successfully, update the url in the database:
        if(file_type == 'pfp'):
            update_user_profile(session.get('user_id'), pfp_url = file_meta_data['secure_url'])
        elif(file_type == 'profile_resume'):
            update_user_profile(session.get('user_id'), resume_url = file_meta_data['secure_url'], resume_name = file.filename)
        profile = get_user_profile(session.get('user_id'), completion_percentage_only=True) # get the updated completion_percentage
        return jsonify({'success': f'{file_type} updated successfully', f'{file_type}_secure_url': file_meta_data['secure_url'], f'{file_type}_name':file.filename, 'completion_percentage':profile['completion_percentage']}) , 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400
    


@app.route('/edit/personal_details')
def editPersonalDetails():
    user_id= session.get('user_id')
    user_data = get_user_profile(user_id)
    return render_template('partials/personal-details-edit.html', user_data=user_data, countries=COUNTRIES_LIST)

@app.route('/cancel/personal_details')
def cancelPersonalDetails():
    user_id = session.get('user_id')
    user_data = get_user_profile(user_id)
    return render_template('partials/personal-details-card.html', user_data=user_data)


@app.route('/update/personal_details', methods=['PUT'])
def updateProfile():
    data = request.form
    logging.debug(f'inside personal_details route. Request received for data: {data}')
    user_id = session.get('user_id')
    update_user_profile(user_id, data)
    new_data = get_user_profile(user_id)
    return render_template('partials/personal-details-card.html', user_data = new_data)

@app.route('/action-center')
@login_required('user')
def actionCenter():
    user_id= session.get('user_id')
    list_of_applications, has_unread_notifs = load_applications_for_user(user_id=user_id)    
    return render_template('action-center.html',list_of_applications=list_of_applications, has_new_notifications = has_unread_notifs)

@app.route('/applications')
def applications():
    user_id= session.get('user_id')
    list_of_applications, has_new_notifs = load_applications_for_user(user_id=user_id) # this func returns two values, where only first one is useful, and second one is simply ignored
    return render_template('partials/applications-Container.html', list_of_applications=list_of_applications)

@app.route('/notifications')
def notifications():
    user_id = session.get('user_id')
    list_of_notifications = load_notifications(user_id=user_id)
    return render_template('partials/notifications.html', list_of_notifications=list_of_notifications)

@app.route('/withdraw/<int:application_id>', methods=['POST'])
def withdraw(application_id):
    try:
        user_id = session.get('user_id')
        success, msg = remove_application(application_id, user_id)
        if success == True:
            return '', 200
        else: 
            return jsonify({'error':msg}), 400

    except Exception as e:
        logging.error(f'it would seem an error has occurred: {str(e)}', exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/bookmarked-jobs')
@login_required('user')
def bookmarkedJobs():
    list_of_jobs = load_bookmarked_jobs(session.get('user_id'))
    return render_template('bookmarked-jobs.html', list_of_jobs=list_of_jobs, filtered = False)

@app.route('/searchBookmarkedJobs')
def search_bookmarked_jobs():
    q = request.args.get('search', '') #searchbar query
    sort_by = request.args.get('sort_by', 'relevance')  # Default sort by relevance
    locations = request.args.getlist('location')  # Get multiple values for locations (work environment)
    employment_types = request.args.getlist('employment-type')  # Get multiple values for employment_type
    experiences = request.args.getlist('experience')  # Get multiple values for experience
    date_filter = request.args.get('posting-date')  # Get multiple values for posting_date
    logging.debug(f"Received bookmark search request. Request.args: {request.args}")
    list_of_jobs = load_bookmarked_jobs(user_id = session.get('user_id'), q=q, sort_by=sort_by, locations=locations, employment_types=employment_types, experiences=experiences, date_filter=date_filter)
    return render_template('partials/bookmarked-results.html', list_of_jobs=list_of_jobs, filtered = True)



@app.route('/create_job')
def create_job():
    return render_template('admin-create-job.html') 

@app.route('/review_applications')
def review_applications():
    list_of_applications = load_applications(filter='Pending')
    return render_template('admin-review-applications.html', applications = list_of_applications)

@app.route('/updateApplicationStatus/<int:application_id>/<action>', methods=['POST'])
def update_application_status(application_id, action):
    try:
        if (action == 'reject'): new_status = 'Rejected'
        else : new_status = 'Accepted'
        set_application_status(application_id, new_status)
        return '',200 # okay status with blank content to replace the row
    except Exception as e:
        logging.error(f'it would seem an error has occurred:{str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/manage_jobs')
def manage_jobs():
    list_of_jobs = load_jobs_for_table()
    return render_template('admin-manage-jobs.html', jobs=list_of_jobs)

@app.route('/updateJobStatus/<int:job_id>/<activeFilter>/<action>', methods=['POST'])
def update_job_status(job_id, activeFilter, action):
    try:
        if (action == 'close'): new_status = 'closed'
        else : new_status = 'open'
        set_job_status(job_id, new_status)
        if (activeFilter == 'open' and new_status == 'closed') or (activeFilter == 'closed' and new_status == 'open'):
            result = '' #if the row is to be removed from table, return an empty string
        else: 
            job = get_job_details(job_id=job_id) #if the row is to be updated, return the updated row
            result = render_template('partials/jobs-table-results.html',jobs=[job]) #'jobs-table-results' expects a list of jobs, so wrap the job in a list
        return result, 200 
    except Exception as e:
        logging.error(f'it would seem an error has occurred:{str(e)}',  exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/editJob/<int:job_id>')
def edit_job(job_id):
    job = get_job_details(job_id=job_id)
    return render_template('admin-edit-job.html', job=job)

@app.route('/updateJobData/<int:job_id>', methods=['POST'])
def updateJobData(job_id):
    new_job_data = request.form
    new_logo = request.files.get('updated_logo')
    file_meta_data = None # default value
    if new_logo and new_logo.filename != '' : # if a new logo has been provided
        if not allowed_file(new_logo.filename):
            return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400
        file_meta_data = upload_file(new_logo, type="logo") #returns a dictionary containing uploaded file's secure_url and public_id, or error
        if file_meta_data['success'] == False:
            return jsonify({'status': 'error', 'message': 'Error uploading file'}), 500
    try_upload = set_job_details(job_id, new_job_data, file_meta_data) # returns True or False
    if (try_upload == False):
        return jsonify({'status': 'error', 'message': 'Error updating Job Data'}), 500
    else: 
        return jsonify({'status': 'success', 'message': 'Job data updated successfully!'}), 200

@app.route('/exploreJobs')
def exploreJobs():
    list_of_jobs = load_jobs(user_id = session.get('user_id'))
    return render_template('explore-jobs.html', jobs=list_of_jobs)

@app.route('/searchJobs')
def search_jobs():
    q = request.args.get('search', '') #searchbar query
    sort_by = request.args.get('sort_by', 'relevance')  # Default sort by relevance
    locations = request.args.getlist('location')  # Get multiple values for locations (work environment)
    employment_types = request.args.getlist('employment-type')  # Get multiple values for employment_type
    experiences = request.args.getlist('experience')  # Get multiple values for experience
    date_filter = request.args.get('posting-date')  # Get multiple values for posting_date
    list_of_jobs = load_jobs(q=q, sort_by=sort_by, locations=locations, employment_types=employment_types, experiences=experiences, date_filter=date_filter)
    return render_template('partials/job-search-results.html', jobs=list_of_jobs)

@app.route('/resetFilters')
def reset_filters():
     # reset the filterbox queries but maintain searchbar query
    q = request.args.get('search', '') #searchbar query
    list_of_jobs = load_jobs(q=q)
    return render_template('partials/job-search-results.html', jobs=list_of_jobs)

@app.route('/bookmark-job/<int:job_id>', methods=['POST'])
def bookmark_job(job_id):
    user_id = session.get('user_id')
    if user_id == None:
        return jsonify({'error': 'Please login to bookmark'}), 401
    success, msg = toggle_bookmark(user_id, job_id)
    if success == True:
        status_code = 201 if msg == 'Created' else 200 # send different status codes for addition and removal of bookmark
        return '', status_code
    else:
        return jsonify({'error': msg}), 500

@app.route('/job/<id>/')
@login_required('user')
def job_details(id):
    job = get_job_details(job_id=id, user_id = session.get('user_id'))
    return render_template('jobpage.html', job=job)

@app.route('/<id>/apply/')
@login_required('user')
def apply(id):
    job = get_job_details(job_id=id, concise=True) #fetches only the job title and company name
    user_data = get_user_profile(session.get('user_id'))
    return render_template('apply.html', job=job, user_data = user_data, countries=COUNTRIES_LIST)

@app.route('/submitApplication', methods=['POST'])
def submitApplication():
    get_flashed_messages() #flush all the pre-stored flash messages
    user_id =  session.get('user_id')
    if user_id == None: #if the user is not logged in
        flash('Please login to apply', 'no-session-error')
        return redirect(url_for('login'))
    
    file = request.files.get('resume')
    existing_resume = request.form.get('existing_resume_url')
    logging.debug(f'file is:{file}')
    if (file == None or file.filename == '') and existing_resume == '':  # If no file is uploaded AND there is no existing resume
        flash('No selected file', 'invalid-resume')
        return redirect(url_for('apply', id=request.form.get('job_id')))

    if file: # in case of existing_resume, the 'file' will be None and this condition will be False
        logging.debug(f'filename is: {file.filename}')
        if file.filename == '': # If user does not select file, browser also submits an empty part without filename
            flash('No selected file', 'invalid-resume')
            return redirect(url_for('apply', id=request.form.get('job_id')))
        if not allowed_file(file.filename, is_resume=True): # if incorrect file type
            flash('File type not allowed', 'invalid-resume')
            return redirect(url_for('apply', id=request.form.get('job_id')))
        file_meta_data = upload_file(file, type="resume") #returns a dictionary containing uploaded file's secure_url and public_id, or error

    else: # else for the outer 'if'
        logging.debug('uploading existing resume')
        file_meta_data = upload_file(existing_resume, type="resume") # upload the existing resume if 'file' is None

    if file_meta_data['success'] == False:
        flash('Error uploading file', 'error')
        return redirect(url_for('apply', id=request.form.get('job_id')))

    insertion_response = insert_application(request.form, user_id, file_meta_data['secure_url'], file_meta_data['public_id']) #insert job data into db and return a response (True or False) 
    if insertion_response == False: #if the insertion failed
        flash(f'Error submitting your application into the database', 'error')
        return redirect(url_for('apply', id=request.form.get('job_id')))
    #otherwise, if insertion was successful:
    return redirect(url_for('thank_you_page'))        

    #this is a fallback, if the user somehow manages to bypass the allowed_file check
    return redirect(url_for('apply', id=request.form.get('job_id')))


@app.route('/ThankYouPage')
@login_required('user')
def thank_you_page():
    return render_template('thank-you.html')

@app.route('/admin_base')
@login_required('admin')
def admin_base():
    highlights, remote_data, onsite_data, doughnut_chart_data, list_of_jobs, list_of_applications = get_dashboard_data()
    return render_template('admin-base.html', highlights=highlights, remote_data=remote_data, onsite_data= onsite_data, doughnut_chart_data= doughnut_chart_data, jobs=list_of_jobs, applications=list_of_applications)

@app.route('/admin_dashboard')
def admin_dashboard():
    highlights, remote_data, onsite_data, doughnut_chart_data, list_of_jobs, list_of_applications = get_dashboard_data()
    return render_template('admin-dashboard.html', highlights=highlights, remote_data=remote_data, onsite_data= onsite_data, doughnut_chart_data= doughnut_chart_data, jobs=list_of_jobs, applications=list_of_applications)

@app.route('/newJobData', methods=['POST'])
def newJobData():
    if 'logo' not in request.files:
        return jsonify({'status':'error', 'message': 'No file part'}), 400
    file = request.files['logo']
    # If user does not select file, browser also submits an empty part without filename, so we should check if the filename is empty
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        file_meta_data = upload_file(file, type="logo") #returns a dictionary containing uploaded file's secure_url and public_id, or error

        if file_meta_data['success'] == False:
            return jsonify({'status': 'error', 'message': 'Error uploading file'}), 500

        insertion_response = insert_job_into_db(request.form, file_meta_data['secure_url'], file_meta_data['public_id']) #insert job data into db and return a response (True or False) 
        if insertion_response == False: #if the insertion failed
            return jsonify({'status': 'error', 'message': 'Error inserting job data into database'}), 500
        #otherwise, if insertion was successful:
        return jsonify({'status': 'success', 'message': 'Job opening created successfully!'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400


@app.route('/searchApplicationsTable')
def search_applications_table():
    logging.debug(f"application search request received for :{request.args.get('search', '')}")
    q = request.args.get('search', '') #searchbar query
    filter = request.args.get('filter', 'Pending')
    sort_by = request.args.get('sort_by', 'relevance')
    list_of_applications = load_applications(q=q, filter = filter, sort_by=sort_by)
    return render_template('partials/applications-table-results.html', applications=list_of_applications)


@app.route('/searchJobsTable')
def search_jobs_table():
    logging.debug(f"jobs table search request received for :{request.args.get('search', '')}")
    q = request.args.get('search', '') #searchbar query
    filter = request.args.get('filter', 'All-jobs')
    sort_by = request.args.get('sort_by', 'relevance')

    list_of_jobs = load_jobs_for_table(q=q, filter = filter, sort_by=sort_by)
    return render_template('partials/jobs-table-results.html', jobs=list_of_jobs)