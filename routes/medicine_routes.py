"""
Medicine Routes - Updated to use MongoDB
File: routes/medicine_routes.py
"""

from flask import Blueprint, render_template, request, jsonify, redirect, session
from models.medicine_model import MedicineModel
from utils.helpers import get_current_user
from utils.ai_service import generate_medicine_info
import threading

# ✅ NEW: Import user collections functions
from models.user_collections import (
    add_to_search_history, 
    get_user_search_history,
    add_to_favorites,
    remove_from_favorites,
    get_user_favorites,
    is_favorite,
    add_review,
    get_medicine_reviews,
    get_medicine_average_rating,
    delete_review
)

medicine_bp = Blueprint('medicine', __name__)

# Initialize MongoDB model
medicine_model = MedicineModel()

# Track which medicines are being generated
ai_status = {}

# ============================================
# HOMEPAGE
# ============================================

@medicine_bp.route('/')
@medicine_bp.route('/homepage')
def homepage():
    user_info = get_current_user()
    return render_template('homepage.html', user=user_info)

@medicine_bp.route('/search', methods=['POST'])
def search_medicine():
    medicine_name = request.form.get('medicine', '').strip()
    if not medicine_name:
        return jsonify({'error': 'Medicine name required'}), 400
    
    medicine_url = medicine_name.lower().replace(' ', '-')
    return redirect(f'/medicine/{medicine_url}')

# ============================================
# MEDICINE PAGE - Main Logic
# ============================================

@medicine_bp.route('/medicine/<name>')
def medicine_details(name):
    medicine_name = name.lower().replace('-', ' ')
    
    # ✅ NEW: Track search history if user is logged in
    if 'email' in session:
        user_email = session.get('email')
        add_to_search_history(user_email, medicine_name)
    
    # Check if medicine exists in MongoDB
    medicine_data = medicine_model.get_medicine_by_name(medicine_name)
    
    if medicine_data:
        # Medicine found! Show it
        user_info = get_current_user()
        
        # ✅ NEW: Check if medicine is in user's favorites
        is_favorited = False
        if 'email' in session:
            is_favorited = is_favorite(session.get('email'), medicine_name)
        
        # ✅ NEW: Get reviews for this medicine
        reviews = get_medicine_reviews(medicine_name)
        rating_data = get_medicine_average_rating(medicine_name)
        
        return render_template(
            'medicine.html', 
            medicine=medicine_data, 
            user=user_info,
            is_favorited=is_favorited,
            reviews=reviews,
            average_rating=rating_data['average'] if rating_data else 0,
            review_count=rating_data['count'] if rating_data else 0
        )
    
    # Medicine not found - need AI to generate it
    status = ai_status.get(medicine_name, 'new')

    if status == 'new':
        # First time - start AI generation
        ai_status[medicine_name] = 'working'
        thread = threading.Thread(target=generate_ai_info, args=(medicine_name,))
        thread.daemon = True
        thread.start()

    # Show loading message
    loading_data = {
        'name': name.replace('-', ' ').title(),
        'description': '🤖 AI is generating information... Please wait 1-3 minutes.',
        'advice': '⏳ Page will refresh automatically every 10 seconds.',
        'warning': '💡 Make sure LM Studio is running!',
        'pubmed_link': f'https://pubmed.ncbi.nlm.nih.gov/?term={name.replace("-", "+")}'
    }

    user_info = get_current_user()
    return render_template('medicine.html', 
                        medicine=loading_data, 
                        user=user_info,
                        is_favorited=False,
                        reviews=[],
                        average_rating=0,
                        review_count=0)

# Background function to generate medicine info
def generate_ai_info(medicine_name):
    print(f"🤖 Starting AI for: {medicine_name}")
    
    # Call AI
    medicine_data = generate_medicine_info(medicine_name)
    
    if medicine_data:
        print(f"✅ AI done for: {medicine_name}")
        # Save to MongoDB instead of JSON
        medicine_model.create_medicine(medicine_data)
        ai_status[medicine_name] = 'done'
    else:
        print(f"❌ AI failed for: {medicine_name}")
        ai_status[medicine_name] = 'failed'

# ============================================
# ADD TO PROFILE
# ============================================

@medicine_bp.route('/api/profile/add-medicine', methods=['POST'])
def add_medicine_to_profile():
    #Check for 'email' not 'user_id'
    if 'email' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
    # Get the email from session
    user_email = session.get('email')
    medicine_name = request.form.get('medicine_name', '').strip().lower()
    
    if not medicine_name:
        return jsonify({'success': False, 'error': 'Medicine name required'}), 400
    
    # Check if medicine exists in MongoDB
    medicine_data = medicine_model.get_medicine_by_name(medicine_name)
    
    if not medicine_data:
        return jsonify({'success': False, 'error': 'Medicine not found'}), 404
    
    #  Use the DB saved_meds model instead of session
    from models.user_model import DB
    db = DB()
    saved_meds_model = db.saved_meds
    
    # Check if already saved (prevent duplicates)
    existing_meds = saved_meds_model.get_meds_by_email(user_email)
    already_saved = any(med.get('medication') == medicine_name for med in existing_meds)
    
    if already_saved:
        db.close()
        return jsonify({'success': False, 'message': 'Already saved to profile'}), 400
    
    #  Save to database
    saved_meds_model.save_medication(user_email, medicine_name)
    db.close()
    
    return jsonify({
        'success': True,
        'message': f'{medicine_data["name"]} added to profile!'
    })

# ============================================
# ✅ NEW: FAVORITES ROUTES
# ============================================

@medicine_bp.route('/favorites/add', methods=['POST'])
def add_favorite():
    """Add medicine to favorites"""
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user_email = session.get('email')
    medicine_name = request.form.get('medicine_name')
    
    if not medicine_name:
        return jsonify({'success': False, 'message': 'Medicine name required'}), 400
    
    success = add_to_favorites(user_email, medicine_name)
    
    if success:
        return jsonify({'success': True, 'message': 'Added to favorites!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to add to favorites'}), 500


@medicine_bp.route('/favorites/remove', methods=['POST'])
def remove_favorite():
    """Remove medicine from favorites"""
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user_email = session.get('email')
    medicine_name = request.form.get('medicine_name')
    
    if not medicine_name:
        return jsonify({'success': False, 'message': 'Medicine name required'}), 400
    
    success = remove_from_favorites(user_email, medicine_name)
    
    if success:
        return jsonify({'success': True, 'message': 'Removed from favorites!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to remove from favorites'}), 500


@medicine_bp.route('/api/favorites')
def get_favorites_api():
    """API endpoint to get user's favorites"""
    if 'email' not in session:
        return jsonify({'success': False, 'favorites': []})
    
    user_email = session.get('email')
    favorites = get_user_favorites(user_email)
    
    return jsonify({'success': True, 'favorites': favorites})


# ============================================
# ✅ NEW: REVIEWS ROUTES
# ============================================

@medicine_bp.route('/review/add', methods=['POST'])
def add_medicine_review():
    """Add a review for a medicine"""
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    user_email = session.get('email')
    medicine_name = request.form.get('medicine_name')
    rating = request.form.get('rating', type=int)
    review_text = request.form.get('review_text', '').strip()
    
    # Validate inputs
    if not medicine_name or not rating:
        return jsonify({'success': False, 'message': 'Medicine name and rating required'}), 400
    
    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
    
    if not review_text:
        return jsonify({'success': False, 'message': 'Please write a review'}), 400
    
    # Add review
    review_id = add_review(user_email, medicine_name, rating, review_text)
    
    if review_id:
        return jsonify({'success': True, 'message': 'Review added successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to add review'}), 500


@medicine_bp.route('/review/delete/<review_id>', methods=['POST'])
def delete_medicine_review(review_id):
    """Delete a review"""
    if 'email' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    success = delete_review(review_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Review deleted!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to delete review'}), 500


# ============================================
# ✅ NEW: SEARCH HISTORY API
# ============================================

@medicine_bp.route('/api/search-history')
def get_search_history_api():
    """API endpoint to get search history"""
    if 'email' not in session:
        return jsonify({'success': False, 'history': []})
    
    user_email = session.get('email')
    history = get_user_search_history(user_email, limit=20)
    
    return jsonify({'success': True, 'history': history})


# ============================================
# REDIRECT OLD .html FILES
# ============================================

@medicine_bp.route('/<path:filename>.html')
def block_html_files(filename):
    if filename == 'homepage':
        return redirect('/')
    elif filename == 'login':
        return redirect('/login')
    elif filename == 'signup':
        return redirect('/signup')
    else:
        return redirect('/')

# ============================================
# CLOSE CONNECTION WHEN APP STOPS
# ============================================

@medicine_bp.teardown_app_request
def close_db_connection(exception=None):
    """Close MongoDB connection when request ends"""
    pass  # Connection pooling handles this automatically