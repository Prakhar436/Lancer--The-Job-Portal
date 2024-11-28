# LANCER
Lancer is a database-driven full-stack Job Portal designed to provide a seamless and efficient platform for browsing job opportunities. This web application enables job seekers to search, filter, and apply for job openings while keeping track of their application statuses. For the admin, the platform offers a comprehensive suite of tools for managing job listings, performing full CRUD operations on postings, and reviewing and managing applications, all through an intuitive admin interface.
## **Live Demo**
Check out the live version hosted on Vercel: [https://lancerjobportal-qyqqi8ohx-prakhar436s-projects.vercel.app/](https://lancerjobportal-qyqqi8ohx-prakhar436s-projects.vercel.app/)
Demo Admin Credentials:
    Email address: prakharp436@gmail.com
    Password: password
## **Features**
- **Session Management:** Secure session management for users and admin, ensuring their login state persists across different pages.

- **Password Encryption:** User passwords are securely hashed using the `bcrypt` module to ensure data protection.

- **Job Search & Filters:** Users can search for open positions, companies, salaries and filter results based on employment type, location, experience, date posted etc.

- **Job Applications:** Apply for jobs by filling out application forms and attaching your resume.

- **Job Bookmarking:** Users can save jobs they are interested in for future reference.

- **Action Center:** Users can easily track the status of their job applications and withdraw applications if necessary. The **Notifications** tab provides alerts and messages about application status changes.

- **User Profiles:** Each user has a personalized profile where they can maintain and update their personal details, profile picture, and resume.

- **Inline Editing:** Users can edit their profile information directly on the profile page without navigating to a separate edit page.

- **Auto-fill Application Forms:** When applying for a job, the application form automatically fetches data from the user's profile and populates the relevant fields, streamlining the process and saving time.

- **Admin Dashboard:** A feature-rich dashboard for admins to manage job listings, monitor statistics, and review applications.

- **Job Management:** Admin can create, read, update, and delete job postings easily through the admin interface.

- **Application Review:** Admins can review and process user applications.

- **Basic Logging:** Utilizes the Python `logging` module to log important events and errors for easier debugging and tracking.
## **Technology Stack**
- **Frontend:** HTML, CSS, JavaScript, HTMX
- **Backend:** Flask (Python)
- **Database:** MySQL
- **Cloud Storage:** Cloudinary
- **Hosting:** Vercel
## **Installation**
Clone the repository:
   ```bash
    git clone https://github.com/Prakhar436/Lancer--The-Job-Portal.git
    cd Lancer--The-Job-Portal
```
Install dependencies:
```bash
    pip install -r requirements.txt
```
Setup environment variables:
```bash
    APP_SECRET_KEY=your_secret_key
    CLOUDINARY_API_SECRET=your_cloudinary_api_secret
    CLOUDINARY_API_KEY=your_cloudinary_api_key
    CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
    DATABASE=your_database_url
    DBPORT=your_database_port
    HOSTNAME=your_database_hostname
    PASSWORD=your_database_password
    USERNAME=your_database_username
```
Import database schema into your MySQL database
```bash
    mysql -u <username> -p <database-name> < lancer_schema.sql
```

Run the application:
```bash
    python wsgi.py
```
