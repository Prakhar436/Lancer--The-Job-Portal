import cloudinary
import cloudinary.uploader
import logging
import os
from cloudinary.utils import cloudinary_url
from flask import jsonify

# Configuration       
cloudinary.config( 
    cloud_name = os.environ['CLOUDINARY_CLOUD_NAME'], 
    api_key = os.environ['CLOUDINARY_API_KEY'], 
    api_secret = os.environ['CLOUDINARY_API_SECRET'], 
    secure=True
)

# Upload a file into its respective folder
def upload_file(file, type):
    print("UPLOADING FILE:", file, "TYPE:", type)
    try:
        # first assign folder and resource-type based on filetype:
        if type == 'logo':
            folder="Logos"
            rtype="image"

        elif type == 'resume':
            folder="Resume"
            rtype="auto"

        elif type=='profile_resume':
            folder="Profile/Resume"
            rtype="auto"
        
        elif type == 'pfp':
            folder = "Profile/Pfp"
            rtype="image"

        result = cloudinary.uploader.upload(
            file,
            asset_folder=folder,
            resource_type=rtype
        )
        return {"success": True, "secure_url": result['secure_url'], "public_id": result['public_id']}
    except Exception as e:
        logging.error(f"!!!ERROR OCCURRED WHILE UPLOADING IMAGE TO CDN:  {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

