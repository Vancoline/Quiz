# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Job, Question, User, Result
from werkzeug.security import check_password_hash
import random
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mot_key_bi_mat_rat_an_toan' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///career_quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# FIX LỖI ADMIN: Context Processor để cung cấp thông tin User cho mọi template
@app.context_processor
def inject_user():
    current_user = None
    if 'user_id' in session:
        # Tải user hiện tại
        current_user = User.query.get(session['user_id'])
    return dict(current_user=current_user, User=User)

# ----------------- ADMIN DECORATOR -----------------
def admin_required(f):
    def wrapper(*args, **kwargs):
        # Sử dụng current_user từ context processor
        user_id = session.get('user_id')
        user = User.query.get(user_id) if user_id else None
        
        if not user or not user.is_admin:
            flash('Bạn cần đăng nhập với quyền Admin để truy cập trang này.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ----------------- ROUTES CHÍNH (Quiz) -----------------

@app.route('/')
def index():
    # Lấy ngẫu nhiên 10 câu hỏi từ 500 ngành nghề
    question_ids = [q.id for q in Question.query.all()]
    if len(question_ids) < 10:
        return "Chưa có đủ câu hỏi trong CSDL. Vui lòng chạy data_init.py trước."
        
    random.shuffle(question_ids)
    selected_ids = random.sample(question_ids, 10)
    questions = Question.query.filter(Question.id.in_(selected_ids)).all()
    
    return render_template('index.html', questions=questions)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    score = 0
    detailed_results = []
    
    # Lấy ID người dùng (Nếu chưa đăng nhập, dùng ID 1 giả định hoặc ID người dùng chung)
    user_id = session.get('user_id', 1) 
    
    for key, value in request.form.items():
        if key.startswith('q_'):
            try:
                question_id = key.split('_')[1]
                user_answer = value
                
                question = Question.query.get(int(question_id))
                if question:
                    is_correct = (user_answer == question.correct_answer)
                    
                    if is_correct:
                        score += 1
                    
                    # Lưu kết quả chi tiết
                    detailed_results.append({
                        'q_id': question.id,
                        'q_text': question.text,
                        'user_ans': user_answer,
                        'correct_ans': question.correct_answer,
                        'is_correct': is_correct,
                        'job_name': question.job.name
                    })
            except Exception as e:
                # Xử lý lỗi nếu ID câu hỏi không hợp lệ
                print(f"Lỗi khi xử lý câu hỏi: {e}")
                
    # Lưu kết quả vào CSDL
    new_result = Result(
        user_id=user_id, 
        score=score, 
        details=json.dumps(detailed_results)
    )
    db.session.add(new_result)
    db.session.commit()

    flash(f'Bạn đã hoàn thành bài Quiz! Điểm của bạn là {score}/10.', 'success')
    return render_template('results.html', score=score, details=detailed_results)

# ----------------- ROUTES ADMIN/AUTH -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Đăng nhập thành công.', 'success')
                return redirect(url_for('index'))
        
        flash('Sai tên đăng nhập hoặc mật khẩu.', 'danger')
    
    return render_template('login.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Lấy tất cả kết quả và thông tin người dùng
    all_results = Result.query.order_by(Result.timestamp.desc()).all()
    
    admin_data = []
    for result in all_results:
        user = User.query.get(result.user_id)
        
        # Phân tích chi tiết câu trả lời
        try:
            details = json.loads(result.details)
        except (json.JSONDecodeError, TypeError):
            details = [] # Xử lý lỗi nếu dữ liệu JSON bị hỏng
        
        admin_data.append({
            'result_id': result.id,
            'username': user.username if user else 'N/A', # Xử lý nếu user bị xóa
            'score': result.score,
            'timestamp': result.timestamp.strftime('%Y-%m-%d %H:%M'),
            'details': details
        })
        
    return render_template('admin.html', admin_data=admin_data)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Bạn đã đăng xuất.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)