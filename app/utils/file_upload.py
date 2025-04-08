# app/utils/file_upload.py
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import imghdr

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def validate_image(stream):
    """Validate file is an actual image"""
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

def save_profile_picture(file, user_id):
    """Save user profile picture"""
    if file and allowed_file(file.filename):
        try:
            # Create unique filename
            filename = secure_filename(file.filename)
            ext = get_file_extension(filename)
            new_filename = f"user_{user_id}_{uuid.uuid4().hex}.{ext}"
            
            # Ensure upload directory exists
            upload_folder = os.path.join(current_app.static_folder, 'img', 'profiles')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save original file
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
            
            # Create thumbnail
            create_thumbnail(file_path, file_path.replace('.', '_thumb.'), (150, 150))
            
            # Return relative path to be stored in database
            return os.path.join('/static', 'img', 'profiles', new_filename)
            
        except Exception as e:
            current_app.logger.error(f"Error saving profile picture: {str(e)}")
            return None
    
    return None

def create_thumbnail(source_path, target_path, size=(150, 150)):
    """Create thumbnail from an image"""
    try:
        with Image.open(source_path) as img:
            img.thumbnail(size)
            img.save(target_path)
    except Exception as e:
        current_app.logger.error(f"Error creating thumbnail: {str(e)}")

def delete_file(file_path):
    """Delete file from disk"""
    if not file_path:
        return False
        
    try:
        # Convert from URL to file system path
        if file_path.startswith('/static'):
            file_path = os.path.join(current_app.static_folder, file_path[8:])
            
        # Delete file if it exists
        if os.path.exists(file_path):
            os.remove(file_path)
            
            # Also delete thumbnail if it exists
            thumb_path = file_path.replace('.', '_thumb.')
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file: {str(e)}")
        return False

def save_player_photo(file, player_id):
    """Save player photo"""
    if file and allowed_file(file.filename):
        try:
            # Create unique filename
            filename = secure_filename(file.filename)
            ext = get_file_extension(filename)
            new_filename = f"player_{player_id}_{uuid.uuid4().hex}.{ext}"
            
            # Ensure upload directory exists
            upload_folder = os.path.join(current_app.static_folder, 'img', 'players')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save original file
            file_path = os.path.join(upload_folder, new_filename)
            file.save(file_path)
            
            # Create thumbnail
            create_thumbnail(file_path, file_path.replace('.', '_thumb.'), (150, 150))
            
            # Return relative path to be stored in database
            return os.path.join('/static', 'img', 'players', new_filename)
            
        except Exception as e:
            current_app.logger.error(f"Error saving player photo: {str(e)}")
            return None
    
    return None 