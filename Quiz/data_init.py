# data_init.py
from app import app
from models import db, Job, Question, User
import random
from werkzeug.security import generate_password_hash

def init_data():
    with app.app_context():
        db.create_all()

        # --- 1. Tạo 500 Ngành nghề Giả ---
        if Job.query.count() < 500:
            print("Đang tạo 500 ngành nghề giả...")
            for i in range(1, 501):
                job_name = f"Ngành nghề {i}"
                description = f"Đây là mô tả chi tiết về Ngành nghề {i} trong lĩnh vực X."
                qualities = f"Phẩm chất: Tính kiên nhẫn, Sáng tạo. Năng lực: Lập trình, Phân tích dữ liệu."
                job = Job(name=job_name, description=description, qualities=qualities)
                db.session.add(job)
            db.session.commit()
            print("Đã tạo xong 500 ngành nghề.")

        # --- 2. Tạo 10 Câu hỏi Giả cho mỗi ngành (Tổng 5000 câu) ---
        if Question.query.count() == 0:
            print("Đang tạo câu hỏi giả...")
            jobs = Job.query.all()
            for job in jobs:
                for i in range(1, 11):
                    question_text = f"Câu hỏi {i} về năng lực/phẩm chất của {job.name}?"
                    correct = random.choice(['A', 'B', 'C'])
                    q = Question(
                        job_id=job.id,
                        text=question_text,
                        option_a="Đáp án A (Năng lực X)",
                        option_b="Đáp án B (Năng lực Y)",
                        option_c="Đáp án C (Phẩm chất Z)",
                        correct_answer=correct
                    )
                    db.session.add(q)
            db.session.commit()
            print("Đã tạo xong câu hỏi.")

        # --- 3. Tạo tài khoản Admin ---
        if not User.query.filter_by(username='admin').first():
            print("Đang tạo tài khoản Admin...")
            admin_user = User(
                username='admin',
                is_admin=True,
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Đã tạo tài khoản admin: admin/admin123")

if __name__ == '__main__':
    from app import app
    init_data()