from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String(50), unique=True, nullable=False)  # roll / id
    full_name = db.Column(db.String(150), nullable=False)

    class_name = db.Column(db.String(80))
    year_text = db.Column(db.String(30))

    dob = db.Column(db.String(20))
    contact_no = db.Column(db.String(20))
    blood_group = db.Column(db.String(5))

    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    address_line3 = db.Column(db.String(200))

    photo_path = db.Column(db.String(255))  # static/uploads/photos/...


class CardBatch(db.Model):
   
    __tablename__ = "card_batches"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime)
    output_format = db.Column(db.String(10))  # "PNG" or "PDF"
    output_file = db.Column(db.String(255))   # bulk PDF ya ZIP ka path


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("card_batches.id"))

    qr_data = db.Column(db.String(400))
    barcode_number = db.Column(db.String(80))

    front_image_path = db.Column(db.String(255))  # optional: PNG path
    back_image_path = db.Column(db.String(255))   # optional: PNG path

    student = db.relationship("Student", backref="cards")
    batch = db.relationship("CardBatch", backref="cards")
