"""
Profile Routes - User Profile Page
File: routes/profile_routes.py
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session
from models.user_model import DB
from models.medicine_model import MedicineModel
from datetime import datetime, timedelta

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile_page', methods=['GET', 'POST'])
def profile_page():
    if 'email' not in session:
        return redirect('/login')

    email = session['email']
    db = DB()
    user_model = db.users
    saved_meds_model = db.saved_meds
    medicine_model = MedicineModel()
    
    # Fetch user data
    user = user_model.get_user_by_email(email)

    if request.method == 'POST':
        # Collect updated form data
        profile_data = {
            "fullname": request.form.get("name", "").strip(),
            "age": request.form.get("age", "").strip(),
            "weight": request.form.get("weight", "").strip(),
            "height": request.form.get("height", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "allergies": request.form.get("allergies", "").strip(),
            "medications": request.form.get("medications", "").strip(),
            "smoker": request.form.get("smoker", "").strip(),
            "alcohol": request.form.get("alcohol", "").strip(),
            "medical_conditions": request.form.get("medical_conditions", "").strip()
        }
        user_model.update_user(email, profile_data)

        # Save each medication individually
        medications_input = request.form.get("medications", "").strip()
        if medications_input:
            meds_list = [m.strip() for m in medications_input.split(",") if m.strip()]
            for med in meds_list:
                saved_meds_model.save_medication(email, med)

        # Refresh user object
        user = user_model.get_user_by_email(email)
        db.close()
        medicine_model.close_connection()
        return jsonify({"success": True, "message": "Profile updated", "user": user})

    # GET request → display profile
    # Fetch saved medicines for this user
    raw_meds = saved_meds_model.get_meds_by_email(email)
    saved_meds_list = []
    all_warnings = []
    
    # Process user allergies
    user_allergies = user.get('allergies', '')
    if isinstance(user_allergies, str):
        user_allergies = [a.strip().lower() for a in user_allergies.split(',') if a.strip()]
    else:
        user_allergies = []
    
    # Process each saved medicine
    for med in raw_meds:
        medicine_name = med.get("medication", "")
        
        # Add to saved medicines list ONCE
        saved_meds_list.append({"medication": medicine_name})
        
        # Fetch full medicine data from Medicine collection
        medicine_data = medicine_model.get_medicine_by_name(medicine_name)
        
        if medicine_data:
            # Get warnings from medicine
            warnings = medicine_data.get('warning', [])
            
            # Check if warnings is a string (shouldn't be, but handle it)
            if isinstance(warnings, str):
                warnings = [warnings]
            
            # Make sure it's actually a list
            if not isinstance(warnings, list):
                warnings = []
            
            # Add each warning with the medicine name
            for warning in warnings:
                # Make sure warning is a string, not something else
                if not isinstance(warning, str):
                    continue
                    
                # Clean up the warning text - remove bullet points and extra whitespace
                clean_warning = warning.strip()
                if clean_warning.startswith('•'):
                    clean_warning = clean_warning[1:].strip()
                if clean_warning.startswith('-'):
                    clean_warning = clean_warning[1:].strip()
                
                all_warnings.append({
                    'medicine': medicine_name.title(),
                    'text': clean_warning
                })
            
            # Check for allergy conflicts
            medicine_name_lower = medicine_name.lower()
            for allergy in user_allergies:
                if allergy in medicine_name_lower or medicine_name_lower in allergy:
                    all_warnings.append({
                        'medicine': medicine_name.title(),
                        'text': f'ALLERGY WARNING: You are allergic to {allergy}!',
                        'is_allergy': True
                    })
       
    db.close()
    medicine_model.close_connection()
    
    return render_template(
        'profile_page.html', 
        user=user, 
        saved_medicines=saved_meds_list,
        warnings=all_warnings,
       
    )