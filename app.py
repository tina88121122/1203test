from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import qrcode
from io import BytesIO
from sqlalchemy.dialects.postgresql import ENUM

# 初始化 Flask 應用
app = Flask(__name__)

# 資料庫設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://appdata_b97z_user:SOxfD2bGB4370oGAawtiz6l1Bo3rzzfo@5432/appdata_b97z'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化資料庫
db = SQLAlchemy(app)

# 設定上傳檔案的儲存路徑
UPLOAD_FOLDER_IMAGES = 'static/uploads/images' #物件照片上傳路徑
UPLOAD_FOLDER_QRCODES = 'static/uploads/qrcodes' #QRcode上傳路徑
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
app.config['UPLOAD_FOLDER_QRCODES'] = UPLOAD_FOLDER_QRCODES
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

# 定義 ENUM 類型
new_category_type = ENUM('上身', '下身','連身', '其他', name='new_category_type')
new_color_type = ENUM('暖色','冷色','黑白','其他', name='new_color_type')
wardrobe_types = ENUM('A櫃', 'B櫃', 'C櫃', name='wardrobe_types')

# 定義資料庫 Item 模型
class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(new_category_type, nullable=False)
    color = db.Column(new_color_type, nullable=False)
    description = db.Column(db.Text, nullable=True)
    wardrobe = db.Column(wardrobe_types, nullable=False)
    qrcode_path = db.Column(db.String(255))
    clothes_photo_path = db.Column(db.String(255))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 顯示衣櫃資料
@app.route('/wardrobe', methods=['GET'])
def get_wardrobe():
    wardrobe_id = request.args.get('wardrobe_id', 'All')  # 默認顯示所有
    category_filter = request.args.get('category', None)

    query = Item.query
    if wardrobe_id != 'All':
        query = query.filter(Item.wardrobe == wardrobe_id)
    if category_filter:
        query = query.filter(Item.category == category_filter)

    items = query.all()
    result = []
    for item in items:
        result.append({
            'id': item.id,
            'clothes_photo_path': item.clothes_photo_path,
            'wardrobe': item.wardrobe,
            'name': item.name,
            'category': item.category,
            'color': item.color,
            'description': item.description
        })

    return jsonify(result)


# 新增物品資料
@app.route('/add', methods=['POST'])
def add_item():
    photo = request.files['photo']  # 上傳的圖片
    if photo and allowed_file(photo.filename):  # 檢查檔案類型
        filename = secure_filename(photo.filename)  # 確保檔名安全
        photo_path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename)
        photo.save(photo_path)  # 儲存圖片

        # 儲存資料
        item = Item(
            clothes_photo_path=photo_path,
            wardrobe=request.form['wardrobe'],
            name=request.form['name'],
            category=request.form['category'],
            color=request.form['color'],
            description=request.form['description']
        )
        db.session.add(item)
        db.session.commit()

        # 生成 QR Code
        qr = qrcode.make(item.id)  # 生成以物品ID為內容的QR code
        qr_code_path = os.path.join(app.config['UPLOAD_FOLDER_QRCODES'], f"{item.id}.png")
        qr.save(qr_code_path)  # 儲存 QR code 圖片

        # 儲存 QR Code 路徑到資料庫
        item.qrcode_path = qr_code_path
        db.session.commit()

        return jsonify({"message": "Item added successfully", "photo_url": photo_path, "qrcode_url": qr_code_path})
    else:
        return jsonify({"message": "File type not allowed"}), 400

# 顯示詳細資料
@app.route('/data/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    return jsonify({
        'clothes_photo_path': item.clothes_photo_path,
        'wardrobe': item.wardrobe,
        'name': item.name,
        'category': item.category,
        'color': item.color,
        'description': item.description,
        'qrcode_path': item.qrcode_path
    })


# 更新物品資料
@app.route('/update/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    item.wardrobe=request.form.get('wardrobe',item.wardrobe)
    item.name = request.form.get('name', item.name)
    item.category = request.form.get('category', item.category)
    item.color = request.form.get('color', item.color)
    item.description = request.form.get('description', item.description)
    db.session.commit()

    return jsonify({"message": "Item updated successfully"})


# 刪除物品資料
@app.route('/delete/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item deleted successfully"})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)


   





