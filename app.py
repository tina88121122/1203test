from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os
import qrcode
from io import BytesIO

# 初始化 Flask 應用
app = Flask(__name__)

# 資料庫設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/yourdatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# 上傳圖片設定
app.config['UPLOADED_PHOTOS_DEST'] = 'static/uploads/photos'
app.config['UPLOADED_QRCODES_DEST'] = 'static/uploads/qrcodes'

# 初始化資料庫
db = SQLAlchemy(app)

# 上傳設定
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

# 定義資料庫模型
class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    clothes_photo_path = db.Column(db.String(255), nullable=False)
    wardrobe = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    qrcode_path = db.Column(db.String(255), nullable=True)

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
    photo_path = photos.save(photo)  # 儲存圖片並取得檔案名稱
    photo_url = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], photo_path)  # 圖片 URL

    # 儲存資料
    item = Item(
        clothes_photo_path=photo_url,
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
    qrcode_path = f"{item.id}.png"
    qrcode_full_path = os.path.join(app.config['UPLOADED_QRCODES_DEST'], qrcode_path)
    qr.save(qrcode_full_path)  # 儲存 QR code 圖片

    # 儲存 QR Code 路徑到資料庫
    item.qrcode_path = qrcode_full_path
    db.session.commit()

    return jsonify({"message": "Item added successfully", "photo_url": photo_url, "qrcode_url": qrcode_full_path})


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
    app.run(debug=True)